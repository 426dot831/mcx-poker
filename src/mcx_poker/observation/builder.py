"""Player-facing observation DTOs and builders.

The builder accepts duck-typed table snapshots, state summaries, and public hand
events.  It intentionally does not import PokerKit or adapter internals.
"""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from enum import Enum
from math import isfinite
from typing import Any, TypeAlias

from mcx_poker.engine.actions import ActionType, LegalAction

Identifier: TypeAlias = str | int
JSONValue: TypeAlias = str | int | float | bool | None | list["JSONValue"] | dict[str, "JSONValue"]

SEAT_COUNT = 6
_MISSING = object()
_ALWAYS_HIDDEN_KEYS = frozenset(
    {
        "adapter_hand_ref",
        "controller_private_state",
        "deck",
        "deck_order",
        "future_cards",
        "pokerkit_state",
        "private_controller_state",
        "raw_pokerkit_state",
        "raw_state",
        "remaining_deck",
        "stub",
        "undealt_cards",
    }
)
_PRIVATE_CARD_KEYS = frozenset(
    {
        "all_hole_cards",
        "hidden_hole_cards",
        "hole_cards_by_player",
        "opponent_hole_cards",
        "private_cards",
        "private_hole_cards",
        "unshown_hole_cards",
    }
)
_SHOWDOWN_EVENT_TYPES = frozenset({"showdown", "cards_shown", "hole_cards_shown"})


@dataclass(frozen=True, slots=True)
class VisibleSeat:
    """Seat state visible to one observer."""

    seat_index: int
    player_id: Identifier | None = None
    player_name: str | None = None
    stack: int = 0
    current_bet: int = 0
    status: str = "empty"
    hole_card_count: int = 0
    shown_cards: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "seat_index", _require_seat_index(self.seat_index))
        object.__setattr__(self, "player_id", _optional_identifier(self.player_id))
        object.__setattr__(self, "player_name", _optional_string(self.player_name))
        object.__setattr__(self, "stack", _chip_amount(self.stack, "stack"))
        object.__setattr__(self, "current_bet", _chip_amount(self.current_bet, "current_bet"))
        object.__setattr__(self, "status", _status_string(self.status, self.player_id))
        object.__setattr__(
            self,
            "hole_card_count",
            _chip_amount(self.hole_card_count, "hole_card_count"),
        )
        object.__setattr__(self, "shown_cards", _string_tuple(self.shown_cards, "shown_cards"))

    def to_dict(self) -> dict[str, JSONValue]:
        return {
            "seat_index": self.seat_index,
            "player_id": self.player_id,
            "player_name": self.player_name,
            "stack": self.stack,
            "current_bet": self.current_bet,
            "status": self.status,
            "hole_card_count": self.hole_card_count,
            "shown_cards": list(self.shown_cards),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> VisibleSeat:
        return cls(
            seat_index=_read(data, ("seat_index", "index")),
            player_id=_read(data, ("player_id",), None),
            player_name=_read(data, ("player_name", "name"), None),
            stack=_read(data, ("stack",), 0),
            current_bet=_read(data, ("current_bet",), 0),
            status=_read(data, ("status",), "empty"),
            hole_card_count=_read(data, ("hole_card_count",), 0),
            shown_cards=tuple(_read(data, ("shown_cards",), ())),
        )


@dataclass(frozen=True, slots=True)
class PotSummary:
    """Visible pot summary with JSON-safe side-pot details."""

    total_amount: int = 0
    pots: tuple[Mapping[str, JSONValue], ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "total_amount", _chip_amount(self.total_amount, "total_amount"))
        object.__setattr__(
            self,
            "pots",
            tuple(_sanitize_public_mapping(pot, allow_private_cards=False) for pot in self.pots),
        )

    def to_dict(self) -> dict[str, JSONValue]:
        return {
            "total_amount": self.total_amount,
            "pots": [dict(pot) for pot in self.pots],
        }

    @classmethod
    def from_any(cls, value: Any) -> PotSummary:
        if value is None:
            return cls()
        if isinstance(value, PotSummary):
            return value

        total = _read(value, ("total_amount", "total", "pot_total", "amount"), 0)
        raw_pots = _read(value, ("pots", "side_pots"), ())
        pots: list[Mapping[str, JSONValue]] = []
        for index, raw_pot in enumerate(_as_iterable(raw_pots)):
            pot_payload = _object_to_public_mapping(raw_pot, allow_private_cards=False)
            if "index" not in pot_payload:
                pot_payload = {"index": index, **pot_payload}
            pots.append(pot_payload)
        return cls(total_amount=total, pots=tuple(pots))


@dataclass(frozen=True, slots=True)
class BetSummary:
    """Visible current-betting summary for the hand state."""

    current_bet: int = 0
    to_call: int | None = None
    min_raise_to: int | None = None
    max_raise_to: int | None = None
    bets_by_seat: Mapping[int, int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "current_bet", _chip_amount(self.current_bet, "current_bet"))
        object.__setattr__(self, "to_call", _optional_chip_amount(self.to_call, "to_call"))
        object.__setattr__(
            self,
            "min_raise_to",
            _optional_chip_amount(self.min_raise_to, "min_raise_to"),
        )
        object.__setattr__(
            self,
            "max_raise_to",
            _optional_chip_amount(self.max_raise_to, "max_raise_to"),
        )
        object.__setattr__(
            self,
            "bets_by_seat",
            {seat: _chip_amount(amount, "bet") for seat, amount in self.bets_by_seat.items()},
        )

    def to_dict(self) -> dict[str, JSONValue]:
        return {
            "current_bet": self.current_bet,
            "to_call": self.to_call,
            "min_raise_to": self.min_raise_to,
            "max_raise_to": self.max_raise_to,
            "bets_by_seat": {str(seat): amount for seat, amount in self.bets_by_seat.items()},
        }

    @classmethod
    def from_any(cls, value: Any) -> BetSummary:
        if value is None:
            return cls()
        if isinstance(value, BetSummary):
            return value
        return cls(
            current_bet=_read(value, ("current_bet", "current_bet_to_match"), 0),
            to_call=_read(value, ("to_call", "call_amount"), None),
            min_raise_to=_read(value, ("min_raise_to", "amount_min"), None),
            max_raise_to=_read(value, ("max_raise_to", "amount_max"), None),
            bets_by_seat=_indexed_amounts(_read(value, ("bets_by_seat", "bets"), {})),
        )


@dataclass(frozen=True, slots=True)
class PlayerObservation:
    """Per-player observation with hidden information redacted."""

    observer_player_id: Identifier
    observer_seat_index: int
    table_id: Identifier
    hand_id: Identifier
    turn_id: Identifier
    is_actor: bool
    button_seat_index: int
    own_hole_cards: tuple[str, ...] = ()
    board_cards: tuple[str, ...] = ()
    visible_seats: tuple[VisibleSeat, ...] = ()
    pot_summary: PotSummary = field(default_factory=PotSummary)
    bet_summary: BetSummary = field(default_factory=BetSummary)
    visible_action_history: tuple[Mapping[str, JSONValue], ...] = ()
    legal_actions: tuple[LegalAction, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "observer_player_id", _require_identifier(self.observer_player_id))
        object.__setattr__(
            self, "observer_seat_index", _require_seat_index(self.observer_seat_index)
        )
        object.__setattr__(self, "table_id", _require_identifier(self.table_id))
        object.__setattr__(self, "hand_id", _require_identifier(self.hand_id))
        object.__setattr__(self, "turn_id", _require_identifier(self.turn_id))
        if not isinstance(self.is_actor, bool):
            raise ValueError("is_actor must be a bool")
        object.__setattr__(self, "button_seat_index", _require_seat_index(self.button_seat_index))
        object.__setattr__(
            self,
            "own_hole_cards",
            _string_tuple(self.own_hole_cards, "own_hole_cards"),
        )
        object.__setattr__(self, "board_cards", _string_tuple(self.board_cards, "board_cards"))
        object.__setattr__(
            self,
            "visible_seats",
            tuple(_normalize_visible_seat(seat) for seat in self.visible_seats),
        )
        object.__setattr__(self, "pot_summary", PotSummary.from_any(self.pot_summary))
        object.__setattr__(self, "bet_summary", BetSummary.from_any(self.bet_summary))
        object.__setattr__(
            self,
            "visible_action_history",
            tuple(_normalize_visible_event(event) for event in self.visible_action_history),
        )
        object.__setattr__(
            self,
            "legal_actions",
            tuple(_normalize_legal_action(action) for action in self.legal_actions),
        )

    def to_dict(self) -> dict[str, JSONValue]:
        return {
            "observer_player_id": self.observer_player_id,
            "observer_seat_index": self.observer_seat_index,
            "table_id": self.table_id,
            "hand_id": self.hand_id,
            "turn_id": self.turn_id,
            "is_actor": self.is_actor,
            "button_seat_index": self.button_seat_index,
            "own_hole_cards": list(self.own_hole_cards),
            "board_cards": list(self.board_cards),
            "visible_seats": [seat.to_dict() for seat in self.visible_seats],
            "pot_summary": self.pot_summary.to_dict(),
            "bet_summary": self.bet_summary.to_dict(),
            "visible_action_history": [dict(event) for event in self.visible_action_history],
            "legal_actions": [
                _sanitize_public_mapping(action.to_dict(), allow_private_cards=False)
                for action in self.legal_actions
            ],
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> PlayerObservation:
        return cls(
            observer_player_id=_read(data, ("observer_player_id",)),
            observer_seat_index=_read(data, ("observer_seat_index",)),
            table_id=_read(data, ("table_id",)),
            hand_id=_read(data, ("hand_id",)),
            turn_id=_read(data, ("turn_id",)),
            is_actor=bool(_read(data, ("is_actor",), False)),
            button_seat_index=_read(data, ("button_seat_index",)),
            own_hole_cards=tuple(_read(data, ("own_hole_cards",), ())),
            board_cards=tuple(_read(data, ("board_cards",), ())),
            visible_seats=tuple(_read(data, ("visible_seats",), ())),
            pot_summary=PotSummary.from_any(_read(data, ("pot_summary",), None)),
            bet_summary=BetSummary.from_any(_read(data, ("bet_summary",), None)),
            visible_action_history=tuple(_read(data, ("visible_action_history",), ())),
            legal_actions=tuple(_read(data, ("legal_actions",), ())),
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), separators=(",", ":"), sort_keys=True)

    @classmethod
    def from_json(cls, payload: str) -> PlayerObservation:
        loaded = json.loads(payload)
        if not isinstance(loaded, Mapping):
            raise ValueError("PlayerObservation JSON payload must be an object")
        return cls.from_dict(loaded)

    def to_websocket_payload(self) -> dict[str, JSONValue]:
        """Return a private ``action_requested`` payload shape."""

        observation = self.to_dict()
        return {
            "table_id": self.table_id,
            "hand_id": self.hand_id,
            "turn_id": self.turn_id,
            "player_id": self.observer_player_id,
            "seat_index": self.observer_seat_index,
            "legal_actions": observation["legal_actions"],
            "observation": observation,
        }


def build_player_observation(
    table_snapshot: Any,
    state_summary: Any,
    public_events: Iterable[Any] | None = None,
    *,
    observer_player_id: Identifier | None = None,
    observer_seat_index: int | None = None,
    turn_id: Identifier | None = None,
) -> PlayerObservation:
    """Build one player's redacted observation from platform summaries."""

    events = tuple(public_events or ())
    seats_by_index = _seats_by_index(table_snapshot)
    player_to_seat = _player_to_seat(seats_by_index)

    observer_seat = _resolve_observer_seat(
        observer_player_id=observer_player_id,
        observer_seat_index=observer_seat_index,
        player_to_seat=player_to_seat,
    )
    observer_player = _resolve_observer_player(
        observer_player_id=observer_player_id,
        observer_seat_index=observer_seat,
        seats_by_index=seats_by_index,
    )

    actor = _actor_ref(state_summary)
    actor_seat = _actor_seat_index(actor, player_to_seat)
    actor_player = _actor_player_id(actor)
    is_actor = actor_seat == observer_seat or (
        actor_player is not None and actor_player == observer_player
    )

    hole_cards_by_seat = _indexed_card_mapping(_read(state_summary, ("hole_cards_by_seat",), {}))
    shown_cards = _shown_cards_by_seat(state_summary, events, player_to_seat)
    folded_seats = _folded_seats(events)
    bets_by_seat = _indexed_amounts(_read(state_summary, ("bets", "bets_by_seat"), {}))
    stacks_by_seat = _indexed_amounts(_read(state_summary, ("stacks", "stacks_by_seat"), {}))

    own_hole_cards = hole_cards_by_seat.get(observer_seat, ())
    board_cards = _board_cards(state_summary, table_snapshot, events)
    bet_summary = _build_bet_summary(state_summary, bets_by_seat)

    hand_id = _first_identifier(
        _read(state_summary, ("hand_id",), None),
        _read(table_snapshot, ("hand_id", "current_hand_id"), None),
        "unknown-hand",
    )
    resolved_turn_id = _first_identifier(
        turn_id,
        _read(state_summary, ("turn_id", "current_turn_id", "action_turn_id"), None),
        _read(table_snapshot, ("turn_id", "current_turn_id", "action_turn_id"), None),
        hand_id,
    )

    visible_seats = tuple(
        _build_visible_seat(
            seat_index=seat_index,
            raw_seat=seats_by_index.get(seat_index),
            observer_seat_index=observer_seat,
            hole_cards_by_seat=hole_cards_by_seat,
            shown_cards_by_seat=shown_cards,
            folded_seats=folded_seats,
            bets_by_seat=bets_by_seat,
            stacks_by_seat=stacks_by_seat,
        )
        for seat_index in range(SEAT_COUNT)
    )

    return PlayerObservation(
        observer_player_id=observer_player,
        observer_seat_index=observer_seat,
        table_id=_first_identifier(_read(table_snapshot, ("table_id",), None), "local-table"),
        hand_id=hand_id,
        turn_id=resolved_turn_id,
        is_actor=is_actor,
        button_seat_index=_button_seat_index(table_snapshot, state_summary),
        own_hole_cards=own_hole_cards,
        board_cards=board_cards,
        visible_seats=visible_seats,
        pot_summary=PotSummary.from_any(
            _read(state_summary, ("pot_summary",), _read(table_snapshot, ("pot_summary",), None))
        ),
        bet_summary=bet_summary,
        visible_action_history=tuple(
            _event_to_visible_dict(event) for event in events if _is_public_event(event)
        ),
        legal_actions=_legal_actions(state_summary) if is_actor else (),
    )


build_observation = build_player_observation


def _build_visible_seat(
    *,
    seat_index: int,
    raw_seat: Any,
    observer_seat_index: int,
    hole_cards_by_seat: Mapping[int, tuple[str, ...]],
    shown_cards_by_seat: Mapping[int, tuple[str, ...]],
    folded_seats: set[int],
    bets_by_seat: Mapping[int, int],
    stacks_by_seat: Mapping[int, int],
) -> VisibleSeat:
    player_id = _read(raw_seat, ("player_id",), None)
    shown_cards = shown_cards_by_seat.get(seat_index, ())
    hidden_cards = hole_cards_by_seat.get(seat_index, ())
    raw_hole_count = _read(raw_seat, ("hole_card_count", "card_count"), None)
    if raw_hole_count is None and _read(
        raw_seat, ("has_hole_cards", "in_hand", "is_in_hand"), False
    ):
        raw_hole_count = 2

    if seat_index == observer_seat_index:
        hole_card_count = len(hidden_cards) if hidden_cards else _optional_int(raw_hole_count, 0)
    elif hidden_cards:
        hole_card_count = len(hidden_cards)
    elif shown_cards:
        hole_card_count = len(shown_cards)
    else:
        hole_card_count = _optional_int(raw_hole_count, 0)

    stack = _indexed_or_raw(
        stacks_by_seat, seat_index, raw_seat, ("stack", "chips", "current_stack")
    )
    current_bet = _indexed_or_raw(bets_by_seat, seat_index, raw_seat, ("current_bet", "bet"))
    status = _visible_status(
        raw_status=_read(raw_seat, ("status",), None),
        player_id=player_id,
        seat_index=seat_index,
        folded_seats=folded_seats,
        stack=stack,
        hole_card_count=hole_card_count,
    )
    return VisibleSeat(
        seat_index=seat_index,
        player_id=player_id,
        player_name=_read(raw_seat, ("player_name", "name", "display_name"), None),
        stack=stack,
        current_bet=current_bet,
        status=status,
        hole_card_count=hole_card_count,
        shown_cards=shown_cards,
    )


def _build_bet_summary(state_summary: Any, bets_by_seat: Mapping[int, int]) -> BetSummary:
    explicit = _read(state_summary, ("bet_summary", "betting_summary"), None)
    if explicit is not None:
        return BetSummary.from_any(explicit)

    boundaries = _read(state_summary, ("legal_action_boundaries",), None)
    return BetSummary(
        current_bet=max(bets_by_seat.values(), default=0),
        to_call=_read(boundaries, ("call_amount", "to_call"), None),
        min_raise_to=_read(boundaries, ("min_raise_to",), None),
        max_raise_to=_read(boundaries, ("max_raise_to",), None),
        bets_by_seat=bets_by_seat,
    )


def _legal_actions(state_summary: Any) -> tuple[LegalAction, ...]:
    explicit = _read(state_summary, ("legal_actions", "legal_action_set"), None)
    if explicit is not None:
        return tuple(_normalize_legal_action(action) for action in _legal_action_items(explicit))

    boundaries = _read(state_summary, ("legal_action_boundaries",), None)
    if boundaries is None:
        return ()

    actions: list[LegalAction] = []
    for field_name, action_type in (
        ("fold", ActionType.FOLD),
        ("check", ActionType.CHECK),
        ("call", ActionType.CALL),
        ("raise_to", ActionType.RAISE_TO),
        ("all_in", ActionType.ALL_IN),
    ):
        boundary = _read(boundaries, (field_name, action_type.value), None)
        if boundary is None:
            continue
        actions.append(_normalize_legal_action(boundary, default_action_type=action_type))
    return tuple(actions)


def _legal_action_items(value: Any) -> tuple[Any, ...]:
    actions = _read(value, ("actions",), _MISSING)
    if actions is not _MISSING:
        return tuple(_as_iterable(actions))
    return tuple(_as_iterable(value))


def _normalize_legal_action(
    value: Any,
    *,
    default_action_type: ActionType | None = None,
) -> LegalAction:
    if isinstance(value, LegalAction):
        return value
    if isinstance(value, str | Enum):
        return LegalAction(_enum_value(value))

    payload = _object_to_public_mapping(value, allow_private_cards=False)
    action_type = _enum_value(
        _first_defined(
            payload.get("action_type"),
            payload.get("type"),
            payload.get("action"),
            default_action_type,
        )
    )
    if action_type is None:
        raise ValueError("legal action is missing action_type")

    return LegalAction.from_dict(
        {
            "action_type": action_type,
            "enabled": payload.get("enabled", True),
            "amount_min": _first_defined(
                payload.get("amount_min"),
                payload.get("min_amount"),
                payload.get("min_total"),
            ),
            "amount_max": _first_defined(
                payload.get("amount_max"),
                payload.get("max_amount"),
                payload.get("max_total"),
            ),
            "amount_fixed": _first_defined(
                payload.get("amount_fixed"),
                payload.get("fixed_amount"),
                payload.get("amount"),
            ),
            "reason_if_disabled": payload.get("reason_if_disabled"),
        }
    )


def _normalize_visible_seat(value: Any) -> VisibleSeat:
    if isinstance(value, VisibleSeat):
        return value
    return VisibleSeat.from_dict(_object_to_public_mapping(value, allow_private_cards=False))


def _normalize_visible_event(value: Any) -> Mapping[str, JSONValue]:
    event = _object_to_public_mapping(value, allow_private_cards=True)
    visibility = _string_or_none(event.get("visibility"))
    if visibility is not None and visibility != "public":
        raise ValueError("visible_action_history accepts only public events")
    if event.get("public") is False:
        raise ValueError("visible_action_history accepts only public events")
    event.pop("private_payload", None)
    return event


def _event_to_visible_dict(event: Any) -> Mapping[str, JSONValue]:
    event_type = _event_type(event)
    payload = _sanitize_public_mapping(
        _event_payload(event),
        allow_private_cards=event_type in _SHOWDOWN_EVENT_TYPES,
    )
    visible: dict[str, JSONValue] = {
        "hand_id": _to_json_value(_read(event, ("hand_id",), None)),
        "sequence_number": _to_json_value(_read(event, ("sequence_number",), 0)),
        "event_type": event_type,
        "actor_player_id": _to_json_value(_read(event, ("actor_player_id",), None)),
        "actor_seat_index": _to_json_value(_read(event, ("actor_seat_index",), None)),
        "payload": payload,
    }
    created_at = _read(event, ("created_at",), None)
    if created_at is not None:
        visible["created_at"] = _to_json_value(created_at)
    return visible


def _is_public_event(event: Any) -> bool:
    visibility = _string_or_none(_read(event, ("visibility",), None))
    if visibility is not None and visibility != "public":
        return False
    public_flag = _read(event, ("public",), None)
    return public_flag is not False


def _event_type(event: Any) -> str:
    return str(_enum_value(_read(event, ("event_type", "type", "event"), "")) or "")


def _event_payload(event: Any) -> Mapping[str, Any]:
    payload = _read(event, ("public_payload", "payload"), None)
    if payload is None:
        return {}
    if not isinstance(payload, Mapping):
        raise ValueError("public event payload must be a mapping")
    return payload


def _shown_cards_by_seat(
    state_summary: Any,
    public_events: Iterable[Any],
    player_to_seat: Mapping[Identifier, int],
) -> dict[int, tuple[str, ...]]:
    shown = _indexed_card_mapping(_read(state_summary, ("shown_cards_by_seat",), {}))
    for event in public_events:
        if not _is_public_event(event) or _event_type(event) not in _SHOWDOWN_EVENT_TYPES:
            continue
        _merge_shown_cards_from_payload(shown, _event_payload(event), player_to_seat)
    return shown


def _merge_shown_cards_from_payload(
    shown: dict[int, tuple[str, ...]],
    payload: Mapping[str, Any],
    player_to_seat: Mapping[Identifier, int],
) -> None:
    for key in ("shown_cards_by_seat", "revealed_cards_by_seat", "hole_cards_by_seat"):
        indexed = _read(payload, (key,), None)
        if indexed is not None:
            shown.update(_indexed_card_mapping(indexed))

    for raw_entry in _showdown_entries(payload):
        seat_index = _seat_from_entry(raw_entry, player_to_seat)
        if seat_index is None:
            continue
        cards = _first_defined(
            _read(raw_entry, ("shown_cards",), None),
            _read(raw_entry, ("hole_cards",), None),
            _read(raw_entry, ("cards",), None),
        )
        if cards is not None:
            shown[seat_index] = _string_tuple(cards, "shown_cards")


def _showdown_entries(payload: Mapping[str, Any]) -> tuple[Any, ...]:
    entries: list[Any] = []
    for key in ("players", "revealed", "showdown", "showdown_summary", "entries"):
        value = _read(payload, (key,), None)
        if value is not None:
            entries.extend(_as_iterable(value))
    if any(
        key in payload for key in ("seat_index", "player_id", "shown_cards", "hole_cards", "cards")
    ):
        entries.append(payload)
    return tuple(entries)


def _seat_from_entry(entry: Any, player_to_seat: Mapping[Identifier, int]) -> int | None:
    seat_index = _int_or_none(_read(entry, ("seat_index", "seat", "index"), None))
    if seat_index is not None:
        return seat_index
    player_id = _read(entry, ("player_id",), None)
    return player_to_seat.get(player_id)


def _folded_seats(public_events: Iterable[Any]) -> set[int]:
    folded: set[int] = set()
    for event in public_events:
        if not _is_public_event(event):
            continue
        payload = _event_payload(event)
        action = str(_enum_value(_read(payload, ("action", "action_type"), "")) or "").casefold()
        if action in {"fold", "folded"}:
            seat_index = _int_or_none(
                _first_defined(
                    _read(event, ("actor_seat_index",), None),
                    _read(payload, ("seat_index",), None),
                )
            )
            if seat_index is not None:
                folded.add(seat_index)
    return folded


def _board_cards(
    state_summary: Any, table_snapshot: Any, public_events: Iterable[Any]
) -> tuple[str, ...]:
    cards = _first_defined(
        _read(state_summary, ("board_cards", "board"), None),
        _read(table_snapshot, ("board_cards", "board"), None),
    )
    if cards is not None:
        return _string_tuple(cards, "board_cards")

    board: tuple[str, ...] = ()
    for event in public_events:
        if not _is_public_event(event) or _event_type(event) != "board_dealt":
            continue
        payload = _event_payload(event)
        board = _string_tuple(
            _first_defined(_read(payload, ("board",), None), _read(payload, ("cards",), ())),
            "board_cards",
        )
    return board


def _seats_by_index(table_snapshot: Any) -> dict[int, Any]:
    raw_seats = _read(table_snapshot, ("seats", "visible_seats"), ())
    seats: dict[int, Any] = {}
    for fallback_index, raw_seat in enumerate(_as_iterable(raw_seats)):
        seat_index = _int_or_none(_read(raw_seat, ("seat_index", "index"), fallback_index))
        if seat_index is None or seat_index < 0 or seat_index >= SEAT_COUNT:
            continue
        seats[seat_index] = raw_seat
    return seats


def _player_to_seat(seats_by_index: Mapping[int, Any]) -> dict[Identifier, int]:
    return {
        player_id: seat_index
        for seat_index, seat in seats_by_index.items()
        if (player_id := _read(seat, ("player_id",), None)) is not None
    }


def _resolve_observer_seat(
    *,
    observer_player_id: Identifier | None,
    observer_seat_index: int | None,
    player_to_seat: Mapping[Identifier, int],
) -> int:
    if observer_seat_index is not None:
        return _require_seat_index(observer_seat_index)
    if observer_player_id is not None and observer_player_id in player_to_seat:
        return player_to_seat[observer_player_id]
    raise ValueError("observer_seat_index is required when observer_player_id is not seated")


def _resolve_observer_player(
    *,
    observer_player_id: Identifier | None,
    observer_seat_index: int,
    seats_by_index: Mapping[int, Any],
) -> Identifier:
    if observer_player_id is not None:
        return _require_identifier(observer_player_id)
    player_id = _read(seats_by_index.get(observer_seat_index), ("player_id",), None)
    return _require_identifier(player_id)


def _actor_ref(state_summary: Any) -> Any:
    return _first_defined(
        _read(state_summary, ("current_actor", "actor", "action_player"), None),
        {
            "seat_index": _read(
                state_summary,
                ("current_actor_seat_index", "actor_seat_index", "action_seat_index"),
                None,
            ),
            "player_id": _read(
                state_summary,
                ("current_actor_player_id", "actor_player_id", "action_player_id"),
                None,
            ),
        },
    )


def _actor_seat_index(actor: Any, player_to_seat: Mapping[Identifier, int]) -> int | None:
    if isinstance(actor, int) and not isinstance(actor, bool):
        return actor
    seat_index = _int_or_none(_read(actor, ("seat_index", "seat", "index"), None))
    if seat_index is not None:
        return seat_index
    player_id = _actor_player_id(actor)
    if player_id is not None:
        return player_to_seat.get(player_id)
    return None


def _actor_player_id(actor: Any) -> Identifier | None:
    if isinstance(actor, str):
        return actor
    return _optional_identifier(_read(actor, ("player_id",), None))


def _button_seat_index(table_snapshot: Any, state_summary: Any) -> int:
    value = _first_defined(
        _read(table_snapshot, ("button_seat_index",), None),
        _read(_read(table_snapshot, ("hand_context",), None), ("button_seat_index",), None),
        _read(state_summary, ("button_seat_index",), None),
        0,
    )
    return _require_seat_index(value)


def _visible_status(
    *,
    raw_status: Any,
    player_id: Any,
    seat_index: int,
    folded_seats: set[int],
    stack: int,
    hole_card_count: int,
) -> str:
    if player_id is None:
        return "empty"
    if seat_index in folded_seats:
        return "folded"
    normalized = _string_or_none(raw_status)
    if normalized in {"folded", "all_in", "sitting_out"}:
        return normalized
    if hole_card_count > 0 and stack == 0:
        return "all_in"
    if normalized in {"in_hand", "seated"}:
        return "active"
    return normalized or "active"


def _status_string(status: Any, player_id: Any) -> str:
    normalized = _string_or_none(status)
    if normalized:
        return normalized
    return "active" if player_id is not None else "empty"


def _indexed_amounts(value: Any) -> dict[int, int]:
    if value is None:
        return {}
    if isinstance(value, Mapping):
        return {
            int(key): _chip_amount(amount, "amount")
            for key, amount in value.items()
            if _can_parse_index(key)
        }
    return {
        index: _chip_amount(amount, "amount") for index, amount in enumerate(_as_iterable(value))
    }


def _indexed_card_mapping(value: Any) -> dict[int, tuple[str, ...]]:
    if value is None:
        return {}
    if isinstance(value, Mapping):
        return {
            int(key): _string_tuple(cards, "cards")
            for key, cards in value.items()
            if _can_parse_index(key)
        }
    return {index: _string_tuple(cards, "cards") for index, cards in enumerate(_as_iterable(value))}


def _indexed_or_raw(
    indexed: Mapping[int, int],
    seat_index: int,
    raw_seat: Any,
    names: tuple[str, ...],
) -> int:
    if seat_index in indexed:
        return indexed[seat_index]
    return _chip_amount(_read(raw_seat, names, 0), names[0])


def _can_parse_index(value: Any) -> bool:
    try:
        int(value)
    except (TypeError, ValueError):
        return False
    return True


def _read(value: Any, names: tuple[str, ...], default: Any = _MISSING) -> Any:
    if value is None:
        if default is _MISSING:
            raise ValueError(f"missing required field {names[0]}")
        return default
    for name in names:
        if isinstance(value, Mapping) and name in value:
            return value[name]
        if hasattr(value, name):
            return getattr(value, name)
    if default is _MISSING:
        raise ValueError(f"missing required field {names[0]}")
    return default


def _first_defined(*values: Any) -> Any:
    for value in values:
        if value is not None:
            return value
    return None


def _first_identifier(*values: Any) -> Identifier:
    for value in values:
        if value is not None:
            return _require_identifier(value)
    raise ValueError("identifier is required")


def _require_identifier(value: Any) -> Identifier:
    if isinstance(value, bool) or not isinstance(value, str | int) or value == "":
        raise ValueError("identifier must be a non-empty string or integer")
    return value


def _optional_identifier(value: Any) -> Identifier | None:
    if value is None:
        return None
    return _require_identifier(value)


def _optional_string(value: Any) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError("value must be a string or None")
    return value


def _string_or_none(value: Any) -> str | None:
    if value is None:
        return None
    normalized = _enum_value(value)
    if normalized is None:
        return None
    return str(normalized).strip().lower().replace("-", "_")


def _require_seat_index(value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0 or value >= SEAT_COUNT:
        raise ValueError(f"seat_index must be between 0 and {SEAT_COUNT - 1}")
    return value


def _int_or_none(value: Any) -> int | None:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        try:
            return int(value)
        except ValueError:
            return None
    return None


def _optional_int(value: Any, default: int) -> int:
    parsed = _int_or_none(value)
    return default if parsed is None else parsed


def _chip_amount(value: Any, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{name} must be a non-negative integer")
    return value


def _optional_chip_amount(value: Any, name: str) -> int | None:
    if value is None:
        return None
    return _chip_amount(value, name)


def _string_tuple(value: Any, name: str) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str | bytes) or not isinstance(value, Iterable):
        raise ValueError(f"{name} must be an iterable of card strings")
    return tuple(_card_string(card, name) for card in value)


def _card_string(value: Any, name: str) -> str:
    _reject_runtime_object(value, name)
    if not isinstance(value, str):
        value = str(value)
    if not value:
        raise ValueError(f"{name} cannot contain blank cards")
    return value


def _as_iterable(value: Any) -> tuple[Any, ...]:
    if value is None:
        return ()
    if isinstance(value, Mapping):
        return tuple(value.values())
    if isinstance(value, str | bytes) or not isinstance(value, Iterable):
        return (value,)
    return tuple(value)


def _object_to_public_mapping(value: Any, *, allow_private_cards: bool) -> dict[str, JSONValue]:
    if isinstance(value, Mapping):
        return _sanitize_public_mapping(value, allow_private_cards=allow_private_cards)
    if hasattr(value, "to_dict") and callable(value.to_dict):
        return _sanitize_public_mapping(value.to_dict(), allow_private_cards=allow_private_cards)
    if hasattr(value, "__dataclass_fields__"):
        return _sanitize_public_mapping(
            {field_name: getattr(value, field_name) for field_name in value.__dataclass_fields__},
            allow_private_cards=allow_private_cards,
        )
    if hasattr(value, "__dict__"):
        return _sanitize_public_mapping(vars(value), allow_private_cards=allow_private_cards)
    raise ValueError("value must be mapping-like")


def _sanitize_public_mapping(
    value: Mapping[str, Any], *, allow_private_cards: bool
) -> dict[str, JSONValue]:
    sanitized: dict[str, JSONValue] = {}
    for raw_key, raw_item in value.items():
        key = str(raw_key)
        normalized_key = key.lower().replace("-", "_").replace(" ", "_")
        if normalized_key in _ALWAYS_HIDDEN_KEYS:
            continue
        if not allow_private_cards and normalized_key in _PRIVATE_CARD_KEYS:
            continue
        if normalized_key == "private_payload":
            continue
        sanitized[key] = _to_json_value(raw_item, allow_private_cards=allow_private_cards)
    return sanitized


def _to_json_value(value: Any, *, allow_private_cards: bool = False) -> JSONValue:
    _reject_runtime_object(value, "value")
    if value is None or isinstance(value, str):
        return value
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        if not isfinite(value):
            raise ValueError("value cannot contain non-finite floats")
        return value
    if isinstance(value, Enum):
        return str(_enum_value(value))
    if isinstance(value, Mapping):
        return _sanitize_public_mapping(value, allow_private_cards=allow_private_cards)
    if isinstance(value, Sequence) and not isinstance(value, str | bytes):
        return [_to_json_value(item, allow_private_cards=allow_private_cards) for item in value]
    if hasattr(value, "isoformat") and callable(value.isoformat):
        return str(value.isoformat())
    return str(value)


def _enum_value(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    return value


def _reject_runtime_object(value: Any, name: str) -> None:
    module_name = getattr(type(value), "__module__", "")
    if module_name == "pokerkit" or module_name.startswith("pokerkit."):
        raise ValueError(f"{name} cannot contain PokerKit runtime objects")
