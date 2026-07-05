"""Platform action DTOs for table clients and controllers."""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Self, TypeVar

Identifier = str | int
EnumT = TypeVar("EnumT", bound=StrEnum)


class ActionType(StrEnum):
    """Supported player action types."""

    FOLD = "Fold"
    CHECK = "Check"
    CALL = "Call"
    RAISE_TO = "RaiseTo"
    ALL_IN = "AllIn"


class ActionSource(StrEnum):
    """Diagnostic source marker for submitted actions."""

    HUMAN = "human"
    BOT = "bot"
    FUTURE_AGENT = "future_agent"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class PlayerAction:
    """A submitted player action in platform-native shape."""

    player_id: Identifier
    seat_index: int
    hand_id: Identifier
    turn_id: Identifier
    action_type: ActionType
    amount: int | None = None
    source: ActionSource = ActionSource.UNKNOWN

    def __post_init__(self) -> None:
        action_type = _parse_enum(ActionType, self.action_type, "action_type")
        source = _parse_enum(ActionSource, self.source, "source")
        amount = _validate_optional_amount(self.amount, "amount")

        if action_type is ActionType.RAISE_TO:
            if amount is None:
                raise ValueError("RaiseTo requires amount")
        elif amount is not None:
            raise ValueError(f"{action_type.value} does not accept amount")

        object.__setattr__(self, "player_id", _validate_identifier(self.player_id, "player_id"))
        object.__setattr__(self, "seat_index", _validate_seat_index(self.seat_index))
        object.__setattr__(self, "hand_id", _validate_identifier(self.hand_id, "hand_id"))
        object.__setattr__(self, "turn_id", _validate_identifier(self.turn_id, "turn_id"))
        object.__setattr__(self, "action_type", action_type)
        object.__setattr__(self, "amount", amount)
        object.__setattr__(self, "source", source)

    def to_dict(self) -> dict[str, object]:
        return {
            "player_id": self.player_id,
            "seat_index": self.seat_index,
            "hand_id": self.hand_id,
            "turn_id": self.turn_id,
            "action_type": self.action_type.value,
            "amount": self.amount,
            "source": self.source.value,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> Self:
        _require_mapping(data, "PlayerAction")
        _require_keys(
            data,
            "PlayerAction",
            ("player_id", "seat_index", "hand_id", "turn_id", "action_type"),
        )
        return cls(
            player_id=data["player_id"],
            seat_index=data["seat_index"],
            hand_id=data["hand_id"],
            turn_id=data["turn_id"],
            action_type=data["action_type"],
            amount=data.get("amount"),
            source=data.get("source", ActionSource.UNKNOWN),
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), separators=(",", ":"), sort_keys=True)

    @classmethod
    def from_json(cls, payload: str) -> Self:
        return cls.from_dict(_loads_mapping(payload, "PlayerAction"))


@dataclass(frozen=True, slots=True)
class LegalAction:
    """A platform description of one currently available action."""

    action_type: ActionType
    enabled: bool = True
    amount_min: int | None = None
    amount_max: int | None = None
    amount_fixed: int | None = None
    reason_if_disabled: str | None = None

    def __post_init__(self) -> None:
        action_type = _parse_enum(ActionType, self.action_type, "action_type")
        amount_min = _validate_optional_amount(self.amount_min, "amount_min")
        amount_max = _validate_optional_amount(self.amount_max, "amount_max")
        amount_fixed = _validate_optional_amount(self.amount_fixed, "amount_fixed")

        if not isinstance(self.enabled, bool):
            raise ValueError("enabled must be a bool")
        if amount_min is not None and amount_max is not None and amount_min > amount_max:
            raise ValueError("amount_min cannot be greater than amount_max")
        if self.reason_if_disabled is not None and not isinstance(self.reason_if_disabled, str):
            raise ValueError("reason_if_disabled must be a string or None")

        object.__setattr__(self, "action_type", action_type)
        object.__setattr__(self, "amount_min", amount_min)
        object.__setattr__(self, "amount_max", amount_max)
        object.__setattr__(self, "amount_fixed", amount_fixed)

    def to_dict(self) -> dict[str, object]:
        return {
            "action_type": self.action_type.value,
            "enabled": self.enabled,
            "amount_min": self.amount_min,
            "amount_max": self.amount_max,
            "amount_fixed": self.amount_fixed,
            "reason_if_disabled": self.reason_if_disabled,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> Self:
        _require_mapping(data, "LegalAction")
        _require_keys(data, "LegalAction", ("action_type",))
        return cls(
            action_type=data["action_type"],
            enabled=data.get("enabled", True),
            amount_min=data.get("amount_min"),
            amount_max=data.get("amount_max"),
            amount_fixed=data.get("amount_fixed"),
            reason_if_disabled=data.get("reason_if_disabled"),
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), separators=(",", ":"), sort_keys=True)

    @classmethod
    def from_json(cls, payload: str) -> Self:
        return cls.from_dict(_loads_mapping(payload, "LegalAction"))


@dataclass(frozen=True, slots=True)
class LegalActionSet:
    """Reusable collection of legal action descriptions."""

    actions: tuple[LegalAction, ...]

    def __post_init__(self) -> None:
        if isinstance(self.actions, Mapping | str | bytes) or not isinstance(
            self.actions, Iterable
        ):
            raise ValueError("actions must be an iterable of LegalAction values")

        actions: list[LegalAction] = []
        seen: set[ActionType] = set()
        for action in self.actions:
            if isinstance(action, LegalAction):
                legal_action = action
            elif isinstance(action, Mapping):
                legal_action = LegalAction.from_dict(action)
            else:
                raise ValueError("actions must contain LegalAction values or dictionaries")

            if legal_action.action_type in seen:
                raise ValueError(f"duplicate legal action type: {legal_action.action_type.value}")
            seen.add(legal_action.action_type)
            actions.append(legal_action)

        object.__setattr__(self, "actions", tuple(actions))

    def __iter__(self) -> Iterable[LegalAction]:
        return iter(self.actions)

    def __len__(self) -> int:
        return len(self.actions)

    def get(self, action_type: ActionType | str) -> LegalAction | None:
        parsed_type = _parse_enum(ActionType, action_type, "action_type")
        return next((action for action in self.actions if action.action_type is parsed_type), None)

    def enabled_actions(self) -> tuple[LegalAction, ...]:
        return tuple(action for action in self.actions if action.enabled)

    def to_dict(self) -> dict[str, object]:
        return {"actions": [action.to_dict() for action in self.actions]}

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> Self:
        _require_mapping(data, "LegalActionSet")
        _require_keys(data, "LegalActionSet", ("actions",))
        return cls(tuple(data["actions"]))

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), separators=(",", ":"), sort_keys=True)

    @classmethod
    def from_json(cls, payload: str) -> Self:
        return cls.from_dict(_loads_mapping(payload, "LegalActionSet"))


@dataclass(frozen=True, slots=True)
class ActionError:
    """Platform error returned for rejected actions."""

    code: str
    message: str
    player_id: Identifier | None = None
    hand_id: Identifier | None = None
    turn_id: Identifier | None = None
    retry_same_player: bool = True

    def __post_init__(self) -> None:
        if not isinstance(self.code, str) or not self.code:
            raise ValueError("code must be a non-empty string")
        if not isinstance(self.message, str) or not self.message:
            raise ValueError("message must be a non-empty string")
        if not isinstance(self.retry_same_player, bool):
            raise ValueError("retry_same_player must be a bool")

        object.__setattr__(
            self,
            "player_id",
            _validate_optional_identifier(self.player_id, "player_id"),
        )
        object.__setattr__(self, "hand_id", _validate_optional_identifier(self.hand_id, "hand_id"))
        object.__setattr__(self, "turn_id", _validate_optional_identifier(self.turn_id, "turn_id"))

    def to_dict(self) -> dict[str, object]:
        return {
            "code": self.code,
            "message": self.message,
            "player_id": self.player_id,
            "hand_id": self.hand_id,
            "turn_id": self.turn_id,
            "retry_same_player": self.retry_same_player,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> Self:
        _require_mapping(data, "ActionError")
        _require_keys(data, "ActionError", ("code", "message"))
        return cls(
            code=data["code"],
            message=data["message"],
            player_id=data.get("player_id"),
            hand_id=data.get("hand_id"),
            turn_id=data.get("turn_id"),
            retry_same_player=data.get("retry_same_player", True),
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), separators=(",", ":"), sort_keys=True)

    @classmethod
    def from_json(cls, payload: str) -> Self:
        return cls.from_dict(_loads_mapping(payload, "ActionError"))


def _parse_enum(enum_type: type[EnumT], value: object, field_name: str) -> EnumT:
    if isinstance(value, enum_type):
        return value
    if isinstance(value, str):
        candidate = value.casefold()
        for enum_value in enum_type:
            if candidate in {enum_value.name.casefold(), str(enum_value.value).casefold()}:
                return enum_value
    valid_values = ", ".join(str(enum_value.value) for enum_value in enum_type)
    raise ValueError(f"{field_name} must be one of: {valid_values}")


def _validate_identifier(value: object, field_name: str) -> Identifier:
    if isinstance(value, bool) or value is None:
        raise ValueError(f"{field_name} must be a string or integer identifier")
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value:
        return value
    raise ValueError(f"{field_name} must be a non-empty string or integer identifier")


def _validate_optional_identifier(value: object, field_name: str) -> Identifier | None:
    if value is None:
        return None
    return _validate_identifier(value, field_name)


def _validate_seat_index(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError("seat_index must be a non-negative integer")
    return value


def _validate_optional_amount(value: object, field_name: str) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{field_name} must be an integer chip amount")
    if value < 0:
        raise ValueError(f"{field_name} must be non-negative")
    return value


def _require_mapping(data: object, model_name: str) -> None:
    if not isinstance(data, Mapping):
        raise ValueError(f"{model_name} payload must be a dictionary")


def _require_keys(data: Mapping[str, Any], model_name: str, keys: tuple[str, ...]) -> None:
    missing = [key for key in keys if key not in data]
    if missing:
        missing_list = ", ".join(missing)
        raise ValueError(f"{model_name} payload missing required field(s): {missing_list}")


def _loads_mapping(payload: str, model_name: str) -> Mapping[str, Any]:
    loaded = json.loads(payload)
    _require_mapping(loaded, model_name)
    return loaded


__all__ = [
    "ActionError",
    "ActionSource",
    "ActionType",
    "LegalAction",
    "LegalActionSet",
    "PlayerAction",
]
