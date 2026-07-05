"""Temporary in-memory hand event log.

The log intentionally stores only JSON-compatible payloads.  That keeps the
events easy to broadcast, inspect, and later persist without leaking PokerKit
runtime objects or private card state through public reads.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field, replace
from datetime import UTC, datetime
from enum import StrEnum
from math import isfinite
from typing import TypeAlias

JSONValue: TypeAlias = str | int | float | bool | None | list["JSONValue"] | dict[str, "JSONValue"]


class EventType(StrEnum):
    """Supported temporary hand event types."""

    HAND_STARTED = "hand_started"
    SEAT_SNAPSHOT = "seat_snapshot"
    HOLE_CARDS_DEALT = "hole_cards_dealt"
    BOARD_DEALT = "board_dealt"
    ACTION_SUCCEEDED = "action_succeeded"
    ACTION_REJECTED = "action_rejected"
    POT_UPDATED = "pot_updated"
    SHOWDOWN = "showdown"
    SETTLEMENT = "settlement"
    HAND_ENDED = "hand_ended"


class EventVisibility(StrEnum):
    """Visibility rules for an event."""

    PUBLIC = "public"
    PLAYER_SCOPED = "player_scoped"


_PLAYER_SCOPED_ONLY_EVENT_TYPES = frozenset({EventType.HOLE_CARDS_DEALT})
_ALWAYS_SENSITIVE_PUBLIC_KEYS = frozenset(
    {
        "deck",
        "deck_order",
        "remaining_deck",
        "stub",
        "undealt_cards",
    }
)
_PRIVATE_CARD_PUBLIC_KEYS = frozenset({"hole_cards", "private_cards", "pocket_cards"})


@dataclass(frozen=True, slots=True)
class HandEvent:
    """A single temporary event emitted during a hand.

    ``target_player_id`` is intentionally optional and additive: the MVP fields
    use ``actor_player_id`` as the private recipient when no explicit target is
    supplied, while future event types can target a player who is not the actor.
    """

    hand_id: str
    event_type: EventType | str
    sequence_number: int = 0
    actor_player_id: str | None = None
    actor_seat_index: int | None = None
    public_payload: JSONValue | None = None
    private_payload: JSONValue | None = None
    visibility: EventVisibility | str = EventVisibility.PUBLIC
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    target_player_id: str | None = None

    def __post_init__(self) -> None:
        event_type = _coerce_event_type(self.event_type)
        visibility = _coerce_visibility(self.visibility)
        public_payload = _normalize_payload(self.public_payload, path="public_payload")
        private_payload = _normalize_payload(self.private_payload, path="private_payload")

        object.__setattr__(self, "event_type", event_type)
        object.__setattr__(self, "visibility", visibility)
        object.__setattr__(self, "public_payload", public_payload)
        object.__setattr__(self, "private_payload", private_payload)

        _validate_non_empty_string(self.hand_id, "hand_id")
        _validate_optional_non_empty_string(self.actor_player_id, "actor_player_id")
        _validate_optional_non_empty_string(self.target_player_id, "target_player_id")

        if not isinstance(self.sequence_number, int) or isinstance(self.sequence_number, bool):
            raise TypeError("sequence_number must be an integer")
        if self.sequence_number < 0:
            raise ValueError("sequence_number cannot be negative")

        if self.actor_seat_index is not None:
            if not isinstance(self.actor_seat_index, int) or isinstance(
                self.actor_seat_index,
                bool,
            ):
                raise TypeError("actor_seat_index must be an integer when provided")
            if self.actor_seat_index < 0:
                raise ValueError("actor_seat_index cannot be negative")

        if self.created_at.tzinfo is None:
            object.__setattr__(self, "created_at", self.created_at.replace(tzinfo=UTC))

        if (
            event_type in _PLAYER_SCOPED_ONLY_EVENT_TYPES
            and visibility != EventVisibility.PLAYER_SCOPED
        ):
            raise ValueError(f"{event_type.value} events must be player-scoped")

        if visibility == EventVisibility.PUBLIC:
            if private_payload is not None:
                raise ValueError("public events cannot contain private_payload")
            if self.target_player_id is not None:
                raise ValueError("public events cannot target a private player")
            sensitive_path = _find_sensitive_public_key(
                public_payload,
                allow_private_card_keys=event_type == EventType.SHOWDOWN,
            )
            if sensitive_path is not None:
                raise ValueError(
                    f"public_payload cannot contain private or deck key {sensitive_path!r}"
                )
            return

        target_player_id = self.target_player_id or self.actor_player_id
        if target_player_id is None:
            raise ValueError("player-scoped events require actor_player_id or target_player_id")
        object.__setattr__(self, "target_player_id", target_player_id)

    def to_dict(self, *, include_private: bool = True) -> dict[str, JSONValue]:
        """Return a JSON-compatible representation of the event."""

        event_dict: dict[str, JSONValue] = {
            "hand_id": self.hand_id,
            "sequence_number": self.sequence_number,
            "event_type": _coerce_event_type(self.event_type).value,
            "actor_player_id": self.actor_player_id,
            "actor_seat_index": self.actor_seat_index,
            "public_payload": self.public_payload,
            "visibility": _coerce_visibility(self.visibility).value,
            "created_at": self.created_at.isoformat(),
            "target_player_id": self.target_player_id,
        }
        if include_private:
            event_dict["private_payload"] = self.private_payload
        return event_dict

    @classmethod
    def from_dict(cls, event_dict: Mapping[str, object]) -> HandEvent:
        """Rebuild an event from ``to_dict`` output."""

        created_at = event_dict.get("created_at")
        if isinstance(created_at, str):
            parsed_created_at = datetime.fromisoformat(created_at)
        elif isinstance(created_at, datetime):
            parsed_created_at = created_at
        elif created_at is None:
            parsed_created_at = datetime.now(UTC)
        else:
            raise TypeError("created_at must be an ISO datetime string when provided")

        sequence_number = _optional_int(event_dict, "sequence_number", default=0)
        if sequence_number is None:
            sequence_number = 0

        return cls(
            hand_id=_required_string(event_dict, "hand_id"),
            sequence_number=sequence_number,
            event_type=_required_string(event_dict, "event_type"),
            actor_player_id=_optional_string(event_dict, "actor_player_id"),
            actor_seat_index=_optional_int(event_dict, "actor_seat_index", default=None),
            public_payload=_optional_payload(event_dict, "public_payload"),
            private_payload=_optional_payload(event_dict, "private_payload"),
            visibility=_optional_string(event_dict, "visibility") or EventVisibility.PUBLIC,
            created_at=parsed_created_at,
            target_player_id=_optional_string(event_dict, "target_player_id"),
        )


class HandEventLog:
    """In-memory event log scoped to current process lifetime."""

    def __init__(self, *, max_retained_hands: int = 2) -> None:
        if not isinstance(max_retained_hands, int) or isinstance(max_retained_hands, bool):
            raise TypeError("max_retained_hands must be an integer")
        if max_retained_hands < 1:
            raise ValueError("max_retained_hands must be at least 1")
        self._max_retained_hands = max_retained_hands
        self._events_by_hand: dict[str, list[HandEvent]] = {}
        self._last_sequences: dict[str, int] = {}
        self._hand_order: list[str] = []

    def append(self, event: HandEvent) -> HandEvent:
        """Append an event and assign the next sequence number for its hand."""

        if not isinstance(event, HandEvent):
            raise TypeError("append expects a HandEvent")

        self._ensure_hand_tracked(event.hand_id)
        next_sequence = self._last_sequences.get(event.hand_id, 0) + 1
        stored_event = replace(event, sequence_number=next_sequence)

        self._events_by_hand.setdefault(event.hand_id, []).append(stored_event)
        self._last_sequences[event.hand_id] = next_sequence
        return stored_event

    def list_public_events(self, hand_id: str) -> list[HandEvent]:
        """Return events visible to every observer."""

        return [
            event
            for event in self._events_by_hand.get(hand_id, [])
            if event.visibility == EventVisibility.PUBLIC
        ]

    def list_player_events(self, hand_id: str, player_id: str) -> list[HandEvent]:
        """Return public events plus private events scoped to ``player_id``."""

        _validate_non_empty_string(player_id, "player_id")
        return [
            event
            for event in self._events_by_hand.get(hand_id, [])
            if event.visibility == EventVisibility.PUBLIC or event.target_player_id == player_id
        ]

    def list_successful_actions(self, hand_id: str) -> list[HandEvent]:
        """Return only successful public action events."""

        return [
            event
            for event in self.list_public_events(hand_id)
            if event.event_type == EventType.ACTION_SUCCEEDED
        ]

    def clear_hand(self, hand_id: str) -> None:
        """Remove all retained events and sequence state for a hand."""

        self._events_by_hand.pop(hand_id, None)
        self._last_sequences.pop(hand_id, None)
        self._hand_order = [
            retained_hand_id for retained_hand_id in self._hand_order if retained_hand_id != hand_id
        ]

    def get_last_sequence(self, hand_id: str) -> int:
        """Return the last assigned sequence number for ``hand_id``."""

        return self._last_sequences.get(hand_id, 0)

    def record_hand_started(
        self,
        hand_id: str,
        payload: Mapping[str, object] | None = None,
    ) -> HandEvent:
        return self.append(
            HandEvent(
                hand_id=hand_id,
                event_type=EventType.HAND_STARTED,
                public_payload=_payload_mapping(payload),
            )
        )

    def record_seat_snapshot(
        self,
        hand_id: str,
        seats: object,
        *,
        payload: Mapping[str, object] | None = None,
    ) -> HandEvent:
        event_payload = _payload_mapping(payload)
        event_payload["seats"] = _normalize_payload(seats, path="seats")
        return self.append(
            HandEvent(
                hand_id=hand_id,
                event_type=EventType.SEAT_SNAPSHOT,
                public_payload=event_payload,
            )
        )

    def record_hole_cards_dealt(
        self,
        hand_id: str,
        player_id: str,
        cards: object,
        *,
        seat_index: int | None = None,
        payload: Mapping[str, object] | None = None,
    ) -> HandEvent:
        private_payload = _payload_mapping(payload)
        private_payload["cards"] = _normalize_payload(cards, path="cards")
        return self.append(
            HandEvent(
                hand_id=hand_id,
                event_type=EventType.HOLE_CARDS_DEALT,
                actor_player_id=player_id,
                actor_seat_index=seat_index,
                private_payload=private_payload,
                visibility=EventVisibility.PLAYER_SCOPED,
            )
        )

    def record_board_dealt(
        self,
        hand_id: str,
        cards: object,
        *,
        street: str | None = None,
        board: object | None = None,
        payload: Mapping[str, object] | None = None,
    ) -> HandEvent:
        event_payload = _payload_mapping(payload)
        event_payload["cards"] = _normalize_payload(cards, path="cards")
        if street is not None:
            event_payload["street"] = street
        if board is not None:
            event_payload["board"] = _normalize_payload(board, path="board")
        return self.append(
            HandEvent(
                hand_id=hand_id,
                event_type=EventType.BOARD_DEALT,
                public_payload=event_payload,
            )
        )

    def record_action_succeeded(
        self,
        hand_id: str,
        player_id: str,
        action: str,
        *,
        amount: int | float | None = None,
        seat_index: int | None = None,
        payload: Mapping[str, object] | None = None,
    ) -> HandEvent:
        event_payload = _payload_mapping(payload)
        event_payload["action"] = action
        if amount is not None:
            event_payload["amount"] = amount
        return self.append(
            HandEvent(
                hand_id=hand_id,
                event_type=EventType.ACTION_SUCCEEDED,
                actor_player_id=player_id,
                actor_seat_index=seat_index,
                public_payload=event_payload,
            )
        )

    def record_action_rejected(
        self,
        hand_id: str,
        player_id: str,
        reason: str,
        *,
        attempted_action: str | None = None,
        seat_index: int | None = None,
        payload: Mapping[str, object] | None = None,
    ) -> HandEvent:
        private_payload = _payload_mapping(payload)
        private_payload["reason"] = reason
        if attempted_action is not None:
            private_payload["attempted_action"] = attempted_action
        return self.append(
            HandEvent(
                hand_id=hand_id,
                event_type=EventType.ACTION_REJECTED,
                actor_player_id=player_id,
                actor_seat_index=seat_index,
                private_payload=private_payload,
                visibility=EventVisibility.PLAYER_SCOPED,
            )
        )

    def record_pot_updated(
        self,
        hand_id: str,
        summary: Mapping[str, object] | None = None,
    ) -> HandEvent:
        return self.append(
            HandEvent(
                hand_id=hand_id,
                event_type=EventType.POT_UPDATED,
                public_payload=_payload_mapping(summary),
            )
        )

    def record_betting_summary(
        self,
        hand_id: str,
        summary: Mapping[str, object] | None = None,
    ) -> HandEvent:
        return self.record_pot_updated(hand_id, summary)

    def record_showdown(
        self,
        hand_id: str,
        revealed: Mapping[str, object] | None = None,
    ) -> HandEvent:
        return self.append(
            HandEvent(
                hand_id=hand_id,
                event_type=EventType.SHOWDOWN,
                public_payload=_payload_mapping(revealed),
            )
        )

    def record_settlement(
        self,
        hand_id: str,
        settlement: Mapping[str, object] | None = None,
    ) -> HandEvent:
        return self.append(
            HandEvent(
                hand_id=hand_id,
                event_type=EventType.SETTLEMENT,
                public_payload=_payload_mapping(settlement),
            )
        )

    def record_hand_ended(
        self,
        hand_id: str,
        payload: Mapping[str, object] | None = None,
    ) -> HandEvent:
        return self.append(
            HandEvent(
                hand_id=hand_id,
                event_type=EventType.HAND_ENDED,
                public_payload=_payload_mapping(payload),
            )
        )

    def _ensure_hand_tracked(self, hand_id: str) -> None:
        _validate_non_empty_string(hand_id, "hand_id")
        if hand_id in self._events_by_hand:
            return

        self._events_by_hand[hand_id] = []
        self._hand_order.append(hand_id)
        while len(self._hand_order) > self._max_retained_hands:
            pruned_hand_id = self._hand_order.pop(0)
            self._events_by_hand.pop(pruned_hand_id, None)
            self._last_sequences.pop(pruned_hand_id, None)


TemporaryHandEventLog = HandEventLog

_default_log = HandEventLog()


def append(event: HandEvent) -> HandEvent:
    return _default_log.append(event)


def list_public_events(hand_id: str) -> list[HandEvent]:
    return _default_log.list_public_events(hand_id)


def list_player_events(hand_id: str, player_id: str) -> list[HandEvent]:
    return _default_log.list_player_events(hand_id, player_id)


def clear_hand(hand_id: str) -> None:
    _default_log.clear_hand(hand_id)


def get_last_sequence(hand_id: str) -> int:
    return _default_log.get_last_sequence(hand_id)


def _coerce_event_type(event_type: EventType | str) -> EventType:
    try:
        return EventType(event_type)
    except ValueError as exc:
        raise ValueError(f"unsupported event_type {event_type!r}") from exc


def _coerce_visibility(visibility: EventVisibility | str) -> EventVisibility:
    if isinstance(visibility, str):
        visibility = visibility.replace("-", "_")
    try:
        return EventVisibility(visibility)
    except ValueError as exc:
        raise ValueError(f"unsupported visibility {visibility!r}") from exc


def _normalize_payload(value: object, *, path: str) -> JSONValue:
    if _is_pokerkit_object(value):
        raise ValueError(f"{path} cannot contain PokerKit objects")
    if value is None or isinstance(value, str):
        return value
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        if not isfinite(value):
            raise ValueError(f"{path} cannot contain non-finite floats")
        return value
    if isinstance(value, Mapping):
        normalized: dict[str, JSONValue] = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise TypeError(f"{path} keys must be strings")
            normalized[key] = _normalize_payload(item, path=f"{path}.{key}")
        return normalized
    if isinstance(value, (list, tuple)):
        return [
            _normalize_payload(item, path=f"{path}[{index}]") for index, item in enumerate(value)
        ]
    raise ValueError(f"{path} must be JSON-compatible and cannot contain runtime objects")


def _payload_mapping(payload: Mapping[str, object] | None) -> dict[str, JSONValue]:
    if payload is None:
        return {}
    normalized = _normalize_payload(payload, path="payload")
    if not isinstance(normalized, dict):
        raise TypeError("payload must be a mapping")
    return normalized


def _is_pokerkit_object(value: object) -> bool:
    module_name = getattr(type(value), "__module__", "")
    return module_name == "pokerkit" or module_name.startswith("pokerkit.")


def _find_sensitive_public_key(
    value: JSONValue | None,
    path: str = "public_payload",
    *,
    allow_private_card_keys: bool = False,
) -> str | None:
    if isinstance(value, dict):
        for key, item in value.items():
            normalized_key = key.lower().replace("-", "_").replace(" ", "_")
            key_path = f"{path}.{key}"
            if normalized_key in _ALWAYS_SENSITIVE_PUBLIC_KEYS:
                return key_path
            if not allow_private_card_keys and normalized_key in _PRIVATE_CARD_PUBLIC_KEYS:
                return key_path
            nested_path = _find_sensitive_public_key(
                item,
                key_path,
                allow_private_card_keys=allow_private_card_keys,
            )
            if nested_path is not None:
                return nested_path
    elif isinstance(value, list):
        for index, item in enumerate(value):
            nested_path = _find_sensitive_public_key(
                item,
                f"{path}[{index}]",
                allow_private_card_keys=allow_private_card_keys,
            )
            if nested_path is not None:
                return nested_path
    return None


def _validate_non_empty_string(value: object, name: str) -> None:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{name} must be a non-empty string")


def _validate_optional_non_empty_string(value: object, name: str) -> None:
    if value is not None:
        _validate_non_empty_string(value, name)


def _required_string(event_dict: Mapping[str, object], key: str) -> str:
    value = event_dict.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"{key} must be a non-empty string")
    return value


def _optional_string(event_dict: Mapping[str, object], key: str) -> str | None:
    value = event_dict.get(key)
    if value is None:
        return None
    if not isinstance(value, str) or not value:
        raise ValueError(f"{key} must be a non-empty string")
    return value


def _optional_int(
    event_dict: Mapping[str, object],
    key: str,
    *,
    default: int | None,
) -> int | None:
    value = event_dict.get(key, default)
    if value is None:
        return None
    if not isinstance(value, int) or isinstance(value, bool):
        raise TypeError(f"{key} must be an integer")
    return value


def _optional_payload(event_dict: Mapping[str, object], key: str) -> JSONValue | None:
    return _normalize_payload(event_dict.get(key), path=key)


__all__ = [
    "EventType",
    "EventVisibility",
    "HandEvent",
    "HandEventLog",
    "JSONValue",
    "TemporaryHandEventLog",
    "append",
    "clear_hand",
    "get_last_sequence",
    "list_player_events",
    "list_public_events",
]
