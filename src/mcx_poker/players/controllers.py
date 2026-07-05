"""Player controller boundary implementations.

Controllers consume platform observations and return platform-native
``PlayerAction`` objects. This module intentionally has no dependency on
PokerKit or table-manager internals.
"""

from __future__ import annotations

import asyncio
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, replace
from enum import StrEnum
from typing import Any, Protocol, runtime_checkable

from mcx_poker.engine.actions import (
    ActionError,
    ActionSource,
    ActionType,
    Identifier,
    LegalAction,
    LegalActionSet,
    PlayerAction,
)


class ControllerType(StrEnum):
    """Controller source types known by the player-controller registry."""

    HUMAN = "human"
    BOT = "bot"
    FUTURE_AGENT = "future_agent"


class ControllerError(ValueError):
    """Base error for controller boundary failures."""


class NoLegalActionAvailable(ControllerError):
    """Raised when an observation exposes no enabled legal action."""


class BotStrategyError(ControllerError):
    """Raised when a bot strategy returns an unusable decision."""


class PendingActionError(ControllerError):
    """Raised when a human controller receives conflicting pending requests."""


class ActionSubmissionRejected(ControllerError):
    """Raised when a submitted human action does not match the active turn."""

    action_error: ActionError

    def __init__(self, action_error: ActionError) -> None:
        self.action_error = action_error
        super().__init__(action_error.message)


@dataclass(frozen=True, slots=True)
class ActionRequestContext:
    """Metadata attached to one controller action request."""

    table_id: Identifier
    hand_id: Identifier
    turn_id: Identifier
    player_id: Identifier
    seat_index: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "table_id", _validate_identifier(self.table_id, "table_id"))
        object.__setattr__(self, "hand_id", _validate_identifier(self.hand_id, "hand_id"))
        object.__setattr__(self, "turn_id", _validate_identifier(self.turn_id, "turn_id"))
        object.__setattr__(self, "player_id", _validate_identifier(self.player_id, "player_id"))
        object.__setattr__(self, "seat_index", _validate_seat_index(self.seat_index))

    def to_dict(self) -> dict[str, object]:
        return {
            "table_id": self.table_id,
            "hand_id": self.hand_id,
            "turn_id": self.turn_id,
            "player_id": self.player_id,
            "seat_index": self.seat_index,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> ActionRequestContext:
        _require_mapping(data, "ActionRequestContext")
        _require_keys(
            data,
            "ActionRequestContext",
            ("table_id", "hand_id", "turn_id", "player_id", "seat_index"),
        )
        return cls(
            table_id=data["table_id"],
            hand_id=data["hand_id"],
            turn_id=data["turn_id"],
            player_id=data["player_id"],
            seat_index=data["seat_index"],
        )


@runtime_checkable
class PlayerObservation(Protocol):
    """Minimal observation shape consumed by controllers."""

    @property
    def observer_player_id(self) -> Identifier:
        """Player id of the observing actor."""
        ...

    @property
    def observer_seat_index(self) -> int:
        """Seat index of the observing actor."""
        ...

    @property
    def table_id(self) -> Identifier:
        """Current table id."""
        ...

    @property
    def hand_id(self) -> Identifier:
        """Current hand id."""
        ...

    @property
    def turn_id(self) -> Identifier:
        """Current turn id."""
        ...

    @property
    def legal_actions(self) -> Iterable[LegalAction | Mapping[str, Any] | str]:
        """Currently visible legal action descriptions."""
        ...


@runtime_checkable
class PlayerController(Protocol):
    """Async controller boundary consumed by the game loop."""

    async def request_action(
        self,
        observation: PlayerObservation,
        action_request_context: ActionRequestContext | None = None,
    ) -> PlayerAction:
        """Return one platform action for the supplied observation."""
        ...

    async def notify_action_rejected(self, action_error: ActionError | object) -> None:
        """Receive an action rejection notification from the platform."""
        ...

    async def notify_hand_started(self, hand_context: object) -> None:
        """Receive a hand-started notification."""
        ...

    async def notify_hand_ended(self, result_summary: object) -> None:
        """Receive a hand-ended notification."""
        ...


class BotStrategy(Protocol):
    """Replaceable strategy hook for bot controllers."""

    def select_action(
        self,
        observation: PlayerObservation,
        context: ActionRequestContext,
        legal_actions: Sequence[LegalAction],
    ) -> LegalAction | PlayerAction:
        """Select a legal action description or return a full action."""
        ...


@dataclass(slots=True)
class PendingHumanAction:
    """The currently open human decision point."""

    observation: PlayerObservation
    context: ActionRequestContext
    future: asyncio.Future[PlayerAction]
    waiter_active: bool = False
    last_error: ActionError | object | None = None


@dataclass(frozen=True, slots=True)
class ControllerRegistration:
    """Registry entry for one player controller."""

    player_id: Identifier
    controller: PlayerController
    seat_index: int | None = None
    controller_type: ControllerType = ControllerType.HUMAN


class ControllerRegistry:
    """Lookup registry for controllers by player id or seat index."""

    def __init__(self) -> None:
        self._by_player_id: dict[Identifier, ControllerRegistration] = {}
        self._by_seat_index: dict[int, Identifier] = {}

    def register(
        self,
        player_id: Identifier,
        controller: PlayerController,
        *,
        seat_index: int | None = None,
        controller_type: ControllerType | str = ControllerType.HUMAN,
    ) -> None:
        normalized_player_id = _validate_identifier(player_id, "player_id")
        normalized_seat_index = None if seat_index is None else _validate_seat_index(seat_index)
        normalized_type = _parse_controller_type(controller_type)
        _require_request_action(controller)

        if normalized_seat_index is not None:
            existing_player_id = self._by_seat_index.get(normalized_seat_index)
            if existing_player_id is not None and existing_player_id != normalized_player_id:
                raise ValueError(
                    f"seat {normalized_seat_index} already has a registered controller"
                )
            self._by_seat_index[normalized_seat_index] = normalized_player_id

        self._by_player_id[normalized_player_id] = ControllerRegistration(
            player_id=normalized_player_id,
            controller=controller,
            seat_index=normalized_seat_index,
            controller_type=normalized_type,
        )

    def get(self, player_id: Identifier) -> PlayerController:
        return self.get_by_player_id(player_id)

    def get_by_player_id(self, player_id: Identifier) -> PlayerController:
        return self.get_registration_by_player_id(player_id).controller

    def get_by_seat_index(self, seat_index: int) -> PlayerController:
        return self.get_registration_by_seat_index(seat_index).controller

    def get_registration_by_player_id(self, player_id: Identifier) -> ControllerRegistration:
        normalized_player_id = _validate_identifier(player_id, "player_id")
        try:
            return self._by_player_id[normalized_player_id]
        except KeyError as exc:
            raise KeyError(f"no controller registered for player {normalized_player_id!r}") from exc

    def get_registration_by_seat_index(self, seat_index: int) -> ControllerRegistration:
        normalized_seat_index = _validate_seat_index(seat_index)
        try:
            player_id = self._by_seat_index[normalized_seat_index]
        except KeyError as exc:
            raise KeyError(f"no controller registered for seat {normalized_seat_index!r}") from exc
        return self._by_player_id[player_id]

    async def request_action(
        self,
        player_id: Identifier,
        observation: PlayerObservation,
        action_request_context: ActionRequestContext | None = None,
    ) -> PlayerAction:
        return await self.get_by_player_id(player_id).request_action(
            observation,
            action_request_context,
        )

    async def request_action_by_seat_index(
        self,
        seat_index: int,
        observation: PlayerObservation,
        action_request_context: ActionRequestContext | None = None,
    ) -> PlayerAction:
        return await self.get_by_seat_index(seat_index).request_action(
            observation,
            action_request_context,
        )


class NoopLifecycleController:
    """Shared no-op lifecycle hooks for simple controllers."""

    async def notify_action_rejected(self, action_error: ActionError | object) -> None:
        return None

    async def notify_hand_started(self, hand_context: object) -> None:
        return None

    async def notify_hand_ended(self, result_summary: object) -> None:
        return None


class FirstLegalActionStrategy:
    """Deterministic strategy that selects the first enabled legal action."""

    def select_action(
        self,
        observation: PlayerObservation,
        context: ActionRequestContext,
        legal_actions: Sequence[LegalAction],
    ) -> LegalAction:
        del observation, context
        for legal_action in legal_actions:
            if legal_action.enabled:
                return legal_action
        raise NoLegalActionAvailable("observation does not expose an enabled legal action")


class BotPlayerController(NoopLifecycleController):
    """Minimal deterministic bot controller.

    The default strategy chooses only from ``observation.legal_actions``. If a
    custom strategy returns a full ``PlayerAction``, this controller returns it
    unchanged instead of replacing it with a fallback.
    """

    controller_type = ControllerType.BOT

    def __init__(self, strategy: BotStrategy | None = None) -> None:
        self.strategy = strategy or FirstLegalActionStrategy()

    async def request_action(
        self,
        observation: PlayerObservation,
        action_request_context: ActionRequestContext | None = None,
    ) -> PlayerAction:
        context = action_request_context or _context_from_observation(observation)
        legal_actions = _legal_actions_from_observation(observation)
        decision = self.strategy.select_action(observation, context, legal_actions)

        if isinstance(decision, PlayerAction):
            return decision
        if not isinstance(decision, LegalAction):
            raise BotStrategyError("bot strategy must return LegalAction or PlayerAction")
        if not decision.enabled:
            raise BotStrategyError("bot strategy returned a disabled legal action")
        if decision not in legal_actions:
            raise BotStrategyError("bot strategy returned an action outside legal_actions")

        return _player_action_from_legal_action(decision, context, ActionSource.BOT)


class HumanPlayerController(NoopLifecycleController):
    """Human controller that waits for one submitted action per pending turn."""

    controller_type = ControllerType.HUMAN

    def __init__(self) -> None:
        self._pending: PendingHumanAction | None = None
        self._action_errors: list[ActionError | object] = []

    @property
    def pending_action(self) -> PendingHumanAction | None:
        return self._pending

    @property
    def pending_context(self) -> ActionRequestContext | None:
        return None if self._pending is None else self._pending.context

    @property
    def pending_turn_id(self) -> Identifier | None:
        return None if self._pending is None else self._pending.context.turn_id

    @property
    def last_action_error(self) -> ActionError | object | None:
        if not self._action_errors:
            return None
        return self._action_errors[-1]

    @property
    def action_errors(self) -> tuple[ActionError | object, ...]:
        return tuple(self._action_errors)

    async def request_action(
        self,
        observation: PlayerObservation,
        action_request_context: ActionRequestContext | None = None,
    ) -> PlayerAction:
        context = action_request_context or _context_from_observation(observation)
        pending = self._ensure_pending_action(observation, context)
        try:
            return await pending.future
        except asyncio.CancelledError:
            if self._pending is pending and not pending.future.done():
                self._pending = None
            raise
        finally:
            if self._pending is pending:
                pending.waiter_active = False

    async def submit_action(self, action: PlayerAction | Mapping[str, Any]) -> PlayerAction:
        pending = self._pending
        submitted_action = _coerce_player_action(action)
        if pending is None:
            raise _submission_rejected(
                "no_pending_action",
                "no pending human action is registered",
                submitted_action,
            )
        if pending.future.done():
            raise _submission_rejected(
                "action_already_submitted",
                "an action has already been submitted for this turn",
                submitted_action,
            )

        _validate_submitted_action_matches_context(submitted_action, pending.context)
        human_action = replace(submitted_action, source=ActionSource.HUMAN)
        pending.future.set_result(human_action)
        return human_action

    async def notify_action_rejected(self, action_error: ActionError | object) -> None:
        self._action_errors.append(action_error)
        pending = self._pending
        if pending is None:
            return None

        pending.last_error = action_error
        if isinstance(action_error, ActionError) and not action_error.retry_same_player:
            if not pending.future.done():
                pending.future.set_exception(ActionSubmissionRejected(action_error))
            self._pending = None
            return None

        if _action_error_matches_context(action_error, pending.context) and pending.future.done():
            pending.future = asyncio.get_running_loop().create_future()
        return None

    async def notify_hand_started(self, hand_context: object) -> None:
        self._pending = None
        self._action_errors.clear()

    async def notify_hand_ended(self, result_summary: object) -> None:
        pending = self._pending
        if pending is not None and not pending.future.done():
            pending.future.cancel()
        self._pending = None

    def _ensure_pending_action(
        self,
        observation: PlayerObservation,
        context: ActionRequestContext,
    ) -> PendingHumanAction:
        pending = self._pending
        if pending is None:
            self._pending = PendingHumanAction(
                observation=observation,
                context=context,
                future=asyncio.get_running_loop().create_future(),
                waiter_active=True,
            )
            return self._pending

        if _same_action_context(pending.context, context):
            if pending.waiter_active:
                raise PendingActionError("a pending human action is already registered")
            if pending.future.done():
                raise PendingActionError(
                    "an action has already been submitted for this turn; "
                    "waiting for rejection or the next turn"
                )
            pending.observation = observation
            pending.waiter_active = True
            return pending

        if pending.last_error is not None:
            self._pending = PendingHumanAction(
                observation=observation,
                context=context,
                future=asyncio.get_running_loop().create_future(),
                waiter_active=True,
                last_error=pending.last_error,
            )
            return self._pending

        if not pending.future.done():
            raise PendingActionError("a different pending human action is already registered")

        self._pending = PendingHumanAction(
            observation=observation,
            context=context,
            future=asyncio.get_running_loop().create_future(),
            waiter_active=True,
        )
        return self._pending


class FutureAgentPlayerController(NoopLifecycleController):
    """Reserved future-agent controller type without real LLM/GTO behavior."""

    controller_type = ControllerType.FUTURE_AGENT

    async def request_action(
        self,
        observation: PlayerObservation,
        action_request_context: ActionRequestContext | None = None,
    ) -> PlayerAction:
        del observation, action_request_context
        raise NotImplementedError("future_agent controllers are reserved for future work")


DeterministicBotPlayerController = BotPlayerController


def _player_action_from_legal_action(
    legal_action: LegalAction,
    context: ActionRequestContext,
    source: ActionSource,
) -> PlayerAction:
    return PlayerAction(
        player_id=context.player_id,
        seat_index=context.seat_index,
        hand_id=context.hand_id,
        turn_id=context.turn_id,
        action_type=legal_action.action_type,
        amount=_amount_for_legal_action(legal_action),
        source=source,
    )


def _amount_for_legal_action(legal_action: LegalAction) -> int | None:
    if legal_action.action_type is not ActionType.RAISE_TO:
        return None
    if legal_action.amount_fixed is not None:
        return legal_action.amount_fixed
    if legal_action.amount_min is not None:
        return legal_action.amount_min
    if legal_action.amount_max is not None:
        return legal_action.amount_max
    raise NoLegalActionAvailable("RaiseTo legal action requires an amount boundary")


def _context_from_observation(observation: PlayerObservation) -> ActionRequestContext:
    return ActionRequestContext(
        table_id=_validate_identifier(_read_observation_field(observation, "table_id"), "table_id"),
        hand_id=_validate_identifier(_read_observation_field(observation, "hand_id"), "hand_id"),
        turn_id=_validate_identifier(_read_observation_field(observation, "turn_id"), "turn_id"),
        player_id=_validate_identifier(
            _read_observation_field(observation, "observer_player_id", "player_id"),
            "player_id",
        ),
        seat_index=_validate_seat_index(
            _read_observation_field(observation, "observer_seat_index", "seat_index")
        ),
    )


def _read_observation_field(observation: object, *names: str) -> object:
    for name in names:
        if hasattr(observation, name):
            return getattr(observation, name)
    joined_names = " or ".join(names)
    raise ControllerError(f"observation missing required field: {joined_names}")


def _legal_actions_from_observation(observation: PlayerObservation) -> tuple[LegalAction, ...]:
    raw_legal_actions = _read_observation_field(observation, "legal_actions")
    iterable: Iterable[object]
    if isinstance(raw_legal_actions, LegalActionSet):
        iterable = raw_legal_actions.actions
    elif isinstance(raw_legal_actions, Mapping | str | bytes) or not isinstance(
        raw_legal_actions,
        Iterable,
    ):
        raise ControllerError("observation.legal_actions must be an iterable")
    else:
        iterable = raw_legal_actions

    legal_actions = tuple(_coerce_legal_action(action) for action in iterable)
    if not legal_actions:
        raise NoLegalActionAvailable("observation does not expose any legal actions")
    return legal_actions


def _coerce_legal_action(value: object) -> LegalAction:
    if isinstance(value, LegalAction):
        return value
    if isinstance(value, Mapping):
        return LegalAction.from_dict(value)
    if isinstance(value, str):
        return LegalAction.from_dict({"action_type": value})
    raise ControllerError("legal_actions must contain LegalAction values, mappings, or strings")


def _coerce_player_action(action: PlayerAction | Mapping[str, Any]) -> PlayerAction:
    if isinstance(action, PlayerAction):
        return action
    if isinstance(action, Mapping):
        return PlayerAction.from_dict(action)
    raise ActionSubmissionRejected(
        ActionError(
            code="invalid_submission",
            message="submitted action must be a PlayerAction or mapping",
        )
    )


def _validate_submitted_action_matches_context(
    action: PlayerAction,
    context: ActionRequestContext,
) -> None:
    if action.player_id != context.player_id:
        raise _submission_rejected(
            "wrong_player",
            "submitted action is not for the current player",
            action,
        )
    if action.seat_index != context.seat_index:
        raise _submission_rejected(
            "wrong_seat",
            "submitted action is not for the current seat",
            action,
        )
    if action.hand_id != context.hand_id or action.turn_id != context.turn_id:
        raise _submission_rejected(
            "stale_turn",
            "submitted action is not for the current turn",
            action,
        )


def _submission_rejected(
    code: str,
    message: str,
    action: PlayerAction,
) -> ActionSubmissionRejected:
    return ActionSubmissionRejected(
        ActionError(
            code=code,
            message=message,
            player_id=action.player_id,
            hand_id=action.hand_id,
            turn_id=action.turn_id,
            retry_same_player=True,
        )
    )


def _action_error_matches_context(
    action_error: ActionError | object,
    context: ActionRequestContext,
) -> bool:
    if not isinstance(action_error, ActionError):
        return True
    return (
        (action_error.player_id is None or action_error.player_id == context.player_id)
        and (action_error.hand_id is None or action_error.hand_id == context.hand_id)
        and (action_error.turn_id is None or action_error.turn_id == context.turn_id)
    )


def _same_action_context(left: ActionRequestContext, right: ActionRequestContext) -> bool:
    return (
        left.table_id == right.table_id
        and left.hand_id == right.hand_id
        and left.turn_id == right.turn_id
        and left.player_id == right.player_id
        and left.seat_index == right.seat_index
    )


def _parse_controller_type(controller_type: ControllerType | str) -> ControllerType:
    if isinstance(controller_type, ControllerType):
        return controller_type
    try:
        return ControllerType(str(controller_type))
    except ValueError as exc:
        valid_values = ", ".join(controller.value for controller in ControllerType)
        raise ValueError(f"controller_type must be one of: {valid_values}") from exc


def _require_request_action(controller: PlayerController) -> None:
    if not callable(getattr(controller, "request_action", None)):
        raise TypeError("controller must provide request_action")


def _validate_identifier(value: object, field_name: str) -> Identifier:
    if isinstance(value, bool) or value is None:
        raise ValueError(f"{field_name} must be a string or integer identifier")
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value:
        return value
    raise ValueError(f"{field_name} must be a non-empty string or integer identifier")


def _validate_seat_index(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError("seat_index must be a non-negative integer")
    return value


def _require_mapping(data: object, model_name: str) -> None:
    if not isinstance(data, Mapping):
        raise ValueError(f"{model_name} payload must be a dictionary")


def _require_keys(data: Mapping[str, Any], model_name: str, keys: tuple[str, ...]) -> None:
    missing = [key for key in keys if key not in data]
    if missing:
        missing_list = ", ".join(missing)
        raise ValueError(f"{model_name} payload missing required field(s): {missing_list}")


__all__ = [
    "ActionRequestContext",
    "ActionSubmissionRejected",
    "BotPlayerController",
    "BotStrategy",
    "BotStrategyError",
    "ControllerError",
    "ControllerRegistration",
    "ControllerRegistry",
    "ControllerType",
    "DeterministicBotPlayerController",
    "FirstLegalActionStrategy",
    "FutureAgentPlayerController",
    "HumanPlayerController",
    "NoLegalActionAvailable",
    "PendingActionError",
    "PendingHumanAction",
    "PlayerController",
    "PlayerObservation",
]
