"""Asynchronous hand driver for platform-level poker services."""

from __future__ import annotations

import asyncio
import inspect
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, fields, is_dataclass
from enum import Enum
from typing import Any, Literal, Protocol
from uuid import uuid4

from mcx_poker.engine.actions import ActionError

Identifier = str | int
HandLoopStatus = Literal["completed", "paused", "reset"]
_HIDDEN_DTO_KEYS = {
    "adapter_hand_ref",
    "deck",
    "deck_order",
    "hidden_hole_cards",
    "hole_cards",
    "private_cards",
    "private_hole_cards",
    "remaining_deck",
    "stub",
    "undealt_cards",
}
_HIDDEN_DTO_KEY_FRAGMENTS = ("deck", "hole_cards", "pocket_cards", "private_cards", "undealt")


@dataclass(frozen=True, slots=True)
class CurrentActor:
    """Platform actor for the current decision point."""

    hand_id: Identifier
    turn_id: Identifier
    seat_index: int
    player_id: Identifier

    def to_dict(self) -> dict[str, object]:
        return {
            "hand_id": self.hand_id,
            "turn_id": self.turn_id,
            "seat_index": self.seat_index,
            "player_id": self.player_id,
        }


@dataclass(frozen=True, slots=True)
class ActionRequestContext:
    """Context created by the loop for a single action request."""

    table_id: Identifier
    hand_id: Identifier
    turn_id: Identifier
    player_id: Identifier
    seat_index: int

    def to_dict(self) -> dict[str, object]:
        return {
            "table_id": self.table_id,
            "hand_id": self.hand_id,
            "turn_id": self.turn_id,
            "player_id": self.player_id,
            "seat_index": self.seat_index,
        }


@dataclass(frozen=True, slots=True)
class ValidatedAction:
    """Validator output with adapter-friendly delegated action fields."""

    action: Any
    normalized_type: str | None = None
    normalized_amount: int | None = None
    validation_source: str = "platform"

    @property
    def player_id(self) -> Any:
        return self.action.player_id

    @property
    def seat_index(self) -> Any:
        return self.action.seat_index

    @property
    def hand_id(self) -> Any:
        return self.action.hand_id

    @property
    def turn_id(self) -> Any:
        return self.action.turn_id

    @property
    def action_type(self) -> Any:
        return self.action.action_type

    @property
    def amount(self) -> Any:
        return getattr(self.action, "amount", None)

    @property
    def source(self) -> Any:
        return getattr(self.action, "source", None)

    def to_dict(self) -> dict[str, object]:
        return {
            "action": _to_public_dto(self.action),
            "normalized_type": self.normalized_type,
            "normalized_amount": self.normalized_amount,
            "validation_source": self.validation_source,
        }


@dataclass(frozen=True, slots=True)
class ValidationResult:
    """Explicit success/failure envelope accepted from validators."""

    ok: bool
    validated_action: Any | None = None
    error: ActionError | None = None

    @classmethod
    def accepted(cls, validated_action: Any) -> ValidationResult:
        return cls(ok=True, validated_action=validated_action)

    @classmethod
    def rejected(cls, error: ActionError) -> ValidationResult:
        return cls(ok=False, error=error)


@dataclass(frozen=True, slots=True)
class HandLoopResult:
    """Outcome of driving one hand to a safe boundary."""

    hand_id: Identifier
    status: HandLoopStatus
    settlement: Any | None = None
    next_hand_context: Any | None = None
    reason: str | None = None


class PokerAdapterProtocol(Protocol):
    """Adapter surface consumed by the game loop."""

    def hand_is_active(self, hand_id: Identifier) -> bool: ...

    def get_current_actor(self, hand_id: Identifier) -> Any | None: ...

    def advance_non_player_state(self, hand_id: Identifier) -> Any: ...

    def submit_action(self, validated_action: Any) -> Any: ...

    def get_hand_settlement(self, hand_id: Identifier) -> Any: ...


class ObservationSystemProtocol(Protocol):
    """Builds player-scoped observations from platform state."""

    def build(self, actor: CurrentActor, context: ActionRequestContext) -> Any: ...


class PlayerControllerProtocol(Protocol):
    """Controller surface used for both human and bot players."""

    def request_action(self, observation: Any, context: ActionRequestContext) -> Any: ...

    def notify_action_rejected(self, action_error: ActionError) -> Any: ...


class PlayerControllerRegistryProtocol(Protocol):
    """Finds the controller assigned to a platform player."""

    def get_controller(self, player_id: Identifier) -> PlayerControllerProtocol: ...


class ActionValidatorProtocol(Protocol):
    """Platform action validator boundary."""

    def validate(self, action: Any, context: ActionRequestContext) -> Any: ...


class TableManagerProtocol(Protocol):
    """Table lifecycle surface consumed at safe boundaries."""

    def get_table_snapshot(self, table_id: Identifier) -> Any: ...

    def apply_hand_settlement(self, settlement: Any) -> Any: ...

    def create_next_hand(self, table_id: Identifier) -> Any: ...


class HandEventLogProtocol(Protocol):
    """Temporary hand event log boundary."""

    def record_hand_started(
        self, hand_id: str, payload: Mapping[str, object] | None = None
    ) -> Any: ...

    def record_action_succeeded(
        self,
        hand_id: str,
        player_id: str,
        action: str,
        *,
        amount: int | float | None = None,
        seat_index: int | None = None,
        payload: Mapping[str, object] | None = None,
    ) -> Any: ...

    def record_action_rejected(
        self,
        hand_id: str,
        player_id: str,
        reason: str,
        *,
        attempted_action: str | None = None,
        seat_index: int | None = None,
        payload: Mapping[str, object] | None = None,
    ) -> Any: ...

    def record_hand_ended(
        self, hand_id: str, payload: Mapping[str, object] | None = None
    ) -> Any: ...


class WebSocketGatewayProtocol(Protocol):
    """Gateway event boundary used by the loop."""

    def broadcast_event(
        self, event_type: str, payload: Any, *, table_id: str | None = None
    ) -> Any: ...

    def send_action_requested(
        self,
        player_id: str,
        seat_index: int,
        payload: Any,
        table_id: str | None = None,
    ) -> Any: ...


@dataclass(frozen=True, slots=True)
class _ControlDecision:
    status: Literal["running", "paused", "reset"]
    reason: str | None = None


class GameLoop:
    """Drive one poker hand from start to settlement using injected services."""

    def __init__(
        self,
        *,
        table_manager: TableManagerProtocol,
        adapter: PokerAdapterProtocol,
        observation_system: ObservationSystemProtocol,
        controller_registry: PlayerControllerRegistryProtocol,
        action_validator: ActionValidatorProtocol,
        hand_event_log: HandEventLogProtocol,
        websocket_gateway: WebSocketGatewayProtocol | None = None,
        turn_id_factory: Any | None = None,
    ) -> None:
        self.table_manager = table_manager
        self.adapter = adapter
        self.observation_system = observation_system
        self.controller_registry = controller_registry
        self.action_validator = action_validator
        self.hand_event_log = hand_event_log
        self.websocket_gateway = websocket_gateway
        self._turn_id_factory = turn_id_factory or (lambda: uuid4().hex)

    async def start_hand(self, hand_context: Any) -> HandLoopResult:
        """Drive a single hand until settlement, pause, or reset."""

        hand_id = _required_identifier(hand_context, "hand_id")
        table_id = _identifier_or_default(hand_context, "table_id", "local-table")

        await self._record_hand_started(hand_id, hand_context)
        await self._broadcast_hand_started(table_id, hand_id, hand_context)

        while await self._hand_is_active(hand_id):
            control = await self._control_decision(table_id)
            if control.status != "running":
                return HandLoopResult(hand_id=hand_id, status=control.status, reason=control.reason)

            actor_ref = await self._get_current_actor(hand_id)
            if actor_ref is None:
                await self._advance_non_player_state(hand_id)
                continue

            turn_id = self._new_turn_id()
            actor = CurrentActor(
                hand_id=hand_id,
                turn_id=turn_id,
                seat_index=_required_int(actor_ref, "seat_index"),
                player_id=_required_identifier(actor_ref, "player_id"),
            )
            context = ActionRequestContext(
                table_id=table_id,
                hand_id=hand_id,
                turn_id=turn_id,
                player_id=actor.player_id,
                seat_index=actor.seat_index,
            )
            observation = await self._build_observation(actor, context, hand_context)
            await self._record_actor_requested(actor, observation, context)
            await self._send_action_requested(table_id, actor, observation, context)

            controller = await self._controller_for(actor)
            action = await _maybe_await(controller.request_action(observation, context))

            control = await self._control_decision(table_id)
            if control.status != "running":
                error = _control_error(control, actor)
                await self._notify_and_record_rejection(controller, actor, error, action)
                return HandLoopResult(hand_id=hand_id, status=control.status, reason=control.reason)

            validation = await self._validate_action(action, context)
            if not validation.ok:
                error = validation.error or _action_error(
                    "action_rejected",
                    "Action validator rejected the action.",
                    actor,
                )
                await self._notify_and_record_rejection(controller, actor, error, action)
                continue

            control = await self._control_decision(table_id)
            if control.status != "running":
                error = _control_error(control, actor)
                await self._notify_and_record_rejection(controller, actor, error, action)
                return HandLoopResult(hand_id=hand_id, status=control.status, reason=control.reason)

            try:
                submission = await self._submit_action(validation.validated_action)
            except Exception as exc:
                error = _error_from_exception(exc, actor)
                await self._notify_and_record_rejection(controller, actor, error, action)
                continue

            submission_error = _submission_error(submission, actor)
            if submission_error is not None:
                await self._notify_and_record_rejection(controller, actor, submission_error, action)
                continue

            await self._record_action_succeeded(actor, action, submission)
            await self._broadcast_state_update(table_id, actor, action, submission)

        settlement = await self._get_settlement(hand_id)
        await self._apply_settlement(settlement, table_id, hand_id)
        await self._record_settlement(hand_id, settlement)
        await self._record_hand_ended(hand_id, settlement)
        await self._broadcast_hand_ended(table_id, hand_id, settlement)

        next_hand_context = None
        control = await self._control_decision(table_id)
        if control.status == "running":
            next_hand_context = await self._create_next_hand(table_id)

        return HandLoopResult(
            hand_id=hand_id,
            status="completed",
            settlement=settlement,
            next_hand_context=next_hand_context,
        )

    def _new_turn_id(self) -> Identifier:
        return _normalize_identifier(self._turn_id_factory(), "turn_id")

    async def _hand_is_active(self, hand_id: Identifier) -> bool:
        if _has_callable(self.adapter, "hand_is_active"):
            return bool(
                await _call_service_method(
                    self.adapter,
                    ("hand_is_active",),
                    {"hand_id": hand_id},
                    ("hand_id",),
                )
            )
        if _has_callable(self.adapter, "is_hand_active"):
            return bool(
                await _call_service_method(
                    self.adapter,
                    ("is_hand_active",),
                    {"hand_id": hand_id},
                    ("hand_id",),
                )
            )
        summary = await self._state_summary(hand_id)
        return bool(_field(summary, "is_active", _field(summary, "status", False)))

    async def _get_current_actor(self, hand_id: Identifier) -> Any | None:
        if _has_callable(self.adapter, "get_current_actor"):
            return await _call_service_method(
                self.adapter,
                ("get_current_actor",),
                {"hand_id": hand_id},
                ("hand_id",),
            )
        if _has_callable(self.adapter, "current_actor"):
            return await _call_service_method(
                self.adapter,
                ("current_actor",),
                {"hand_id": hand_id},
                ("hand_id",),
            )
        summary = await self._state_summary(hand_id)
        return _field(summary, "current_actor")

    async def _advance_non_player_state(self, hand_id: Identifier) -> None:
        if _has_callable(self.adapter, "advance_non_player_state"):
            await _call_service_method(
                self.adapter,
                ("advance_non_player_state",),
                {"hand_id": hand_id},
                ("hand_id",),
            )
            return
        if _has_callable(self.adapter, "advance"):
            await _call_service_method(
                self.adapter,
                ("advance",),
                {"hand_id": hand_id},
                ("hand_id",),
            )
            return
        await asyncio.sleep(0)

    async def _state_summary(self, hand_id: Identifier) -> Any:
        return await _call_service_method(
            self.adapter,
            ("get_state_summary", "state_summary"),
            {"hand_id": hand_id},
            ("hand_id",),
        )

    async def _build_observation(
        self,
        actor: CurrentActor,
        context: ActionRequestContext,
        hand_context: Any,
    ) -> Any:
        payload = {
            "actor": actor,
            "context": context,
            "hand_context": hand_context,
            "hand_id": actor.hand_id,
            "player_id": actor.player_id,
            "seat_index": actor.seat_index,
            "turn_id": actor.turn_id,
        }
        return await _call_service_method(
            self.observation_system,
            ("build", "build_observation", "observe"),
            payload,
            ("actor", "context"),
        )

    async def _controller_for(self, actor: CurrentActor) -> PlayerControllerProtocol:
        controller = await _call_service_method(
            self.controller_registry,
            ("get_controller", "controller_for", "get"),
            {
                "player_id": actor.player_id,
                "seat_index": actor.seat_index,
                "actor": actor,
            },
            ("player_id",),
        )
        return controller

    async def _validate_action(
        self,
        action: Any,
        context: ActionRequestContext,
    ) -> ValidationResult:
        try:
            raw_result = await _call_service_method(
                self.action_validator,
                ("validate", "validate_action"),
                {"action": action, "context": context},
                ("action", "context"),
            )
        except Exception as exc:
            return ValidationResult.rejected(_error_from_exception(exc, context))

        return _coerce_validation_result(raw_result, action, context)

    async def _submit_action(self, validated_action: Any) -> Any:
        return await _call_service_method(
            self.adapter,
            ("submit_action",),
            {"validated_action": validated_action, "action": validated_action},
            ("validated_action",),
        )

    async def _get_settlement(self, hand_id: Identifier) -> Any:
        return await _call_service_method(
            self.adapter,
            ("get_hand_settlement", "get_settlement"),
            {"hand_id": hand_id},
            ("hand_id",),
        )

    async def _apply_settlement(
        self,
        settlement: Any,
        table_id: Identifier,
        hand_id: Identifier,
    ) -> None:
        await _call_service_method(
            self.table_manager,
            ("apply_hand_settlement",),
            {"settlement": settlement, "table_id": table_id, "hand_id": hand_id},
            ("settlement",),
        )

    async def _create_next_hand(self, table_id: Identifier) -> Any:
        if not _has_callable(self.table_manager, "create_next_hand"):
            return None
        return await _call_service_method(
            self.table_manager,
            ("create_next_hand",),
            {"table_id": table_id},
            ("table_id",),
        )

    async def _control_decision(self, table_id: Identifier) -> _ControlDecision:
        status: Any = None

        if _has_callable(self.table_manager, "is_table_resetting"):
            resetting = await _call_service_method(
                self.table_manager,
                ("is_table_resetting",),
                {"table_id": table_id},
                ("table_id",),
            )
            if resetting:
                return _ControlDecision("reset", "table reset")

        if _has_callable(self.table_manager, "is_table_paused"):
            paused = await _call_service_method(
                self.table_manager,
                ("is_table_paused",),
                {"table_id": table_id},
                ("table_id",),
            )
            if paused:
                return _ControlDecision("paused", "table paused")

        if _has_callable(self.table_manager, "get_table_status"):
            status = await _call_service_method(
                self.table_manager,
                ("get_table_status",),
                {"table_id": table_id},
                ("table_id",),
            )
        elif _has_callable(self.table_manager, "get_table_snapshot"):
            snapshot = await _call_service_method(
                self.table_manager,
                ("get_table_snapshot",),
                {"table_id": table_id},
                ("table_id",),
            )
            status = _field(snapshot, "status")
        elif _has_callable(self.table_manager, "get_table"):
            snapshot = await _call_service_method(
                self.table_manager,
                ("get_table",),
                {"table_id": table_id},
                ("table_id",),
            )
            status = _field(snapshot, "status")
        else:
            status = _field(self.table_manager, "status")

        normalized = _status_value(status)
        if normalized in {"reset", "resetting"}:
            return _ControlDecision("reset", "table reset")
        if normalized in {"paused", "pausing"}:
            return _ControlDecision("paused", "table paused")
        return _ControlDecision("running")

    async def _record_hand_started(self, hand_id: Identifier, hand_context: Any) -> None:
        payload = {"hand_context": _to_public_dto(hand_context)}
        await _call_optional(
            self.hand_event_log,
            ("record_hand_started",),
            {"hand_id": str(hand_id), "payload": payload},
            ("hand_id",),
        )

    async def _record_actor_requested(
        self,
        actor: CurrentActor,
        observation: Any,
        context: ActionRequestContext,
    ) -> None:
        payload = {
            "actor": actor.to_dict(),
            "context": context.to_dict(),
            "observation": _to_public_dto(observation),
        }
        await _call_optional(
            self.hand_event_log,
            ("record_actor_requested",),
            {
                "hand_id": str(actor.hand_id),
                "player_id": str(actor.player_id),
                "seat_index": actor.seat_index,
                "turn_id": str(actor.turn_id),
                "payload": payload,
            },
            ("hand_id", "player_id", "seat_index", "turn_id"),
        )

    async def _notify_and_record_rejection(
        self,
        controller: Any,
        actor: CurrentActor,
        error: ActionError,
        action: Any,
    ) -> None:
        if _has_callable(controller, "notify_action_rejected"):
            await _call_service_method(
                controller,
                ("notify_action_rejected",),
                {"action_error": error, "error": error},
                ("action_error",),
            )

        payload = {
            "error": error.to_dict(),
            "action": _to_public_dto(action),
        }
        await _call_optional(
            self.hand_event_log,
            ("record_action_rejected",),
            {
                "hand_id": str(actor.hand_id),
                "player_id": str(actor.player_id),
                "reason": error.message,
                "attempted_action": _action_type_value(action),
                "seat_index": actor.seat_index,
                "payload": payload,
            },
            ("hand_id", "player_id", "reason"),
        )
        await self._send_action_rejected(actor, error, action)

    async def _record_action_succeeded(
        self,
        actor: CurrentActor,
        action: Any,
        submission: Any,
    ) -> None:
        payload = {
            "actor": actor.to_dict(),
            "action": _to_public_dto(action),
            "result": _to_public_dto(submission),
        }
        await _call_optional(
            self.hand_event_log,
            ("record_action_succeeded",),
            {
                "hand_id": str(actor.hand_id),
                "player_id": str(actor.player_id),
                "action": _action_type_value(action),
                "amount": _field(action, "amount"),
                "seat_index": actor.seat_index,
                "payload": payload,
            },
            ("hand_id", "player_id", "action"),
        )

    async def _record_settlement(self, hand_id: Identifier, settlement: Any) -> None:
        await _call_optional(
            self.hand_event_log,
            ("record_settlement",),
            {"hand_id": str(hand_id), "settlement": _to_public_dto(settlement)},
            ("hand_id", "settlement"),
        )

    async def _record_hand_ended(self, hand_id: Identifier, settlement: Any) -> None:
        await _call_optional(
            self.hand_event_log,
            ("record_hand_ended",),
            {
                "hand_id": str(hand_id),
                "payload": {"settlement": _to_public_dto(settlement)},
            },
            ("hand_id",),
        )

    async def _broadcast_hand_started(
        self,
        table_id: Identifier,
        hand_id: Identifier,
        hand_context: Any,
    ) -> None:
        payload = {"hand_id": hand_id, "hand_context": _to_public_dto(hand_context)}
        await self._broadcast(
            ("broadcast_hand_started",),
            "hand_started",
            payload,
            table_id=table_id,
        )

    async def _send_action_requested(
        self,
        table_id: Identifier,
        actor: CurrentActor,
        observation: Any,
        context: ActionRequestContext,
    ) -> None:
        if self.websocket_gateway is None:
            return
        payload = {
            "table_id": table_id,
            "hand_id": actor.hand_id,
            "turn_id": actor.turn_id,
            "player_id": actor.player_id,
            "seat_index": actor.seat_index,
            "observation": _to_public_dto(observation),
            "context": context.to_dict(),
        }
        if _has_callable(self.websocket_gateway, "send_action_requested"):
            await _call_service_method(
                self.websocket_gateway,
                ("send_action_requested",),
                {
                    "player_id": str(actor.player_id),
                    "seat_index": actor.seat_index,
                    "payload": payload,
                    "table_id": str(table_id),
                },
                ("player_id", "seat_index", "payload"),
            )
            return
        await _call_optional(
            self.websocket_gateway,
            ("broadcast_actor_requested", "send_actor_requested"),
            {"payload": payload, "table_id": str(table_id)},
            ("payload",),
        )

    async def _send_action_rejected(
        self,
        actor: CurrentActor,
        error: ActionError,
        action: Any,
    ) -> None:
        if self.websocket_gateway is None:
            return
        payload = {
            "actor": actor.to_dict(),
            "error": error.to_dict(),
            "action": _to_public_dto(action),
        }
        await _call_optional(
            self.websocket_gateway,
            ("broadcast_action_rejected", "send_action_rejected_to_player"),
            {
                "player_id": str(actor.player_id),
                "seat_index": actor.seat_index,
                "payload": payload,
            },
            ("player_id", "seat_index", "payload"),
        )

    async def _broadcast_state_update(
        self,
        table_id: Identifier,
        actor: CurrentActor,
        action: Any,
        submission: Any,
    ) -> None:
        payload = {
            "hand_id": actor.hand_id,
            "turn_id": actor.turn_id,
            "player_id": actor.player_id,
            "seat_index": actor.seat_index,
            "action": _to_public_dto(action),
            "result": _to_public_dto(submission),
        }
        if self.websocket_gateway is None:
            return
        if _has_callable(self.websocket_gateway, "broadcast_state_update"):
            await _call_service_method(
                self.websocket_gateway,
                ("broadcast_state_update",),
                {"payload": payload, "table_id": str(table_id)},
                ("payload",),
            )
            return
        await self._broadcast(
            ("broadcast_player_acted",),
            "player_acted",
            payload,
            table_id=table_id,
        )

    async def _broadcast_hand_ended(
        self,
        table_id: Identifier,
        hand_id: Identifier,
        settlement: Any,
    ) -> None:
        payload = {"hand_id": hand_id, "settlement": _to_public_dto(settlement)}
        await self._broadcast(("broadcast_hand_ended",), "hand_ended", payload, table_id=table_id)

    async def _broadcast(
        self,
        method_names: tuple[str, ...],
        event_type: str,
        payload: Any,
        *,
        table_id: Identifier,
    ) -> None:
        if self.websocket_gateway is None:
            return
        if any(_has_callable(self.websocket_gateway, method_name) for method_name in method_names):
            await _call_service_method(
                self.websocket_gateway,
                method_names,
                {"payload": payload, "table_id": str(table_id)},
                ("payload",),
            )
            return
        if _has_callable(self.websocket_gateway, "broadcast_event"):
            await _call_service_method(
                self.websocket_gateway,
                ("broadcast_event",),
                {
                    "event_type": event_type,
                    "payload": payload,
                    "table_id": str(table_id),
                },
                ("event_type", "payload"),
            )


def _coerce_validation_result(raw_result: Any, action: Any, context: Any) -> ValidationResult:
    if isinstance(raw_result, ValidationResult):
        return raw_result
    if isinstance(raw_result, ActionError):
        return ValidationResult.rejected(raw_result)
    if isinstance(raw_result, Mapping):
        ok = bool(raw_result.get("ok", raw_result.get("valid", True)))
        if not ok:
            return ValidationResult.rejected(_error_from_raw(raw_result.get("error"), context))
        validated = raw_result.get("validated_action", raw_result.get("action", action))
        return ValidationResult.accepted(validated)
    if isinstance(raw_result, tuple) and len(raw_result) == 2:
        ok, value = raw_result
        if ok:
            return ValidationResult.accepted(value)
        return ValidationResult.rejected(_error_from_raw(value, context))

    ok = _field(raw_result, "ok", _field(raw_result, "valid"))
    if ok is False:
        return ValidationResult.rejected(_error_from_raw(_field(raw_result, "error"), context))
    validated = _field(raw_result, "validated_action", _field(raw_result, "action"))
    if validated is not None and raw_result is not None:
        return ValidationResult.accepted(validated)
    if raw_result is None:
        return ValidationResult.accepted(action)
    return ValidationResult.accepted(raw_result)


def _submission_error(submission: Any, actor: CurrentActor) -> ActionError | None:
    if isinstance(submission, Mapping):
        if submission.get("ok") is False:
            return _error_from_raw(submission.get("error"), actor)
        return None
    if _field(submission, "ok") is False:
        return _error_from_raw(_field(submission, "error"), actor)
    error = _field(submission, "error")
    if error is not None:
        return _error_from_raw(error, actor)
    return None


def _control_error(control: _ControlDecision, actor: CurrentActor) -> ActionError:
    if control.status == "reset":
        return _action_error("table_reset", control.reason or "Table was reset.", actor)
    return _action_error("table_paused", control.reason or "Table is paused.", actor)


def _error_from_exception(exc: Exception, context: Any) -> ActionError:
    return _error_from_raw(exc, context)


def _error_from_raw(raw_error: Any, context: Any) -> ActionError:
    if isinstance(raw_error, ActionError):
        return raw_error
    if isinstance(raw_error, Mapping):
        return ActionError(
            code=str(raw_error.get("code", "action_rejected")),
            message=str(raw_error.get("message", "Action was rejected.")),
            player_id=_field_or_mapping(raw_error, "player_id", _field(context, "player_id")),
            hand_id=_field_or_mapping(raw_error, "hand_id", _field(context, "hand_id")),
            turn_id=_field_or_mapping(raw_error, "turn_id", _field(context, "turn_id")),
            retry_same_player=bool(raw_error.get("retry_same_player", True)),
        )

    return ActionError(
        code=str(_field(raw_error, "code", "action_rejected")),
        message=str(_field(raw_error, "message", str(raw_error) or "Action was rejected.")),
        player_id=_field(raw_error, "player_id", _field(context, "player_id")),
        hand_id=_field(raw_error, "hand_id", _field(context, "hand_id")),
        turn_id=_field(raw_error, "turn_id", _field(context, "turn_id")),
        retry_same_player=bool(_field(raw_error, "retry_same_player", True)),
    )


def _action_error(code: str, message: str, context: Any) -> ActionError:
    return ActionError(
        code=code,
        message=message,
        player_id=_field(context, "player_id"),
        hand_id=_field(context, "hand_id"),
        turn_id=_field(context, "turn_id"),
        retry_same_player=True,
    )


async def _call_optional(
    service: Any,
    method_names: tuple[str, ...],
    payload: Mapping[str, Any],
    positional_order: tuple[str, ...] = (),
) -> Any:
    if not any(_has_callable(service, method_name) for method_name in method_names):
        return None
    return await _call_service_method(service, method_names, payload, positional_order)


async def _call_service_method(
    service: Any,
    method_names: tuple[str, ...],
    payload: Mapping[str, Any],
    positional_order: tuple[str, ...] = (),
) -> Any:
    target = None
    for method_name in method_names:
        candidate = getattr(service, method_name, None)
        if callable(candidate):
            target = candidate
            break
    if target is None:
        names = ", ".join(method_names)
        raise AttributeError(f"service does not provide any of: {names}")

    result = _call_with_supported_arguments(target, payload, positional_order)
    return await _maybe_await(result)


def _call_with_supported_arguments(
    target: Any,
    payload: Mapping[str, Any],
    positional_order: tuple[str, ...],
) -> Any:
    try:
        signature = inspect.signature(target)
    except (TypeError, ValueError):
        ordered_args = [payload[name] for name in positional_order if name in payload]
        return target(*ordered_args)

    parameters = list(signature.parameters.values())
    if any(parameter.kind == inspect.Parameter.VAR_KEYWORD for parameter in parameters):
        return target(**payload)

    supported_keyword_names = {
        parameter.name
        for parameter in parameters
        if parameter.kind
        in (inspect.Parameter.POSITIONAL_OR_KEYWORD, inspect.Parameter.KEYWORD_ONLY)
    }
    supported_payload = {
        name: value for name, value in payload.items() if name in supported_keyword_names
    }
    if supported_payload and set(supported_payload) == set(payload):
        return target(**supported_payload)

    positional_parameters = [
        parameter
        for parameter in parameters
        if parameter.kind
        in (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD)
    ]
    if len(positional_parameters) == 1 and len(supported_payload) == 1:
        name = next(iter(supported_payload))
        return target(supported_payload[name])
    if supported_payload and not positional_parameters:
        return target(**supported_payload)

    ordered_args = [payload[name] for name in positional_order if name in payload]
    return target(*ordered_args[: len(positional_parameters)])


async def _maybe_await(result: Any) -> Any:
    if inspect.isawaitable(result):
        return await result
    return result


def _field(value: Any, name: str, default: Any = None) -> Any:
    if value is None:
        return default
    if isinstance(value, Mapping):
        return value.get(name, default)
    return getattr(value, name, default)


def _field_or_mapping(value: Mapping[str, Any], name: str, default: Any = None) -> Any:
    return value.get(name, default)


def _required_identifier(value: Any, name: str) -> Identifier:
    return _normalize_identifier(_field(value, name), name)


def _identifier_or_default(value: Any, name: str, default: Identifier) -> Identifier:
    raw_value = _field(value, name, default)
    return _normalize_identifier(raw_value, name)


def _normalize_identifier(value: Any, name: str) -> Identifier:
    if isinstance(value, bool) or value is None:
        raise ValueError(f"{name} must be a string or integer identifier")
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value:
        return value
    raise ValueError(f"{name} must be a non-empty string or integer identifier")


def _required_int(value: Any, name: str) -> int:
    raw_value = _field(value, name)
    if isinstance(raw_value, bool) or not isinstance(raw_value, int):
        raise ValueError(f"{name} must be an integer")
    return raw_value


def _status_value(status: Any) -> str:
    if isinstance(status, Enum):
        return str(status.value).casefold()
    if status is None:
        return "running"
    return str(status).casefold()


def _action_type_value(action: Any) -> str:
    action_type = _field(action, "action_type", "unknown")
    if isinstance(action_type, Enum):
        return str(action_type.value)
    return str(action_type)


def _has_callable(service: Any, method_name: str) -> bool:
    return callable(getattr(service, method_name, None))


def _to_public_dto(value: Any) -> Any:
    if value is None or isinstance(value, str | int | float | bool):
        return value
    if isinstance(value, Enum):
        return value.value

    value_type = value.__class__
    module_name = getattr(value_type, "__module__", "").casefold()
    if "pokerkit" in module_name:
        return None

    if isinstance(value, Mapping):
        public: dict[str, Any] = {}
        for raw_key, raw_item in value.items():
            key = str(raw_key)
            normalized_key = key.casefold()
            if (
                normalized_key in _HIDDEN_DTO_KEYS
                or "pokerkit" in normalized_key
                or any(fragment in normalized_key for fragment in _HIDDEN_DTO_KEY_FRAGMENTS)
            ):
                continue
            public[key] = _to_public_dto(raw_item)
        return public

    if isinstance(value, Sequence) and not isinstance(value, str | bytes | bytearray):
        return [_to_public_dto(item) for item in value]

    if hasattr(value, "to_dict") and callable(value.to_dict):
        return _to_public_dto(value.to_dict())
    if hasattr(value, "model_dump") and callable(value.model_dump):
        return _to_public_dto(value.model_dump())
    if is_dataclass(value):
        return {field.name: _to_public_dto(getattr(value, field.name)) for field in fields(value)}
    if hasattr(value, "__dict__"):
        return _to_public_dto(vars(value))
    return repr(value)


__all__ = [
    "ActionRequestContext",
    "ActionValidatorProtocol",
    "CurrentActor",
    "GameLoop",
    "HandEventLogProtocol",
    "HandLoopResult",
    "ObservationSystemProtocol",
    "PlayerControllerProtocol",
    "PlayerControllerRegistryProtocol",
    "PokerAdapterProtocol",
    "TableManagerProtocol",
    "ValidatedAction",
    "ValidationResult",
    "WebSocketGatewayProtocol",
]
