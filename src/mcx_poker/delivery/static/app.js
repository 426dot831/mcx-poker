(function attachMcxPoker(root) {
  "use strict";

  const SEAT_COUNT = 6;
  const ACTION_TYPES = ["Fold", "Check", "Call", "RaiseTo", "AllIn"];

  function createInitialState(config) {
    const safeConfig = config || {};

    return {
      tableSnapshot: null,
      playerObservation: null,
      pendingAction: null,
      lastError: "",
      connectionStatus: "disconnected",
      awaitingConfirmation: false,
      lastPlayerActed: null,
      lastServerEvent: null,
      playerId: safeConfig.playerId || null,
      seatIndex: normalizeSeatIndex(safeConfig.seatIndex),
    };
  }

  function normalizeSeatIndex(value) {
    if (value === null || value === undefined || value === "") {
      return null;
    }

    const numberValue = Number(value);
    return Number.isInteger(numberValue) && numberValue >= 0 ? numberValue : null;
  }

  function normalizeEvent(rawEvent) {
    const event = rawEvent || {};
    const type = event.event_type || event.type || event.event || event.name || "";
    const payload =
      event.payload !== undefined
        ? event.payload
        : event.data !== undefined
          ? event.data
          : event;

    return { type, payload: payload || {} };
  }

  function normalizeLegalActions(rawActions) {
    if (!Array.isArray(rawActions)) {
      return [];
    }

    return rawActions
      .map((action) => {
        if (typeof action === "string") {
          return { action_type: action, enabled: true };
        }

        if (!action || typeof action !== "object") {
          return null;
        }

        return {
          ...action,
          action_type: action.action_type || action.type || action.name,
          enabled: action.enabled !== false && action.available !== false,
        };
      })
      .filter((action) => ACTION_TYPES.includes(action.action_type));
  }

  function getLegalActions(state) {
    const pendingActions = state.pendingAction && state.pendingAction.legal_actions;
    const observationActions = state.playerObservation && state.playerObservation.legal_actions;
    return normalizeLegalActions(pendingActions || observationActions || []);
  }

  function isActionEnabled(state, actionType) {
    return getLegalActions(state).some(
      (action) => action.action_type === actionType && action.enabled !== false,
    );
  }

  function findLegalAction(state, actionType) {
    return getLegalActions(state).find((action) => action.action_type === actionType) || null;
  }

  function buildActionPayload(state, actionType, amountInput) {
    if (!ACTION_TYPES.includes(actionType)) {
      throw new Error(`Unknown action type: ${actionType}`);
    }

    if (!state || !state.pendingAction) {
      throw new Error("No pending action to submit");
    }

    const pending = state.pendingAction;
    const payload = {
      player_id: firstDefined(pending.player_id, state.playerId),
      seat_index: firstDefined(pending.seat_index, state.seatIndex),
      hand_id: pending.hand_id,
      turn_id: pending.turn_id,
      action_type: actionType,
    };

    if (actionType === "RaiseTo") {
      const amount = Number(amountInput);
      if (!Number.isFinite(amount) || amount < 0) {
        throw new Error("RaiseTo requires a non-negative total amount");
      }
      payload.amount = amount;
    }

    return payload;
  }

  function buildClientEvent(state, actionType, amountInput) {
    return {
      event_type: "submit_action",
      payload: buildActionPayload(state, actionType, amountInput),
    };
  }

  function applyServerEvent(state, rawEvent) {
    const event = normalizeEvent(rawEvent);
    state.lastServerEvent = event.type;

    switch (event.type) {
      case "table_snapshot":
        applySnapshot(state, event.payload);
        state.lastError = "";
        state.awaitingConfirmation = false;
        break;

      case "hand_started":
      case "table_paused":
      case "table_resumed":
      case "table_reset":
        applySnapshotFromPayload(state, event.payload);
        state.lastError = "";
        state.awaitingConfirmation = false;
        if (event.type === "table_reset") {
          state.pendingAction = null;
          state.playerObservation = null;
        }
        break;

      case "hole_cards_dealt":
        state.playerObservation = {
          ...(state.playerObservation || {}),
          player_id: firstDefined(event.payload.player_id, state.playerId),
          seat_index: firstDefined(event.payload.seat_index, state.seatIndex),
          hole_cards: firstArray(event.payload.hole_cards, event.payload.cards),
        };
        break;

      case "board_updated":
        mergeBackendTableFields(state, event.payload, ["board", "community_cards", "pot", "pots"]);
        break;

      case "action_requested":
        applyActionRequested(state, event.payload);
        state.lastError = "";
        state.awaitingConfirmation = false;
        break;

      case "player_acted":
        state.lastPlayerActed = event.payload;
        state.awaitingConfirmation = false;
        clearConfirmedPendingAction(state, event.payload);
        applySnapshotFromPayload(state, event.payload);
        break;

      case "action_rejected":
        state.lastError = extractErrorMessage(event.payload);
        state.awaitingConfirmation = false;
        break;

      case "hand_ended":
        applySnapshotFromPayload(state, event.payload);
        state.pendingAction = null;
        state.playerObservation = clearObservationActions(state.playerObservation);
        state.awaitingConfirmation = false;
        break;

      default:
        if (event.payload && event.payload.table_snapshot) {
          applySnapshot(state, event.payload.table_snapshot);
        }
        break;
    }

    return state;
  }

  function applySnapshot(state, snapshot) {
    if (snapshot && typeof snapshot === "object") {
      state.tableSnapshot = snapshot;
    }
  }

  function applySnapshotFromPayload(state, payload) {
    const snapshot = extractSnapshot(payload);
    if (snapshot) {
      applySnapshot(state, snapshot);
    }
  }

  function extractSnapshot(payload) {
    if (!payload || typeof payload !== "object") {
      return null;
    }

    if (payload.table_snapshot) {
      return payload.table_snapshot;
    }
    if (payload.snapshot) {
      return payload.snapshot;
    }
    if (payload.table) {
      return payload.table;
    }
    if (payload.seats || payload.board || payload.community_cards || payload.pot || payload.pots) {
      return payload;
    }

    return null;
  }

  function mergeBackendTableFields(state, payload, fields) {
    if (!payload || typeof payload !== "object") {
      return;
    }

    const current = state.tableSnapshot || {};
    const next = { ...current };

    fields.forEach((field) => {
      if (payload[field] !== undefined) {
        next[field] = payload[field];
      }
    });

    if (payload.table_snapshot || payload.snapshot || payload.table) {
      applySnapshotFromPayload(state, payload);
      return;
    }

    state.tableSnapshot = next;
  }

  function applyActionRequested(state, payload) {
    const observation = payload.observation || payload.player_observation || payload;
    state.playerObservation = {
      ...(state.playerObservation || {}),
      ...observation,
      legal_actions: observation.legal_actions || payload.legal_actions || [],
    };

    state.pendingAction = {
      player_id: firstDefined(payload.player_id, observation.player_id, state.playerId),
      seat_index: firstDefined(payload.seat_index, observation.seat_index, state.seatIndex),
      hand_id: firstDefined(payload.hand_id, observation.hand_id),
      turn_id: firstDefined(payload.turn_id, observation.turn_id),
      legal_actions: observation.legal_actions || payload.legal_actions || [],
    };

    if (state.pendingAction.player_id !== null && state.pendingAction.player_id !== undefined) {
      state.playerId = state.pendingAction.player_id;
    }
    if (state.pendingAction.seat_index !== null && state.pendingAction.seat_index !== undefined) {
      state.seatIndex = normalizeSeatIndex(state.pendingAction.seat_index);
      state.pendingAction.seat_index = state.seatIndex;
    }
  }

  function clearConfirmedPendingAction(state, payload) {
    if (!state.pendingAction) {
      return;
    }

    const actedTurn = payload && payload.turn_id;
    const actedPlayer = payload && payload.player_id;
    const matchesTurn = actedTurn && actedTurn === state.pendingAction.turn_id;
    const matchesPlayer = actedPlayer && actedPlayer === state.pendingAction.player_id;

    if (matchesTurn || (matchesPlayer && state.awaitingConfirmation)) {
      state.pendingAction = null;
      state.playerObservation = clearObservationActions(state.playerObservation);
    }
  }

  function clearObservationActions(observation) {
    if (!observation) {
      return null;
    }

    const next = { ...observation };
    delete next.legal_actions;
    return next;
  }

  function extractErrorMessage(payload) {
    if (!payload) {
      return "Action rejected";
    }

    if (typeof payload === "string") {
      return payload;
    }

    return (
      payload.message ||
      payload.error_message ||
      (payload.error && (payload.error.message || payload.error.code)) ||
      payload.code ||
      "Action rejected"
    );
  }

  function firstDefined() {
    for (let index = 0; index < arguments.length; index += 1) {
      if (arguments[index] !== undefined && arguments[index] !== null) {
        return arguments[index];
      }
    }
    return null;
  }

  function firstArray() {
    for (let index = 0; index < arguments.length; index += 1) {
      if (Array.isArray(arguments[index])) {
        return arguments[index];
      }
    }
    return [];
  }

  function setupBrowserApp() {
    const doc = root.document;
    const body = doc.body;
    const searchParams = new URLSearchParams(root.location.search);
    const config = {
      apiBase: body.dataset.apiBase || "/api",
      wsPath: body.dataset.wsPath || "/ws/table",
      playerId: searchParams.get("player_id") || body.dataset.playerId || null,
      seatIndex: searchParams.get("seat_index") || body.dataset.playerSeatIndex || null,
    };
    const state = createInitialState(config);
    let socket = null;

    const elements = {
      connectionStatus: doc.querySelector("[data-connection-status]"),
      handId: doc.querySelector("[data-hand-id]"),
      currentActor: doc.querySelector("[data-current-actor]"),
      lastError: doc.querySelector("[data-last-error]"),
      boardCards: doc.querySelector("[data-board-cards]"),
      potTotal: doc.querySelector("[data-pot-total]"),
      potBreakdown: doc.querySelector("[data-pot-breakdown]"),
      showdown: doc.querySelector("[data-showdown-summary]"),
      heroCards: doc.querySelector("[data-hero-cards]"),
      actionBar: doc.querySelector("[data-action-bar]"),
      raiseInput: doc.querySelector("[data-raise-to-amount]"),
      tableControls: doc.querySelector("[data-table-controls]"),
      seats: Array.from(doc.querySelectorAll("[data-seat-index]")),
    };

    function renderNow() {
      render(state, elements);
    }

    elements.actionBar.addEventListener("submit", (event) => {
      event.preventDefault();
      const button = event.submitter && event.submitter.closest("[data-action]");
      if (!button || button.disabled) {
        return;
      }

      try {
        const actionType = button.dataset.action;
        const amount = elements.raiseInput.value;
        const message = buildClientEvent(state, actionType, amount);
        if (!socket || socket.readyState !== WebSocket.OPEN) {
          throw new Error("WebSocket is not connected");
        }
        socket.send(JSON.stringify(message));
        state.awaitingConfirmation = true;
        state.lastError = "";
        renderNow();
      } catch (error) {
        state.lastError = error.message;
        renderNow();
      }
    });

    elements.tableControls.addEventListener("click", (event) => {
      const button = event.target.closest("[data-command]");
      if (!button) {
        return;
      }
      sendTableCommand(config.apiBase, state, button.dataset.command).then(renderNow);
    });

    renderNow();
    fetchInitialSnapshot(config.apiBase, state).then(renderNow);
    socket = connectSocket(config, state, renderNow);

    root.McxPokerState = state;
  }

  async function fetchInitialSnapshot(apiBase, state) {
    try {
      const response = await fetch(`${apiBase}/table`, { headers: { Accept: "application/json" } });
      if (!response.ok) {
        throw new Error(`Snapshot request failed: ${response.status}`);
      }

      const body = await response.json();
      const snapshot = body && body.ok === false ? null : body.data || body;
      if (body && body.ok === false) {
        throw new Error(extractErrorMessage(body));
      }
      applyServerEvent(state, { type: "table_snapshot", payload: snapshot });
    } catch (error) {
      state.lastError = error.message;
    }
  }

  async function sendTableCommand(apiBase, state, command) {
    try {
      const tableId = state.tableSnapshot && (state.tableSnapshot.table_id || state.tableSnapshot.id);
      const response = await fetch(`${apiBase}/table/control`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        body: JSON.stringify({ table_id: tableId, command }),
      });

      if (!response.ok) {
        throw new Error(`Table command failed: ${response.status}`);
      }

      const body = await response.json();
      if (body && body.ok === false) {
        throw new Error(extractErrorMessage(body));
      }

      applyServerEvent(state, { type: "table_snapshot", payload: body.data || body });
    } catch (error) {
      state.lastError = error.message;
    }
  }

  function connectSocket(config, state, renderNow) {
    if (!root.WebSocket) {
      state.connectionStatus = "unavailable";
      renderNow();
      return null;
    }

    const socket = new WebSocket(buildWsUrl(config));
    state.connectionStatus = "connecting";
    renderNow();

    socket.addEventListener("open", () => {
      state.connectionStatus = "connected";
      socket.send(JSON.stringify({ event_type: "request_snapshot", payload: {} }));
      renderNow();
    });

    socket.addEventListener("message", (message) => {
      try {
        applyServerEvent(state, JSON.parse(message.data));
      } catch (error) {
        state.lastError = error.message;
      }
      renderNow();
    });

    socket.addEventListener("close", () => {
      state.connectionStatus = "disconnected";
      renderNow();
    });

    socket.addEventListener("error", () => {
      state.connectionStatus = "error";
      renderNow();
    });

    return socket;
  }

  function buildWsUrl(config) {
    const wsPath = config.wsPath || "/ws/table";
    const protocol = root.location.protocol === "https:" ? "wss:" : "ws:";
    const url = wsPath.startsWith("ws://") || wsPath.startsWith("wss://")
      ? new URL(wsPath)
      : new URL(wsPath, `${protocol}//${root.location.host}`);

    if (config.playerId) {
      url.searchParams.set("player_id", config.playerId);
    }
    if (config.seatIndex !== null && config.seatIndex !== undefined && config.seatIndex !== "") {
      url.searchParams.set("seat_index", config.seatIndex);
    }

    return url.toString();
  }

  function render(state, elements) {
    const snapshot = state.tableSnapshot || {};
    const seats = normalizeSeats(snapshot);

    elements.connectionStatus.textContent = state.connectionStatus;
    elements.handId.textContent = snapshot.hand_id || snapshot.current_hand_id || "-";
    elements.currentActor.textContent = formatActor(snapshot.current_actor || snapshot.action_player);
    elements.lastError.textContent = state.lastError || "";

    renderBoard(
      elements.boardCards,
      firstArray(snapshot.community_cards, snapshot.board, snapshot.board_cards),
    );
    renderPot(elements, snapshot);
    renderSeats(elements.seats, seats, state);
    renderHeroHand(elements.heroCards, state);
    renderActionBar(elements, state);
    renderShowdown(elements.showdown, snapshot);
  }

  function normalizeSeats(snapshot) {
    const rawSeats = firstArray(snapshot.seats, snapshot.players);
    const byIndex = new Map();

    rawSeats.forEach((seat, fallbackIndex) => {
      const index = normalizeSeatIndex(firstDefined(seat.seat_index, seat.index, fallbackIndex));
      if (index !== null && index < SEAT_COUNT) {
        byIndex.set(index, seat);
      }
    });

    return Array.from({ length: SEAT_COUNT }, (_, index) => ({
      seat_index: index,
      ...(byIndex.get(index) || {}),
    }));
  }

  function renderBoard(container, cards) {
    replaceChildren(
      container,
      Array.from({ length: 5 }, (_, index) => createCard(cards[index], cards[index] ? "face" : "slot")),
    );
  }

  function renderPot(elements, snapshot) {
    const potSummary = snapshot.pot_summary || {};
    const pot = firstDefined(
      snapshot.pot_total,
      snapshot.total_pot,
      snapshot.pot,
      potSummary.total_amount,
      potSummary.total,
    );
    elements.potTotal.textContent = formatValue(pot);

    const pots = firstArray(snapshot.pots, snapshot.side_pots);
    elements.potBreakdown.textContent = pots.length
      ? pots.map((item) => formatValue(firstDefined(item.amount, item.total, item))).join(" / ")
      : "";
  }

  function renderSeats(seatElements, seats, state) {
    seatElements.forEach((element) => {
      const seatIndex = normalizeSeatIndex(element.dataset.seatIndex);
      const seat = seats[seatIndex] || { seat_index: seatIndex };
      const isHero = state.seatIndex !== null && seatIndex === state.seatIndex;

      element.classList.toggle("hero-seat", isHero);
      element.querySelector("[data-seat-name]").textContent = seatName(seat);
      element.querySelector("[data-seat-stack]").textContent = formatValue(
        firstDefined(seat.stack, seat.chips, seat.stack_amount, seat.player && seat.player.stack),
      );
      element.querySelector("[data-seat-state]").textContent = seatState(seat);

      const cardContainer = element.querySelector("[data-seat-cards]");
      const visibleCards = visibleCardsForSeat(seat, state, isHero);
      const hiddenCount = visibleCards.length ? 0 : hiddenCardCount(seat);
      replaceChildren(
        cardContainer,
        visibleCards.length
          ? visibleCards.map((card) => createCard(card, "face"))
          : Array.from({ length: hiddenCount }, () => createCard(null, "back")),
      );
    });
  }

  function renderHeroHand(container, state) {
    const cards = heroHoleCards(state);
    replaceChildren(
      container,
      cards.length
        ? cards.map((card) => createCard(card, "face"))
        : [createCard(null, "slot"), createCard(null, "slot")],
    );
  }

  function renderActionBar(elements, state) {
    const isWaiting = state.awaitingConfirmation;
    ACTION_TYPES.forEach((actionType) => {
      const button = elements.actionBar.querySelector(`[data-action="${actionType}"]`);
      if (button) {
        button.disabled = isWaiting || !isActionEnabled(state, actionType);
      }
    });

    const raiseAction = findLegalAction(state, "RaiseTo");
    elements.raiseInput.disabled = isWaiting || !raiseAction || raiseAction.enabled === false;
    elements.raiseInput.min = firstDefined(
      raiseAction && raiseAction.min,
      raiseAction && raiseAction.min_amount,
      raiseAction && raiseAction.min_total,
      0,
    );
    elements.raiseInput.max = firstDefined(
      raiseAction && raiseAction.max,
      raiseAction && raiseAction.max_amount,
      raiseAction && raiseAction.max_total,
      "",
    );
  }

  function renderShowdown(container, snapshot) {
    const showdown = firstArray(snapshot.showdown, snapshot.revealed_hands, snapshot.results);
    if (!showdown.length) {
      container.hidden = true;
      container.textContent = "";
      return;
    }

    container.hidden = false;
    container.textContent = showdown
      .map((entry) => {
        const label = entry.player_name || entry.player_id || `Seat ${entry.seat_index}`;
        const cards = firstArray(entry.cards, entry.revealed_cards, entry.showdown_cards)
          .map(formatCard)
          .join(" ");
        return cards ? `${label}: ${cards}` : label;
      })
      .join(" | ");
  }

  function visibleCardsForSeat(seat, state, isHero) {
    if (isHero) {
      const heroCards = heroHoleCards(state);
      if (heroCards.length) {
        return heroCards;
      }
    }

    const publicCards = firstArray(
      seat.revealed_cards,
      seat.public_cards,
      seat.showdown_cards,
      seat.exposed_cards,
    );
    if (publicCards.length) {
      return publicCards;
    }

    if (seat.cards_revealed || seat.hole_cards_public || seat.show_cards) {
      return firstArray(seat.hole_cards, seat.cards);
    }

    return [];
  }

  function heroHoleCards(state) {
    const observation = state.playerObservation || {};
    return firstArray(
      observation.own_hole_cards,
      observation.hole_cards,
      observation.cards,
      observation.private_cards,
    );
  }

  function hiddenCardCount(seat) {
    const explicitCount = firstDefined(seat.hidden_card_count, seat.hole_card_count, seat.card_count);
    if (Number.isInteger(Number(explicitCount)) && Number(explicitCount) > 0) {
      return Number(explicitCount);
    }

    if (seat.has_hole_cards || seat.in_hand || seat.is_in_hand) {
      return 1;
    }

    return 0;
  }

  function createCard(card, mode) {
    const element = root.document.createElement("span");
    element.className = `card ${mode === "back" ? "back" : mode === "slot" ? "slot" : "face"}`;
    element.textContent = mode === "back" ? "BACK" : mode === "slot" ? "--" : formatCard(card);
    if (mode === "back") {
      element.setAttribute("aria-label", "Hidden card");
    }
    return element;
  }

  function replaceChildren(container, children) {
    container.replaceChildren(...children);
  }

  function seatName(seat) {
    return (
      seat.player_name ||
      seat.name ||
      (seat.player && (seat.player.name || seat.player.player_name)) ||
      (seat.player_id ? String(seat.player_id) : "Empty")
    );
  }

  function seatState(seat) {
    return seat.status || seat.state || (seat.player_id || seat.player_name || seat.player ? "seated" : "Open");
  }

  function formatActor(actor) {
    if (actor === null || actor === undefined || actor === "") {
      return "-";
    }
    if (typeof actor === "string" || typeof actor === "number") {
      return String(actor);
    }
    return actor.player_name || actor.player_id || `Seat ${actor.seat_index}`;
  }

  function formatValue(value) {
    if (value === null || value === undefined || value === "") {
      return "-";
    }
    return String(value);
  }

  function formatCard(card) {
    if (card === null || card === undefined || card === "") {
      return "--";
    }
    if (typeof card === "string") {
      return card;
    }
    return card.code || card.label || card.text || `${card.rank || ""}${card.suit || ""}` || "--";
  }

  const api = {
    ACTION_TYPES,
    SEAT_COUNT,
    applyServerEvent,
    buildActionPayload,
    buildClientEvent,
    createInitialState,
    getLegalActions,
    isActionEnabled,
    normalizeLegalActions,
  };

  root.McxPoker = api;

  if (typeof module !== "undefined" && module.exports) {
    module.exports = api;
  }

  if (root.document) {
    root.document.addEventListener("DOMContentLoaded", setupBrowserApp);
  }
})(typeof window !== "undefined" ? window : globalThis);
