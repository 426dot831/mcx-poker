"""Platform action validation before adapter submission."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any, Literal, Protocol, TypeAlias

from mcx_poker.engine.actions import (
    ActionError,
    ActionType,
    LegalActionSet,
    PlayerAction,
)

Identifier: TypeAlias = str | int
ValidationSource: TypeAlias = Literal["platform"]

ERROR_MESSAGES = {
    "hand_mismatch": "Action hand does not match the current hand.",
    "turn_mismatch": "Action turn does not match the current turn.",
    "player_not_seated": "Player is not seated at the submitted seat.",
    "not_current_actor": "Action was not submitted by the current actor.",
    "action_not_available": "Action is not available for the current actor.",
    "amount_required": "RaiseTo requires a positive integer amount.",
    "amount_not_allowed": "Only RaiseTo may include an amount.",
    "amount_out_of_range": "RaiseTo amount is outside the legal range.",
}


class PlayerActionLike(Protocol):
    """Duck-typed player action accepted by the validator."""

    player_id: Identifier
    seat_index: int
    hand_id: Identifier
    turn_id: Identifier
    action_type: ActionType | str
    amount: int | None


class TableSnapshot(Protocol):
    """Minimal table snapshot surface used to resolve seats."""

    seat_to_player: Mapping[int, Identifier]


@dataclass(frozen=True, slots=True)
class ActionContext:
    """Current server-owned action opportunity."""

    table_id: Identifier
    hand_id: Identifier
    turn_id: Identifier
    actor_player_id: Identifier
    actor_seat_index: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "table_id", _validate_identifier(self.table_id, "table_id"))
        object.__setattr__(self, "hand_id", _validate_identifier(self.hand_id, "hand_id"))
        object.__setattr__(self, "turn_id", _validate_identifier(self.turn_id, "turn_id"))
        object.__setattr__(
            self,
            "actor_player_id",
            _validate_identifier(self.actor_player_id, "actor_player_id"),
        )
        object.__setattr__(
            self,
            "actor_seat_index",
            _validate_seat_index(self.actor_seat_index),
        )


@dataclass(frozen=True, slots=True)
class ValidatedAction:
    """Action accepted by the platform validator."""

    action: PlayerAction | PlayerActionLike | Mapping[str, Any]
    normalized_type: ActionType
    normalized_amount: int | None
    validation_source: ValidationSource = "platform"


ActionValidationResult: TypeAlias = ValidatedAction | ActionError


def validate_action(
    action: PlayerAction | PlayerActionLike | Mapping[str, Any],
    context: ActionContext,
    legal_actions: LegalActionSet | Iterable[Any] | Mapping[str, Any] | Any,
    table_snapshot: TableSnapshot | Mapping[str, Any] | Any,
) -> ActionValidationResult:
    """Validate a submitted action without mutating state or calling the adapter."""

    player_id = _read_field(action, "player_id")
    seat_index = _read_field(action, "seat_index")
    hand_id = _read_field(action, "hand_id")
    turn_id = _read_field(action, "turn_id")
    raw_action_type = _read_field(action, "action_type")
    amount = _read_field(action, "amount", None)

    if hand_id != context.hand_id:
        return _action_error("hand_mismatch", action)

    if turn_id != context.turn_id:
        return _action_error("turn_mismatch", action)

    if not _is_non_bool_int(seat_index) or _seated_player(table_snapshot, seat_index) != player_id:
        return _action_error("player_not_seated", action)

    if seat_index != context.actor_seat_index or player_id != context.actor_player_id:
        return _action_error("not_current_actor", action)

    action_type = _normalize_action_type(raw_action_type)
    if action_type is None:
        return _action_error("action_not_available", action)

    legal_action = _find_legal_action(legal_actions, action_type)
    if legal_action is None or not _legal_action_enabled(legal_action):
        return _action_error("action_not_available", action)

    if action_type is ActionType.RAISE_TO:
        if amount is None:
            return _action_error("amount_required", action)
        if not _is_non_bool_int(amount) or amount <= 0:
            return _action_error("amount_out_of_range", action)
        amount_min = _optional_int(_read_field(legal_action, "amount_min", None))
        amount_max = _optional_int(_read_field(legal_action, "amount_max", None))
        if amount_min is not None and amount < amount_min:
            return _action_error("amount_out_of_range", action)
        if amount_max is not None and amount > amount_max:
            return _action_error("amount_out_of_range", action)
        return ValidatedAction(
            action=action,
            normalized_type=action_type,
            normalized_amount=amount,
        )

    if amount is not None:
        return _action_error("amount_not_allowed", action)

    if not _check_call_amount_semantics(action_type, legal_action):
        return _action_error("action_not_available", action)

    return ValidatedAction(
        action=action,
        normalized_type=action_type,
        normalized_amount=None,
    )


def adapter_error_to_action_error(
    adapter_error: BaseException | Mapping[str, Any] | Any,
    action: PlayerAction | PlayerActionLike | Mapping[str, Any] | None = None,
) -> ActionError:
    """Convert an adapter action rejection into the same ActionError shape."""

    error_payload = _error_payload(adapter_error)
    code = _read_field(error_payload, "code", None)
    message = _read_field(error_payload, "message", None)

    if not isinstance(code, str) or not code:
        code = "adapter_action_error"
    if not isinstance(message, str) or not message:
        message = "Adapter rejected the submitted action."

    return ActionError(
        code=code,
        message=message,
        player_id=_error_identifier(error_payload, action, "player_id"),
        hand_id=_error_identifier(error_payload, action, "hand_id"),
        turn_id=_error_identifier(error_payload, action, "turn_id"),
        retry_same_player=True,
    )


action_error_from_adapter_error = adapter_error_to_action_error


def _action_error(
    code: str,
    action: PlayerAction | PlayerActionLike | Mapping[str, Any],
) -> ActionError:
    return ActionError(
        code=code,
        message=ERROR_MESSAGES[code],
        player_id=_optional_identifier(_read_field(action, "player_id", None)),
        hand_id=_optional_identifier(_read_field(action, "hand_id", None)),
        turn_id=_optional_identifier(_read_field(action, "turn_id", None)),
        retry_same_player=True,
    )


def _find_legal_action(legal_actions: Any, action_type: ActionType) -> Any | None:
    if isinstance(legal_actions, LegalActionSet):
        return legal_actions.get(action_type)

    boundary = _boundary_action(legal_actions, action_type)
    if boundary is not None:
        return boundary

    for candidate in _iter_legal_actions(legal_actions):
        candidate_type = _normalize_action_type(_read_field(candidate, "action_type", None))
        if candidate_type is action_type:
            return candidate
    return None


def _boundary_action(legal_actions: Any, action_type: ActionType) -> Any | None:
    attr_by_type = {
        ActionType.FOLD: "fold",
        ActionType.CHECK: "check",
        ActionType.CALL: "call",
        ActionType.RAISE_TO: "raise_to",
        ActionType.ALL_IN: "all_in",
    }
    attr = attr_by_type[action_type]

    if isinstance(legal_actions, Mapping):
        if attr in legal_actions:
            return legal_actions[attr]
        if action_type.value in legal_actions:
            return legal_actions[action_type.value]
        if action_type.name in legal_actions:
            return legal_actions[action_type.name]
        return None

    return getattr(legal_actions, attr, None)


def _iter_legal_actions(legal_actions: Any) -> Iterable[Any]:
    if isinstance(legal_actions, Mapping):
        actions = legal_actions.get("actions")
        if actions is not None and not isinstance(actions, str | bytes):
            return tuple(actions)
        return ()

    actions_attr = getattr(legal_actions, "actions", None)
    if actions_attr is not None and not isinstance(actions_attr, str | bytes):
        return tuple(actions_attr)

    if isinstance(legal_actions, str | bytes):
        return ()

    try:
        return tuple(legal_actions)
    except TypeError:
        return ()


def _legal_action_enabled(legal_action: Any) -> bool:
    enabled = _read_field(legal_action, "enabled", True)
    return enabled is True


def _check_call_amount_semantics(action_type: ActionType, legal_action: Any) -> bool:
    fixed = _read_field(legal_action, "amount_fixed", None)
    if fixed is None:
        return True
    if not _is_non_bool_int(fixed):
        return False
    if action_type is ActionType.CHECK:
        return fixed == 0
    if action_type is ActionType.CALL:
        return fixed > 0
    return True


def _seated_player(table_snapshot: Any, seat_index: int) -> Identifier | None:
    seat_to_player = _read_field(table_snapshot, "seat_to_player", None)
    if isinstance(seat_to_player, Mapping):
        return _lookup_seat_mapping(seat_to_player, seat_index)

    for mapping_name in ("players_by_seat", "seat_players", "player_by_seat"):
        seat_mapping = _read_field(table_snapshot, mapping_name, None)
        if isinstance(seat_mapping, Mapping):
            return _lookup_seat_mapping(seat_mapping, seat_index)

    seats = _read_field(table_snapshot, "seats", None)
    if seats is None or isinstance(seats, Mapping | str | bytes):
        return None

    for seat in seats:
        if _read_field(seat, "seat_index", None) == seat_index:
            return _optional_identifier(_read_field(seat, "player_id", None))
    return None


def _lookup_seat_mapping(seat_to_player: Mapping[Any, Any], seat_index: int) -> Identifier | None:
    if seat_index in seat_to_player:
        return _optional_identifier(seat_to_player[seat_index])
    string_key = str(seat_index)
    if string_key in seat_to_player:
        return _optional_identifier(seat_to_player[string_key])
    return None


def _normalize_action_type(value: Any) -> ActionType | None:
    if isinstance(value, ActionType):
        return value
    if hasattr(value, "value"):
        value = value.value
    if isinstance(value, str):
        candidate = value.casefold()
        for action_type in ActionType:
            if candidate in {action_type.name.casefold(), action_type.value.casefold()}:
                return action_type
    return None


def _error_payload(adapter_error: BaseException | Mapping[str, Any] | Any) -> Any:
    if isinstance(adapter_error, Mapping):
        return adapter_error

    to_dict = getattr(adapter_error, "to_dict", None)
    if callable(to_dict):
        payload = to_dict()
        if isinstance(payload, Mapping):
            return payload

    return adapter_error


def _error_identifier(
    adapter_error: Any,
    action: PlayerAction | PlayerActionLike | Mapping[str, Any] | None,
    field_name: str,
) -> Identifier | None:
    value = _optional_identifier(_read_field(adapter_error, field_name, None))
    if value is not None or action is None:
        return value
    return _optional_identifier(_read_field(action, field_name, None))


def _read_field(source: Any, field_name: str, default: Any = None) -> Any:
    if isinstance(source, Mapping):
        return source.get(field_name, default)
    return getattr(source, field_name, default)


def _validate_identifier(value: Any, field_name: str) -> Identifier:
    if isinstance(value, bool) or value is None:
        raise ValueError(f"{field_name} must be a string or integer identifier")
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value:
        return value
    raise ValueError(f"{field_name} must be a non-empty string or integer identifier")


def _optional_identifier(value: Any) -> Identifier | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value:
        return value
    return None


def _validate_seat_index(value: Any) -> int:
    if not _is_non_bool_int(value) or value < 0:
        raise ValueError("actor_seat_index must be a non-negative integer")
    return value


def _is_non_bool_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _optional_int(value: Any) -> int | None:
    if _is_non_bool_int(value):
        return value
    return None


__all__ = [
    "ActionContext",
    "ActionValidationResult",
    "PlayerActionLike",
    "TableSnapshot",
    "ValidatedAction",
    "action_error_from_adapter_error",
    "adapter_error_to_action_error",
    "validate_action",
]
