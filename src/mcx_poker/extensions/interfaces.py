"""Future extension interface boundaries for mcx-poker.

The MVP intentionally keeps LLM players, solver integration, coach pages,
statistics databases, network calls, and PokerKit objects out of this module.
Future extensions consume only platform DTOs such as observations, table
snapshots, public hand events, and persisted hand-review inputs.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field, fields, is_dataclass, replace
from enum import Enum, StrEnum
from typing import Any, Protocol, runtime_checkable

MVP_EXCLUSIONS: tuple[str, ...] = (
    "real_llm_player",
    "real_solver",
    "coach_page",
    "statistics_database",
    "network_dependency",
)
"""Capabilities reserved for future work, not implemented by the MVP."""

ALLOWED_EXTENSION_INPUT_TYPES: tuple[str, ...] = (
    "PlayerObservation",
    "TableSnapshot",
    "HandEvent",
    "HandReviewInput",
)
"""Platform DTOs that future extension interfaces are allowed to consume."""

REPLAY_HAND_HISTORY_REQUIREMENT = (
    "Replay depends on persisted Hand History; the temporary hand event log is "
    "not a cross-restart replay source."
)

_FORBIDDEN_INPUT_KEYS = frozenset(
    {
        "all_hole_cards",
        "controller_private_state",
        "deck",
        "deck_order",
        "future_cards",
        "hole_cards_by_player",
        "opponent_hole_cards",
        "pokerkit_state",
        "private_controller_state",
        "raw_pokerkit_state",
        "raw_state",
        "undealt_cards",
        "unshown_hole_cards",
    }
)


class ExtensionInterfaceError(ValueError):
    """Base error for invalid extension boundary use."""


class ExtensionInputRejected(ExtensionInterfaceError):
    """Raised when a value attempts to cross the extension boundary unsafely."""


class NoLegalActionAvailable(ExtensionInterfaceError):
    """Raised when an actionable observation has no enabled platform action."""


class ActionType(StrEnum):
    """Platform action semantics shared by humans, bots, and future agents."""

    FOLD = "Fold"
    CHECK = "Check"
    CALL = "Call"
    RAISE_TO = "RaiseTo"
    ALL_IN = "AllIn"


class PlatformDTO:
    """Marker base for DTOs that are safe to pass into extension interfaces."""

    def to_extension_payload(self) -> dict[str, Any]:
        """Return a JSON-compatible payload after hidden-information checks."""

        payload = _to_serializable(self, ())
        if not isinstance(payload, dict):
            raise ExtensionInputRejected("top-level extension payload must be an object")
        return payload


@dataclass(frozen=True)
class LegalAction(PlatformDTO):
    """Visible legal-action description exposed by the Observation System."""

    action_type: ActionType | str
    enabled: bool = True
    amount_min: int | None = None
    amount_max: int | None = None
    amount_fixed: int | None = None
    reason_if_disabled: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "action_type", normalize_action_type(self.action_type))


@dataclass(frozen=True)
class PlayerAction(PlatformDTO):
    """Platform action returned by a controller implementation."""

    player_id: str
    seat_index: int
    hand_id: str
    turn_id: str
    action_type: ActionType | str
    amount: int | None = None
    source: str = "future_agent"

    def __post_init__(self) -> None:
        action_type = normalize_action_type(self.action_type)
        object.__setattr__(self, "action_type", action_type)
        if action_type is ActionType.RAISE_TO and self.amount is None:
            raise ExtensionInterfaceError("RaiseTo actions require an amount")
        if action_type is not ActionType.RAISE_TO and self.amount is not None:
            raise ExtensionInterfaceError("only RaiseTo actions may carry an amount")


@dataclass(frozen=True)
class VisibleSeat(PlatformDTO):
    """Seat state visible to the observing player."""

    seat_index: int
    player_id: str | None = None
    player_name: str | None = None
    stack: int = 0
    current_bet: int = 0
    status: str = "empty"
    hole_card_count: int = 0
    shown_cards: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "shown_cards", tuple(self.shown_cards))
        if self.hole_card_count < 0:
            raise ExtensionInterfaceError("hole_card_count cannot be negative")


@dataclass(frozen=True)
class HandEvent(PlatformDTO):
    """Public hand event suitable for extension inputs and future replay."""

    event_id: str
    hand_id: str
    event_type: str
    payload: Mapping[str, Any] = field(default_factory=dict)
    public: bool = True

    def __post_init__(self) -> None:
        if not self.public:
            raise ExtensionInputRejected("extension inputs accept only public hand events")
        validate_extension_input(self.payload)


@dataclass(frozen=True)
class TableSnapshot(PlatformDTO):
    """Platform-level table snapshot; it is not a PokerKit state object."""

    table_id: str
    hand_id: str | None
    button_seat_index: int
    visible_seats: tuple[VisibleSeat, ...]
    board_cards: tuple[str, ...] = ()
    pot_summary: Mapping[str, int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "visible_seats", tuple(self.visible_seats))
        object.__setattr__(self, "board_cards", tuple(self.board_cards))


@dataclass(frozen=True)
class PlayerObservation(PlatformDTO):
    """Per-player platform observation passed to controllers and agents.

    This DTO includes the observer's own hole cards and public cards only. It
    has no field for undealt cards, PokerKit state, opponent unshown hole cards,
    or controller-private state.
    """

    observer_player_id: str
    observer_seat_index: int
    table_id: str
    hand_id: str
    turn_id: str
    is_actor: bool
    button_seat_index: int
    own_hole_cards: tuple[str, ...] = ()
    board_cards: tuple[str, ...] = ()
    visible_seats: tuple[VisibleSeat, ...] = ()
    pot_summary: Mapping[str, int] = field(default_factory=dict)
    bet_summary: Mapping[str, int] = field(default_factory=dict)
    visible_action_history: tuple[HandEvent, ...] = ()
    legal_actions: tuple[LegalAction, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "own_hole_cards", tuple(self.own_hole_cards))
        object.__setattr__(self, "board_cards", tuple(self.board_cards))
        object.__setattr__(self, "visible_seats", tuple(self.visible_seats))
        object.__setattr__(self, "visible_action_history", tuple(self.visible_action_history))
        object.__setattr__(self, "legal_actions", tuple(self.legal_actions))
        for event in self.visible_action_history:
            if not event.public:
                raise ExtensionInputRejected("visible_action_history accepts only public events")


@dataclass(frozen=True)
class HandReviewInput(PlatformDTO):
    """Coach and analysis input built from Hand History or public events."""

    hand_id: str
    public_events: tuple[HandEvent, ...] = ()
    persisted_hand_history_id: str | None = None
    table_snapshot: TableSnapshot | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "public_events", tuple(self.public_events))
        for event in self.public_events:
            if not event.public:
                raise ExtensionInputRejected("hand review accepts only public events")


@dataclass(frozen=True)
class ActionRequestContext(PlatformDTO):
    """Context attached to a controller action request."""

    table_id: str
    hand_id: str
    turn_id: str
    player_id: str
    seat_index: int


@runtime_checkable
class PlayerController(Protocol):
    """Controller boundary consumed by the Game Loop."""

    def request_action(
        self,
        observation: PlayerObservation,
        action_request_context: ActionRequestContext | None = None,
    ) -> PlayerAction:
        """Return one platform action for the supplied observation."""
        ...

    def notify_action_rejected(self, action_error: object) -> None:
        """Receive an action rejection notification from the platform."""
        ...

    def notify_hand_started(self, hand_context: object) -> None:
        """Receive a hand-started notification."""
        ...

    def notify_hand_ended(self, result_summary: object) -> None:
        """Receive a hand-ended notification."""
        ...


class BaseFutureController:
    """No-op lifecycle hooks shared by fake future controllers."""

    last_error: Exception | None

    def notify_action_rejected(self, action_error: object) -> None:
        return None

    def notify_hand_started(self, hand_context: object) -> None:
        return None

    def notify_hand_ended(self, result_summary: object) -> None:
        return None


class ControllerRegistry:
    """Small registry used to verify future controller pluggability."""

    def __init__(self) -> None:
        self._controllers: dict[str, PlayerController] = {}

    def register(self, player_id: str, controller: PlayerController) -> None:
        if not callable(getattr(controller, "request_action", None)):
            raise TypeError("controller must provide request_action")
        self._controllers[player_id] = controller

    def get(self, player_id: str) -> PlayerController:
        try:
            return self._controllers[player_id]
        except KeyError as exc:
            raise KeyError(f"no controller registered for player {player_id!r}") from exc

    def request_action(
        self,
        player_id: str,
        observation: PlayerObservation,
        action_request_context: ActionRequestContext | None = None,
    ) -> PlayerAction:
        return self.get(player_id).request_action(observation, action_request_context)


class LLMInputBuilder(Protocol):
    """Draft interface for converting an observation into model input."""

    def build_input(self, observation: PlayerObservation) -> Mapping[str, Any]:
        """Build structured input from a platform observation."""
        ...


class LLMClient(Protocol):
    """Draft interface for a future model client.

    Implementations must not require API keys, SDKs, or network calls in the
    MVP. The fake implementation below is deterministic and local.
    """

    def complete(self, structured_input: Mapping[str, Any]) -> str:
        """Return a model-like action string."""
        ...


class LLMActionParser(Protocol):
    """Draft parser interface that converts model output to PlayerAction."""

    def parse_action(self, model_output: str, observation: PlayerObservation) -> PlayerAction:
        """Parse model output into a platform action."""
        ...


class ObservationLLMInputBuilder:
    """Local input builder that serializes only the safe observation payload."""

    def build_input(self, observation: PlayerObservation) -> Mapping[str, Any]:
        return observation.to_extension_payload()


@dataclass(frozen=True)
class DeterministicLLMClient:
    """Fake local LLM client used only for boundary tests."""

    output: str = "Check"

    def complete(self, structured_input: Mapping[str, Any]) -> str:
        validate_extension_input(structured_input)
        return self.output


class SimpleLLMActionParser:
    """Parser for the tiny deterministic fake model vocabulary."""

    def parse_action(self, model_output: str, observation: PlayerObservation) -> PlayerAction:
        action_type, amount = parse_action_text(model_output)
        return action_from_observation(
            observation,
            requested_action=action_type,
            requested_amount=amount,
            source="future_agent",
        )


class LLMPlayerController(BaseFutureController):
    """Fake future LLM controller that needs no model dependency."""

    def __init__(
        self,
        input_builder: LLMInputBuilder | None = None,
        client: LLMClient | None = None,
        parser: LLMActionParser | None = None,
        source: str = "future_agent",
    ) -> None:
        self.input_builder = input_builder or ObservationLLMInputBuilder()
        self.client = client or DeterministicLLMClient()
        self.parser = parser or SimpleLLMActionParser()
        self.source = source
        self.last_error = None

    def request_action(
        self,
        observation: PlayerObservation,
        action_request_context: ActionRequestContext | None = None,
    ) -> PlayerAction:
        del action_request_context
        validate_extension_input(observation)
        try:
            structured_input = self.input_builder.build_input(observation)
            validate_extension_input(structured_input)
            model_output = self.client.complete(structured_input)
            action = self.parser.parse_action(model_output, observation)
            self.last_error = None
            return replace(action, source=self.source)
        except Exception as exc:
            self.last_error = exc
            return action_from_observation(observation, source=self.source)


@dataclass(frozen=True)
class StrategyQuery(PlatformDTO):
    """Platform-only strategy query for future solver or lookup layers."""

    table_id: str
    hand_id: str
    actor_player_id: str
    actor_seat_index: int
    board_cards: tuple[str, ...]
    pot_summary: Mapping[str, int]
    bet_summary: Mapping[str, int]
    legal_actions: tuple[LegalAction, ...]
    public_events: tuple[HandEvent, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "board_cards", tuple(self.board_cards))
        object.__setattr__(self, "legal_actions", tuple(self.legal_actions))
        object.__setattr__(self, "public_events", tuple(self.public_events))


class StrategyQueryBuilder(Protocol):
    """Draft strategy-query builder consuming only platform DTOs."""

    def build_query(
        self,
        source: PlayerObservation | TableSnapshot | HandReviewInput,
    ) -> StrategyQuery:
        """Build a strategy query from platform state or hand history input."""
        ...


class SolverClient(Protocol):
    """Draft solver client interface with no solver dependency in the MVP."""

    def solve(self, query: StrategyQuery) -> StrategyResult:
        """Return a strategy result for a platform-only query."""
        ...


@dataclass(frozen=True)
class StrategyResult(PlatformDTO):
    """Future GTO result shape with optional frequencies and EVs."""

    recommended_action: ActionType | str | None = None
    recommended_amount: int | None = None
    action_frequencies: Mapping[str, float] = field(default_factory=dict)
    expected_values: Mapping[str, float] = field(default_factory=dict)
    notes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.recommended_action is not None:
            object.__setattr__(
                self,
                "recommended_action",
                normalize_action_type(self.recommended_action),
            )
        object.__setattr__(self, "notes", tuple(self.notes))


class ObservationStrategyQueryBuilder:
    """Build a solver query from a current player observation."""

    def build_query(
        self,
        source: PlayerObservation | TableSnapshot | HandReviewInput,
    ) -> StrategyQuery:
        if not isinstance(source, PlayerObservation):
            raise ExtensionInterfaceError("fake query builder requires PlayerObservation")
        validate_extension_input(source)
        return StrategyQuery(
            table_id=source.table_id,
            hand_id=source.hand_id,
            actor_player_id=source.observer_player_id,
            actor_seat_index=source.observer_seat_index,
            board_cards=source.board_cards,
            pot_summary=source.pot_summary,
            bet_summary=source.bet_summary,
            legal_actions=source.legal_actions,
            public_events=source.visible_action_history,
        )


class NoopSolverClient:
    """Fake local solver that recommends the first enabled fallback action."""

    def solve(self, query: StrategyQuery) -> StrategyResult:
        validate_extension_input(query)
        legal_action = first_enabled_legal_action(query.legal_actions)
        return StrategyResult(recommended_action=legal_action.action_type)


class GTOPlayerController(BaseFutureController):
    """Fake GTO controller that falls back if the solver boundary fails."""

    def __init__(
        self,
        query_builder: StrategyQueryBuilder | None = None,
        solver_client: SolverClient | None = None,
        source: str = "future_agent",
    ) -> None:
        self.query_builder = query_builder or ObservationStrategyQueryBuilder()
        self.solver_client = solver_client or NoopSolverClient()
        self.source = source
        self.last_error = None

    def request_action(
        self,
        observation: PlayerObservation,
        action_request_context: ActionRequestContext | None = None,
    ) -> PlayerAction:
        del action_request_context
        validate_extension_input(observation)
        try:
            query = self.query_builder.build_query(observation)
            result = self.solver_client.solve(query)
            action = action_from_observation(
                observation,
                requested_action=result.recommended_action,
                requested_amount=result.recommended_amount,
                source=self.source,
            )
            self.last_error = None
            return action
        except Exception as exc:
            self.last_error = exc
            return action_from_observation(observation, source=self.source)


@dataclass(frozen=True)
class DecisionAssessment(PlatformDTO):
    """Draft analysis result for one public decision point."""

    hand_id: str
    turn_id: str
    player_id: str
    action_taken: ActionType | str
    notes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "action_taken", normalize_action_type(self.action_taken))
        object.__setattr__(self, "notes", tuple(self.notes))


@dataclass(frozen=True)
class CoachFeedback(PlatformDTO):
    """Future coach feedback DTO; no coach page is implemented in the MVP."""

    feedback_id: str
    player_id: str
    severity: str
    message: str
    training_focus: str | None = None
    related_hand_ids: tuple[str, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "related_hand_ids", tuple(self.related_hand_ids))
        validate_extension_input(self.metadata)


class DecisionAnalyzer(Protocol):
    """Draft interface for future hand-review decision analysis."""

    def analyze(self, review_input: HandReviewInput) -> tuple[DecisionAssessment, ...]:
        """Analyze public hand-review input into decision assessments."""
        ...


class LeakDetector(Protocol):
    """Draft interface for future leak detection."""

    def detect_leaks(
        self,
        review_input: HandReviewInput,
        decisions: Sequence[DecisionAssessment],
    ) -> tuple[CoachFeedback, ...]:
        """Detect stable error patterns from public review inputs."""
        ...


def normalize_action_type(action_type: ActionType | str) -> ActionType:
    """Normalize action type spelling used by draft extension fakes."""

    if isinstance(action_type, ActionType):
        return action_type
    token = str(action_type).replace("-", "").replace("_", "").replace(" ", "").lower()
    aliases = {
        "allin": ActionType.ALL_IN,
        "call": ActionType.CALL,
        "check": ActionType.CHECK,
        "fold": ActionType.FOLD,
        "raise": ActionType.RAISE_TO,
        "raiseto": ActionType.RAISE_TO,
    }
    try:
        return aliases[token]
    except KeyError as exc:
        raise ExtensionInterfaceError(f"unknown action type: {action_type!r}") from exc


def parse_action_text(text: str) -> tuple[ActionType, int | None]:
    """Parse fake LLM action text such as ``Check`` or ``RaiseTo(120)``."""

    cleaned = text.strip()
    if "(" in cleaned and cleaned.endswith(")"):
        name, raw_amount = cleaned[:-1].split("(", 1)
        amount = int(raw_amount.strip())
        return normalize_action_type(name), amount
    if ":" in cleaned:
        name, raw_amount = cleaned.split(":", 1)
        return normalize_action_type(name), int(raw_amount.strip())
    return normalize_action_type(cleaned), None


def first_enabled_legal_action(legal_actions: Sequence[LegalAction]) -> LegalAction:
    """Return the safest enabled action in deterministic fallback order."""

    enabled = [action for action in legal_actions if action.enabled]
    if not enabled:
        raise NoLegalActionAvailable("observation does not expose an enabled action")
    for action_type in (
        ActionType.CHECK,
        ActionType.CALL,
        ActionType.FOLD,
        ActionType.ALL_IN,
        ActionType.RAISE_TO,
    ):
        for legal_action in enabled:
            if legal_action.action_type is action_type:
                return legal_action
    return enabled[0]


def action_from_observation(
    observation: PlayerObservation,
    requested_action: ActionType | str | None = None,
    requested_amount: int | None = None,
    source: str = "future_agent",
) -> PlayerAction:
    """Build a legal platform action from an observation.

    If the requested action is absent or disabled, the function chooses a local
    deterministic fallback from the observation's legal action set.
    """

    if requested_action is None:
        legal_action = first_enabled_legal_action(observation.legal_actions)
    else:
        requested = normalize_action_type(requested_action)
        matched_action = next(
            (
                action
                for action in observation.legal_actions
                if action.enabled and action.action_type is requested
            ),
            None,
        )
        if matched_action is None:
            legal_action = first_enabled_legal_action(observation.legal_actions)
            requested_amount = None
        else:
            legal_action = matched_action
    amount = _amount_for_legal_action(legal_action, requested_amount)
    return PlayerAction(
        player_id=observation.observer_player_id,
        seat_index=observation.observer_seat_index,
        hand_id=observation.hand_id,
        turn_id=observation.turn_id,
        action_type=legal_action.action_type,
        amount=amount,
        source=source,
    )


def validate_extension_input(value: object) -> None:
    """Reject PokerKit objects and hidden-information fields recursively."""

    _to_serializable(value, ())


def _amount_for_legal_action(
    legal_action: LegalAction,
    requested_amount: int | None,
) -> int | None:
    if legal_action.action_type is not ActionType.RAISE_TO:
        return None
    amount = requested_amount or legal_action.amount_fixed or legal_action.amount_min
    if amount is None:
        raise ExtensionInterfaceError("RaiseTo legal action requires an amount boundary")
    if legal_action.amount_min is not None and amount < legal_action.amount_min:
        raise ExtensionInterfaceError("RaiseTo amount is below the legal minimum")
    if legal_action.amount_max is not None and amount > legal_action.amount_max:
        raise ExtensionInterfaceError("RaiseTo amount is above the legal maximum")
    return amount


def _to_serializable(value: object, path: tuple[str, ...]) -> object:
    if _is_pokerkit_object(value):
        raise ExtensionInputRejected(f"PokerKit object rejected at {'.'.join(path) or '<root>'}")
    if value is None or isinstance(value, str | int | float | bool):
        return value
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Mapping):
        result: dict[str, object] = {}
        for key, item in value.items():
            key_text = str(key)
            _reject_forbidden_key(key_text, path)
            result[key_text] = _to_serializable(item, (*path, key_text))
        return result
    if is_dataclass(value):
        if not isinstance(value, PlatformDTO):
            raise ExtensionInputRejected(
                f"non-platform dataclass rejected at {'.'.join(path) or '<root>'}"
            )
        result = {}
        for item in fields(value):
            _reject_forbidden_key(item.name, path)
            result[item.name] = _to_serializable(getattr(value, item.name), (*path, item.name))
        return result
    if isinstance(value, Sequence) and not isinstance(value, str | bytes | bytearray):
        return [_to_serializable(item, (*path, "[]")) for item in value]
    raise ExtensionInputRejected(
        f"unsupported extension input {type(value).__name__} at {'.'.join(path) or '<root>'}"
    )


def _reject_forbidden_key(key: str, path: tuple[str, ...]) -> None:
    normalized = key.lower()
    if normalized in _FORBIDDEN_INPUT_KEYS or normalized.startswith("pokerkit_"):
        location = ".".join((*path, key))
        raise ExtensionInputRejected(f"hidden or internal field rejected: {location}")


def _is_pokerkit_object(value: object) -> bool:
    module = type(value).__module__
    return module == "pokerkit" or module.startswith("pokerkit.")


__all__ = [
    "ALLOWED_EXTENSION_INPUT_TYPES",
    "MVP_EXCLUSIONS",
    "REPLAY_HAND_HISTORY_REQUIREMENT",
    "ActionRequestContext",
    "ActionType",
    "BaseFutureController",
    "CoachFeedback",
    "ControllerRegistry",
    "DecisionAnalyzer",
    "DecisionAssessment",
    "DeterministicLLMClient",
    "ExtensionInputRejected",
    "ExtensionInterfaceError",
    "GTOPlayerController",
    "HandEvent",
    "HandReviewInput",
    "LLMActionParser",
    "LLMClient",
    "LLMInputBuilder",
    "LLMPlayerController",
    "LeakDetector",
    "LegalAction",
    "NoLegalActionAvailable",
    "NoopSolverClient",
    "ObservationLLMInputBuilder",
    "ObservationStrategyQueryBuilder",
    "PlatformDTO",
    "PlayerAction",
    "PlayerController",
    "PlayerObservation",
    "SimpleLLMActionParser",
    "SolverClient",
    "StrategyQuery",
    "StrategyQueryBuilder",
    "StrategyResult",
    "TableSnapshot",
    "VisibleSeat",
    "action_from_observation",
    "first_enabled_legal_action",
    "normalize_action_type",
    "parse_action_text",
    "validate_extension_input",
]
