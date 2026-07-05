"""Long-lived local table state and hand lifecycle management."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Protocol, Self, runtime_checkable

SEAT_COUNT = 6
DEFAULT_TABLE_ID = "local-table"
DEFAULT_SMALL_BLIND = 1
DEFAULT_BIG_BLIND = 2
DEFAULT_ANTE = 0
DEFAULT_STARTING_STACK = 200
DEFAULT_MIN_ACTIVE_PLAYERS = 2


class TableStatus(StrEnum):
    """Lifecycle state for the local table."""

    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    RESETTING = "resetting"


class SeatStatus(StrEnum):
    """Public occupancy state for a fixed table seat."""

    EMPTY = "empty"
    SEATED = "seated"
    SITTING_OUT = "sitting_out"
    IN_HAND = "in_hand"


class ControllerType(StrEnum):
    """Supported controller ownership types for seated players."""

    HUMAN = "human"
    BOT = "bot"
    FUTURE_AGENT = "future_agent"


class TableManagerError(ValueError):
    """Base platform error raised by table-manager commands."""

    code = "table_manager_error"

    def __init__(
        self,
        message: str | None = None,
        *,
        details: Mapping[str, object] | None = None,
    ) -> None:
        super().__init__(message or self.code.replace("_", " "))
        self.message = message or self.code.replace("_", " ")
        self.details = dict(details) if details is not None else None

    @property
    def error_code(self) -> str:
        return self.code

    def to_dict(self) -> dict[str, object]:
        return {"code": self.code, "message": self.message, "details": self.details}


class TableNotInitializedError(TableManagerError):
    code = "table_not_initialized"


class TableStateConflictError(TableManagerError):
    code = "table_state_conflict"


class SeatNotFoundError(TableManagerError):
    code = "seat_not_found"


class SeatOccupiedError(TableManagerError):
    code = "seat_occupied"


class PlayerAlreadySeatedError(TableManagerError):
    code = "player_already_seated"


class InvalidStackError(TableManagerError):
    code = "invalid_stack"


class NoCurrentHandError(TableManagerError):
    code = "no_current_hand"


class HandSettlementMismatchError(TableManagerError):
    code = "hand_settlement_mismatch"


class AdapterUnavailableError(TableManagerError):
    code = "adapter_unavailable"


@dataclass(slots=True)
class SeatState:
    """Mutable long-lived state for one fixed seat."""

    seat_index: int
    player_id: str | None = None
    player_name: str | None = None
    controller_type: ControllerType = ControllerType.HUMAN
    stack: int = 0
    status: SeatStatus = SeatStatus.EMPTY

    def to_snapshot(self) -> SeatSnapshot:
        return SeatSnapshot(
            seat_index=self.seat_index,
            player_id=self.player_id,
            player_name=self.player_name,
            controller_type=self.controller_type,
            stack=self.stack,
            status=self.status,
        )


@dataclass(slots=True)
class HandContext:
    """Mutable context for the currently active hand."""

    hand_id: str
    button_seat_index: int
    active_seat_indexes: tuple[int, ...]
    starting_stacks: dict[int, int]
    adapter_hand_ref: Any = None

    def to_snapshot(self) -> HandSnapshot:
        return HandSnapshot(
            hand_id=self.hand_id,
            button_seat_index=self.button_seat_index,
            active_seat_indexes=self.active_seat_indexes,
            starting_stacks=dict(self.starting_stacks),
        )


@dataclass(slots=True)
class TableState:
    """Mutable long-lived state for the single local table."""

    table_id: str
    seat_count: int
    status: TableStatus
    seats: list[SeatState]
    button_seat_index: int
    current_hand_id: str | None = None
    hand_context: HandContext | None = None


@dataclass(frozen=True, slots=True)
class SeatSnapshot:
    """Public seat state included in table snapshots."""

    seat_index: int
    player_id: str | None = None
    player_name: str | None = None
    controller_type: ControllerType = ControllerType.HUMAN
    stack: int = 0
    status: SeatStatus = SeatStatus.EMPTY

    def to_dict(self) -> dict[str, object]:
        return {
            "seat_index": self.seat_index,
            "player_id": self.player_id,
            "player_name": self.player_name,
            "controller_type": self.controller_type.value,
            "stack": self.stack,
            "status": self.status.value,
        }


@dataclass(frozen=True, slots=True)
class HandSnapshot:
    """Public summary for the current hand."""

    hand_id: str
    button_seat_index: int
    active_seat_indexes: tuple[int, ...]
    starting_stacks: dict[int, int]

    def __post_init__(self) -> None:
        object.__setattr__(self, "active_seat_indexes", tuple(self.active_seat_indexes))
        object.__setattr__(self, "starting_stacks", dict(self.starting_stacks))

    def to_dict(self) -> dict[str, object]:
        return {
            "hand_id": self.hand_id,
            "button_seat_index": self.button_seat_index,
            "active_seat_indexes": list(self.active_seat_indexes),
            "starting_stacks": dict(self.starting_stacks),
        }


@dataclass(frozen=True, slots=True)
class TableSnapshot:
    """Public table state safe for API, events, observations, and UI."""

    table_id: str
    status: TableStatus
    seat_count: int
    seats: tuple[SeatSnapshot, ...]
    button_seat_index: int
    current_hand_id: str | None = None
    current_hand: HandSnapshot | None = None

    @property
    def hand_id(self) -> str | None:
        return self.current_hand_id

    def to_dict(self) -> dict[str, object]:
        return {
            "table_id": self.table_id,
            "status": self.status.value,
            "seat_count": self.seat_count,
            "seats": [seat.to_dict() for seat in self.seats],
            "button_seat_index": self.button_seat_index,
            "current_hand_id": self.current_hand_id,
            "hand_id": self.current_hand_id,
            "current_hand": self.current_hand.to_dict() if self.current_hand else None,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), separators=(",", ":"), sort_keys=True)


@dataclass(frozen=True, slots=True)
class CreateHandRequest:
    """Platform-level input passed to the injected hand adapter."""

    hand_id: str
    seat_to_player: dict[int, str]
    starting_stacks: dict[int, int]
    button_seat_index: int
    small_blind: int = DEFAULT_SMALL_BLIND
    big_blind: int = DEFAULT_BIG_BLIND
    ante: int = DEFAULT_ANTE

    def __post_init__(self) -> None:
        object.__setattr__(self, "seat_to_player", dict(self.seat_to_player))
        object.__setattr__(self, "starting_stacks", dict(self.starting_stacks))

    def to_dict(self) -> dict[str, object]:
        return {
            "hand_id": self.hand_id,
            "seat_to_player": dict(self.seat_to_player),
            "starting_stacks": dict(self.starting_stacks),
            "button_seat_index": self.button_seat_index,
            "small_blind": self.small_blind,
            "big_blind": self.big_blind,
            "ante": self.ante,
        }


@dataclass(frozen=True, slots=True)
class HandSettlement:
    """Final hand result consumed by the table manager."""

    hand_id: str
    final_stacks: dict[int, int]
    payoffs: dict[int, int] = field(default_factory=dict)
    winners: tuple[Mapping[str, object], ...] = ()
    final_board: tuple[str, ...] = ()
    showdown_summary: Mapping[str, object] | None = None
    operations_summary: tuple[Mapping[str, object], ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "final_stacks", dict(self.final_stacks))
        object.__setattr__(self, "payoffs", dict(self.payoffs))
        object.__setattr__(self, "winners", tuple(self.winners))
        object.__setattr__(self, "final_board", tuple(self.final_board))
        object.__setattr__(self, "operations_summary", tuple(self.operations_summary))

    @classmethod
    def from_mapping(cls, data: Mapping[str, object]) -> Self:
        return cls(
            hand_id=_required_string(data.get("hand_id"), "hand_id"),
            final_stacks=_normalize_stack_mapping(data.get("final_stacks"), "final_stacks"),
            payoffs=_normalize_int_mapping(data.get("payoffs", {}), "payoffs"),
            winners=_normalize_mapping_sequence(data.get("winners", ()), "winners"),
            final_board=_normalize_string_sequence(data.get("final_board", ()), "final_board"),
            showdown_summary=_optional_mapping(data.get("showdown_summary"), "showdown_summary"),
            operations_summary=_normalize_mapping_sequence(
                data.get("operations_summary", ()),
                "operations_summary",
            ),
        )


@runtime_checkable
class HandAdapter(Protocol):
    """Adapter boundary used to create one hand from platform state."""

    def create_hand(self, request: CreateHandRequest) -> Any: ...


class TableManager:
    """Command surface for the unique local table."""

    def __init__(
        self,
        *,
        adapter: HandAdapter | None = None,
        table_id: str = DEFAULT_TABLE_ID,
        seat_count: int = SEAT_COUNT,
        default_starting_stack: int = DEFAULT_STARTING_STACK,
        minimum_active_players: int = DEFAULT_MIN_ACTIVE_PLAYERS,
        small_blind: int = DEFAULT_SMALL_BLIND,
        big_blind: int = DEFAULT_BIG_BLIND,
        ante: int = DEFAULT_ANTE,
    ) -> None:
        if seat_count != SEAT_COUNT:
            raise ValueError(f"seat_count must be {SEAT_COUNT}")
        self.adapter = adapter
        self.table_id = _required_string(table_id, "table_id")
        self.seat_count = seat_count
        self.default_starting_stack = _validate_positive_int(
            default_starting_stack,
            "default_starting_stack",
        )
        self.minimum_active_players = _validate_positive_int(
            minimum_active_players,
            "minimum_active_players",
        )
        if self.minimum_active_players > self.seat_count:
            raise ValueError("minimum_active_players cannot exceed seat_count")
        self.small_blind = _validate_non_negative_int(small_blind, "small_blind")
        self.big_blind = _validate_positive_int(big_blind, "big_blind")
        self.ante = _validate_non_negative_int(ante, "ante")
        self._state: TableState | None = None
        self._next_hand_number = 1

    @property
    def state(self) -> TableState:
        return self._require_state()

    def initialize_table(self, config: Mapping[str, object] | None = None) -> TableSnapshot:
        config = config or {}
        table_id = _required_string(config.get("table_id", self.table_id), "table_id")
        default_stack = _validate_positive_int(
            config.get("default_starting_stack", self.default_starting_stack),
            "default_starting_stack",
        )
        minimum_players = _validate_positive_int(
            config.get("minimum_active_players", self.minimum_active_players),
            "minimum_active_players",
        )
        if minimum_players > SEAT_COUNT:
            raise ValueError("minimum_active_players cannot exceed seat_count")

        self.table_id = table_id
        self.default_starting_stack = default_stack
        self.minimum_active_players = minimum_players
        self.small_blind = _validate_non_negative_int(
            config.get("small_blind", self.small_blind),
            "small_blind",
        )
        self.big_blind = _validate_positive_int(
            config.get("big_blind", self.big_blind), "big_blind"
        )
        self.ante = _validate_non_negative_int(config.get("ante", self.ante), "ante")
        self._next_hand_number = 1
        self._state = TableState(
            table_id=table_id,
            seat_count=SEAT_COUNT,
            status=TableStatus.IDLE,
            seats=[SeatState(seat_index=index) for index in range(SEAT_COUNT)],
            button_seat_index=0,
            current_hand_id=None,
            hand_context=None,
        )
        return self.get_table_snapshot()

    def seat_player(
        self,
        seat_index: int,
        *args: object,
        player_id: str | None = None,
        player_name: str | None = None,
        controller_type: ControllerType | str = ControllerType.HUMAN,
        starting_stack: int | None = None,
        stack: int | None = None,
    ) -> TableSnapshot:
        state = self._require_state()
        if state.status is not TableStatus.IDLE:
            raise TableStateConflictError(
                "players can only be seated while the table is idle",
                details={"status": state.status.value},
            )

        parsed = _parse_seat_player_arguments(
            args,
            player_id=player_id,
            player_name=player_name,
            controller_type=controller_type,
            starting_stack=starting_stack,
            stack=stack,
            default_stack=self.default_starting_stack,
        )
        seat = self._seat(seat_index)
        if seat.player_id is not None:
            raise SeatOccupiedError(
                f"seat {seat_index} is occupied",
                details={"seat_index": seat_index, "player_id": seat.player_id},
            )
        existing_seat = self._find_player_seat(parsed.player_id)
        if existing_seat is not None:
            raise PlayerAlreadySeatedError(
                f"player {parsed.player_id} is already seated",
                details={"player_id": parsed.player_id, "seat_index": existing_seat.seat_index},
            )

        seat.player_id = parsed.player_id
        seat.player_name = parsed.player_name
        seat.controller_type = parsed.controller_type
        seat.stack = parsed.starting_stack
        seat.status = SeatStatus.SEATED
        return self.get_table_snapshot()

    def start_table(self, table_id: str | None = None) -> TableSnapshot:
        state = self._require_state(table_id)
        if state.status is not TableStatus.IDLE:
            raise TableStateConflictError(
                "table can only start from idle",
                details={"status": state.status.value},
            )
        active_count = len(self._eligible_seat_indexes())
        if active_count < self.minimum_active_players:
            raise TableStateConflictError(
                "not enough active players to start the table",
                details={
                    "active_players": active_count,
                    "minimum_active_players": self.minimum_active_players,
                },
            )
        state.status = TableStatus.RUNNING
        return self.get_table_snapshot()

    def pause_table(self, table_id: str | None = None) -> TableSnapshot:
        state = self._require_state(table_id)
        if state.status is not TableStatus.RUNNING:
            raise TableStateConflictError(
                "only a running table can be paused",
                details={"status": state.status.value},
            )
        state.status = TableStatus.PAUSED
        return self.get_table_snapshot()

    def resume_table(self, table_id: str | None = None) -> TableSnapshot:
        state = self._require_state(table_id)
        if state.status is not TableStatus.PAUSED:
            raise TableStateConflictError(
                "only a paused table can be resumed",
                details={"status": state.status.value},
            )
        state.status = TableStatus.RUNNING
        return self.get_table_snapshot()

    def reset_table(self, table_id: str | None = None) -> TableSnapshot:
        state = self._require_state(table_id)
        state.status = TableStatus.RESETTING
        state.seats = [SeatState(seat_index=index) for index in range(SEAT_COUNT)]
        state.button_seat_index = 0
        state.current_hand_id = None
        state.hand_context = None
        state.status = TableStatus.IDLE
        self._next_hand_number = 1
        return self.get_table_snapshot()

    def create_next_hand(self, table_id: str | None = None) -> HandContext:
        state = self._require_state(table_id)
        if state.status is not TableStatus.RUNNING:
            raise TableStateConflictError(
                "new hands can only be created while the table is running",
                details={"status": state.status.value},
            )
        if state.hand_context is not None or state.current_hand_id is not None:
            raise TableStateConflictError(
                "a hand is already active",
                details={"current_hand_id": state.current_hand_id},
            )

        active_seats = self._eligible_seat_indexes()
        if len(active_seats) < self.minimum_active_players:
            raise TableStateConflictError(
                "not enough active players to create a hand",
                details={
                    "active_players": len(active_seats),
                    "minimum_active_players": self.minimum_active_players,
                },
            )
        button_seat_index = _button_for_new_hand(state.button_seat_index, active_seats)
        hand_id = self._new_hand_id()
        starting_stacks = {seat_index: self._seat(seat_index).stack for seat_index in active_seats}
        seat_to_player = {
            seat_index: _known_player_id(self._seat(seat_index).player_id)
            for seat_index in active_seats
        }
        request = CreateHandRequest(
            hand_id=hand_id,
            seat_to_player=seat_to_player,
            starting_stacks=starting_stacks,
            button_seat_index=button_seat_index,
            small_blind=self.small_blind,
            big_blind=self.big_blind,
            ante=self.ante,
        )
        if self.adapter is None:
            raise AdapterUnavailableError("hand adapter is not configured")
        adapter_hand_ref = self.adapter.create_hand(request)

        context = HandContext(
            hand_id=hand_id,
            button_seat_index=button_seat_index,
            active_seat_indexes=tuple(active_seats),
            starting_stacks=starting_stacks,
            adapter_hand_ref=adapter_hand_ref,
        )
        state.button_seat_index = button_seat_index
        state.current_hand_id = hand_id
        state.hand_context = context
        for seat_index in active_seats:
            self._seat(seat_index).status = SeatStatus.IN_HAND
        self._next_hand_number += 1
        return context

    def apply_hand_settlement(
        self,
        settlement: HandSettlement | Mapping[str, object] | object,
        table_id: str | None = None,
    ) -> TableSnapshot:
        state = self._require_state(table_id)
        context = state.hand_context
        if context is None or state.current_hand_id is None:
            raise NoCurrentHandError("there is no current hand to settle")

        parsed = _coerce_settlement(settlement)
        if parsed.hand_id != context.hand_id:
            raise HandSettlementMismatchError(
                "settlement does not match the current hand",
                details={
                    "current_hand_id": context.hand_id,
                    "settlement_hand_id": parsed.hand_id,
                },
            )

        expected_seats = set(context.active_seat_indexes)
        actual_seats = set(parsed.final_stacks)
        if actual_seats != expected_seats:
            raise HandSettlementMismatchError(
                "settlement final stacks must match active seats",
                details={
                    "active_seat_indexes": sorted(expected_seats),
                    "settlement_seat_indexes": sorted(actual_seats),
                },
            )

        final_stacks = {
            seat_index: _validate_non_negative_int(stack, f"final_stacks[{seat_index}]")
            for seat_index, stack in parsed.final_stacks.items()
        }

        for seat_index, final_stack in final_stacks.items():
            seat = self._seat(seat_index)
            seat.stack = final_stack
            seat.status = SeatStatus.SEATED if final_stack > 0 else SeatStatus.SITTING_OUT

        state.current_hand_id = None
        state.hand_context = None
        state.button_seat_index = _next_button_after_settlement(
            context.button_seat_index,
            self._eligible_seat_indexes(),
        )
        return self.get_table_snapshot()

    def get_table_snapshot(self, table_id: str | None = None) -> TableSnapshot:
        state = self._require_state(table_id)
        current_hand = state.hand_context.to_snapshot() if state.hand_context is not None else None
        return TableSnapshot(
            table_id=state.table_id,
            status=state.status,
            seat_count=state.seat_count,
            seats=tuple(seat.to_snapshot() for seat in state.seats),
            button_seat_index=state.button_seat_index,
            current_hand_id=state.current_hand_id,
            current_hand=current_hand,
        )

    def get_table(self, table_id: str | None = None) -> TableSnapshot:
        return self.get_table_snapshot(table_id)

    def _seat(self, seat_index: int) -> SeatState:
        state = self._require_state()
        validated_index = _validate_seat_index(seat_index)
        return state.seats[validated_index]

    def _find_player_seat(self, player_id: str) -> SeatState | None:
        state = self._require_state()
        for seat in state.seats:
            if seat.player_id == player_id:
                return seat
        return None

    def _eligible_seat_indexes(self) -> list[int]:
        state = self._require_state()
        return [
            seat.seat_index for seat in state.seats if seat.player_id is not None and seat.stack > 0
        ]

    def _new_hand_id(self) -> str:
        return f"hand-{self._next_hand_number}"

    def _require_state(self, table_id: str | None = None) -> TableState:
        if self._state is None:
            raise TableNotInitializedError("table has not been initialized")
        if table_id is not None and table_id != self._state.table_id:
            raise TableNotInitializedError(
                f"table {table_id!r} is not initialized",
                details={"table_id": table_id, "current_table_id": self._state.table_id},
            )
        return self._state


@dataclass(frozen=True, slots=True)
class _ParsedSeatPlayer:
    player_id: str
    player_name: str
    controller_type: ControllerType
    starting_stack: int


def _parse_seat_player_arguments(
    args: tuple[object, ...],
    *,
    player_id: str | None,
    player_name: str | None,
    controller_type: ControllerType | str,
    starting_stack: int | None,
    stack: int | None,
    default_stack: int,
) -> _ParsedSeatPlayer:
    positional_player_id: object | None = None
    positional_player_name: object | None = None
    positional_controller_type: object | None = None
    positional_stack: object | None = None

    if len(args) == 1:
        positional_player_name = args[0]
    elif len(args) == 2:
        if _looks_like_controller_type(args[1]):
            positional_player_name = args[0]
            positional_controller_type = args[1]
        else:
            positional_player_id = args[0]
            positional_player_name = args[1]
    elif len(args) == 3:
        if _looks_like_controller_type(args[1]):
            positional_player_name = args[0]
            positional_controller_type = args[1]
            positional_stack = args[2]
        else:
            positional_player_id = args[0]
            positional_player_name = args[1]
            positional_controller_type = args[2]
    elif len(args) == 4:
        positional_player_id = args[0]
        positional_player_name = args[1]
        positional_controller_type = args[2]
        positional_stack = args[3]
    elif args:
        raise TypeError("seat_player accepts at most four positional arguments after seat_index")

    resolved_player_name = _required_string(
        _resolve_argument("player_name", player_name, positional_player_name),
        "player_name",
    )
    resolved_player_id = _optional_string(
        _resolve_argument("player_id", player_id, positional_player_id),
        "player_id",
    )
    if resolved_player_id is None:
        resolved_player_id = _derive_player_id(resolved_player_name)

    controller_value = (
        positional_controller_type if positional_controller_type is not None else controller_type
    )
    resolved_controller = _normalize_controller_type(controller_value)
    stack_value = _resolve_stack_argument(starting_stack, stack, positional_stack, default_stack)
    return _ParsedSeatPlayer(
        player_id=resolved_player_id,
        player_name=resolved_player_name,
        controller_type=resolved_controller,
        starting_stack=_validate_positive_int(stack_value, "starting_stack"),
    )


def _resolve_argument(
    name: str, keyword_value: object | None, positional_value: object | None
) -> object:
    if positional_value is None:
        return keyword_value
    if keyword_value is None:
        return positional_value
    if keyword_value == positional_value:
        return keyword_value
    raise TypeError(f"{name} was provided both positionally and by keyword")


def _resolve_stack_argument(
    starting_stack: object | None,
    stack: object | None,
    positional_stack: object | None,
    default_stack: int,
) -> object:
    values = [value for value in (starting_stack, stack, positional_stack) if value is not None]
    if not values:
        return default_stack
    first = values[0]
    if any(value != first for value in values[1:]):
        raise TypeError("starting_stack and stack values conflict")
    return first


def _looks_like_controller_type(value: object) -> bool:
    if isinstance(value, ControllerType):
        return True
    if not isinstance(value, str):
        return False
    normalized = value.strip().lower().replace("-", "_")
    return normalized in {controller.value for controller in ControllerType}


def _normalize_controller_type(value: object) -> ControllerType:
    if isinstance(value, ControllerType):
        return value
    if not isinstance(value, str):
        raise ValueError("controller_type must be a string")
    normalized = value.strip().lower().replace("-", "_")
    try:
        return ControllerType(normalized)
    except ValueError as exc:
        raise ValueError(f"unsupported controller_type {value!r}") from exc


def _coerce_settlement(
    settlement: HandSettlement | Mapping[str, object] | object,
) -> HandSettlement:
    if isinstance(settlement, HandSettlement):
        return settlement
    if isinstance(settlement, Mapping):
        return HandSettlement.from_mapping(settlement)
    attrs: dict[str, object] = {}
    for field_name in (
        "hand_id",
        "final_stacks",
        "payoffs",
        "winners",
        "final_board",
        "showdown_summary",
        "operations_summary",
    ):
        if hasattr(settlement, field_name):
            attrs[field_name] = getattr(settlement, field_name)
    if not attrs:
        raise TypeError("settlement must be a HandSettlement, mapping, or object with fields")
    return HandSettlement.from_mapping(attrs)


def _normalize_stack_mapping(value: object, name: str) -> dict[int, int]:
    normalized = _normalize_int_mapping(value, name)
    for seat_index, stack in normalized.items():
        normalized[seat_index] = _validate_non_negative_int(stack, f"{name}[{seat_index}]")
    return normalized


def _normalize_int_mapping(value: object, name: str) -> dict[int, int]:
    if not isinstance(value, Mapping):
        raise TypeError(f"{name} must be a mapping")
    normalized: dict[int, int] = {}
    for raw_seat_index, raw_value in value.items():
        seat_index = _coerce_seat_index_key(raw_seat_index, f"{name} key")
        if not isinstance(raw_value, int) or isinstance(raw_value, bool):
            raise InvalidStackError(f"{name}[{seat_index}] must be an integer")
        normalized[seat_index] = raw_value
    return normalized


def _normalize_mapping_sequence(value: object, name: str) -> tuple[Mapping[str, object], ...]:
    if value is None:
        return ()
    if isinstance(value, Mapping | str | bytes) or not isinstance(value, Sequence):
        raise TypeError(f"{name} must be a sequence of mappings")
    items: list[Mapping[str, object]] = []
    for item in value:
        if not isinstance(item, Mapping):
            raise TypeError(f"{name} must contain only mappings")
        items.append(dict(item))
    return tuple(items)


def _normalize_string_sequence(value: object, name: str) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str | bytes) or not isinstance(value, Sequence):
        raise TypeError(f"{name} must be a sequence of strings")
    items: list[str] = []
    for item in value:
        items.append(_required_string(item, name))
    return tuple(items)


def _optional_mapping(value: object, name: str) -> Mapping[str, object] | None:
    if value is None:
        return None
    if not isinstance(value, Mapping):
        raise TypeError(f"{name} must be a mapping when provided")
    return dict(value)


def _derive_player_id(player_name: str) -> str:
    return player_name.strip()


def _known_player_id(player_id: str | None) -> str:
    if player_id is None:
        raise ValueError("active seat is missing player_id")
    return player_id


def _button_for_new_hand(current_button: int, active_seat_indexes: Sequence[int]) -> int:
    if current_button in active_seat_indexes:
        return current_button
    return _next_button_after_settlement(current_button - 1, active_seat_indexes)


def _next_button_after_settlement(current_button: int, eligible_seat_indexes: Sequence[int]) -> int:
    if not eligible_seat_indexes:
        return current_button
    eligible = set(eligible_seat_indexes)
    for offset in range(1, SEAT_COUNT + 1):
        candidate = (current_button + offset) % SEAT_COUNT
        if candidate in eligible:
            return candidate
    return current_button


def _validate_seat_index(value: object) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise SeatNotFoundError("seat_index must be an integer")
    if value < 0 or value >= SEAT_COUNT:
        raise SeatNotFoundError(
            f"seat_index must be between 0 and {SEAT_COUNT - 1}",
            details={"seat_index": value},
        )
    return value


def _coerce_seat_index_key(value: object, name: str) -> int:
    if isinstance(value, str):
        try:
            value = int(value)
        except ValueError as exc:
            raise SeatNotFoundError(f"{name} must be a seat index") from exc
    return _validate_seat_index(value)


def _validate_positive_int(value: object, name: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise InvalidStackError(f"{name} must be an integer")
    if value <= 0:
        raise InvalidStackError(f"{name} must be positive")
    return value


def _validate_non_negative_int(value: object, name: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise InvalidStackError(f"{name} must be an integer")
    if value < 0:
        raise InvalidStackError(f"{name} cannot be negative")
    return value


def _required_string(value: object, name: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{name} must be a string")
    stripped = value.strip()
    if not stripped:
        raise ValueError(f"{name} must be a non-empty string")
    return stripped


def _optional_string(value: object, name: str) -> str | None:
    if value is None:
        return None
    return _required_string(value, name)


__all__ = [
    "AdapterUnavailableError",
    "ControllerType",
    "CreateHandRequest",
    "DEFAULT_ANTE",
    "DEFAULT_BIG_BLIND",
    "DEFAULT_MIN_ACTIVE_PLAYERS",
    "DEFAULT_SMALL_BLIND",
    "DEFAULT_STARTING_STACK",
    "HandAdapter",
    "HandContext",
    "HandSettlement",
    "HandSettlementMismatchError",
    "HandSnapshot",
    "InvalidStackError",
    "NoCurrentHandError",
    "PlayerAlreadySeatedError",
    "SEAT_COUNT",
    "SeatNotFoundError",
    "SeatOccupiedError",
    "SeatSnapshot",
    "SeatState",
    "SeatStatus",
    "TableManager",
    "TableManagerError",
    "TableNotInitializedError",
    "TableSnapshot",
    "TableState",
    "TableStateConflictError",
    "TableStatus",
]
