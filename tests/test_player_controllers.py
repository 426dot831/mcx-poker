from __future__ import annotations

import ast
import asyncio
import json
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path

import pytest

from mcx_poker.engine.actions import (
    ActionError,
    ActionSource,
    ActionType,
    LegalAction,
    PlayerAction,
)
from mcx_poker.players import (
    ActionRequestContext,
    ActionSubmissionRejected,
    BotPlayerController,
    ControllerRegistry,
    ControllerType,
    FutureAgentPlayerController,
    HumanPlayerController,
    NoLegalActionAvailable,
    PlayerController,
    PlayerObservation,
)


@dataclass(frozen=True, slots=True)
class FakeObservation:
    observer_player_id: str = "player-1"
    observer_seat_index: int = 0
    table_id: str = "table-1"
    hand_id: str = "hand-1"
    turn_id: str = "turn-1"
    legal_actions: tuple[LegalAction, ...] = field(
        default_factory=lambda: (LegalAction(ActionType.CHECK),)
    )


def _context(
    *,
    turn_id: str = "turn-1",
    player_id: str = "player-1",
    seat_index: int = 0,
) -> ActionRequestContext:
    return ActionRequestContext(
        table_id="table-1",
        hand_id="hand-1",
        turn_id=turn_id,
        player_id=player_id,
        seat_index=seat_index,
    )


def _action(
    action_type: ActionType,
    *,
    turn_id: str = "turn-1",
    player_id: str = "player-1",
    seat_index: int = 0,
    source: ActionSource = ActionSource.UNKNOWN,
) -> PlayerAction:
    return PlayerAction(
        player_id=player_id,
        seat_index=seat_index,
        hand_id="hand-1",
        turn_id=turn_id,
        action_type=action_type,
        source=source,
    )


async def _cancel_waiter(waiter: asyncio.Task[PlayerAction]) -> None:
    waiter.cancel()
    with pytest.raises(asyncio.CancelledError):
        await waiter


async def test_bot_returns_legal_player_action_from_fake_observation() -> None:
    observation = FakeObservation(
        legal_actions=(
            LegalAction(ActionType.FOLD, enabled=False),
            LegalAction(ActionType.CALL),
        )
    )
    bot = BotPlayerController()

    action = await bot.request_action(observation)

    assert isinstance(action, PlayerAction)
    assert action.action_type is ActionType.CALL
    assert action.player_id == "player-1"
    assert action.seat_index == 0
    assert action.hand_id == "hand-1"
    assert action.turn_id == "turn-1"
    assert action.source is ActionSource.BOT


async def test_bot_without_enabled_legal_action_returns_controlled_error() -> None:
    bot = BotPlayerController()
    observation = FakeObservation(legal_actions=(LegalAction(ActionType.CHECK, enabled=False),))

    with pytest.raises(NoLegalActionAvailable, match="enabled legal action"):
        await bot.request_action(observation)


async def test_bot_strategy_illegal_action_is_not_replaced_with_fallback() -> None:
    class IllegalStrategy:
        def select_action(
            self,
            observation: PlayerObservation,
            context: ActionRequestContext,
            legal_actions: Sequence[LegalAction],
        ) -> PlayerAction:
            del observation, context, legal_actions
            return _action(ActionType.FOLD, source=ActionSource.BOT)

    bot = BotPlayerController(strategy=IllegalStrategy())
    observation = FakeObservation(legal_actions=(LegalAction(ActionType.CHECK),))

    action = await bot.request_action(observation)

    assert action.action_type is ActionType.FOLD
    assert action.action_type not in {legal.action_type for legal in observation.legal_actions}


async def test_human_controller_registers_pending_turn_and_submit_wakes_waiter() -> None:
    controller = HumanPlayerController()
    context = _context()
    waiter = asyncio.create_task(controller.request_action(FakeObservation(), context))
    await asyncio.sleep(0)

    assert controller.pending_context == context
    assert controller.pending_turn_id == "turn-1"

    submitted = await controller.submit_action(_action(ActionType.CHECK))
    action = await asyncio.wait_for(waiter, timeout=1)

    assert action == submitted
    assert action.source is ActionSource.HUMAN


async def test_human_controller_rejects_stale_turn_submission() -> None:
    controller = HumanPlayerController()
    waiter = asyncio.create_task(controller.request_action(FakeObservation(), _context()))
    await asyncio.sleep(0)

    with pytest.raises(ActionSubmissionRejected) as exc_info:
        await controller.submit_action(_action(ActionType.CHECK, turn_id="turn-old"))

    assert exc_info.value.action_error.code == "stale_turn"
    assert controller.pending_turn_id == "turn-1"
    await _cancel_waiter(waiter)


async def test_human_controller_rejects_non_current_player_or_seat() -> None:
    controller = HumanPlayerController()
    waiter = asyncio.create_task(controller.request_action(FakeObservation(), _context()))
    await asyncio.sleep(0)

    with pytest.raises(ActionSubmissionRejected) as wrong_player:
        await controller.submit_action(_action(ActionType.CHECK, player_id="player-2"))
    with pytest.raises(ActionSubmissionRejected) as wrong_seat:
        await controller.submit_action(_action(ActionType.CHECK, seat_index=1))

    assert wrong_player.value.action_error.code == "wrong_player"
    assert wrong_seat.value.action_error.code == "wrong_seat"
    await _cancel_waiter(waiter)


async def test_human_controller_rejection_is_recorded_and_keeps_same_pending_turn() -> None:
    controller = HumanPlayerController()
    context = _context()
    waiter = asyncio.create_task(controller.request_action(FakeObservation(), context))
    await asyncio.sleep(0)

    first_action = await controller.submit_action(_action(ActionType.CHECK))
    assert await waiter == first_action

    error = ActionError(
        code="action_not_available",
        message="Check is not currently available",
        player_id="player-1",
        hand_id="hand-1",
        turn_id="turn-1",
        retry_same_player=True,
    )
    await controller.notify_action_rejected(error)

    assert controller.last_action_error == error
    assert controller.pending_context == context

    retry_waiter = asyncio.create_task(controller.request_action(FakeObservation(), context))
    await asyncio.sleep(0)
    retry_action = await controller.submit_action(_action(ActionType.CALL))

    assert await asyncio.wait_for(retry_waiter, timeout=1) == retry_action
    assert retry_action.action_type is ActionType.CALL


async def test_game_loop_can_use_fake_async_controller_through_registry() -> None:
    class FakeController:
        async def request_action(
            self,
            observation: PlayerObservation,
            action_request_context: ActionRequestContext | None = None,
        ) -> PlayerAction:
            del observation, action_request_context
            return _action(ActionType.CHECK)

        async def notify_action_rejected(self, action_error: object) -> None:
            return None

        async def notify_hand_started(self, hand_context: object) -> None:
            return None

        async def notify_hand_ended(self, result_summary: object) -> None:
            return None

    controller = FakeController()
    registry = ControllerRegistry()
    registry.register("player-1", controller, seat_index=0, controller_type=ControllerType.BOT)

    action = await registry.request_action("player-1", FakeObservation(), _context())
    by_seat = registry.get_by_seat_index(0)

    assert isinstance(controller, PlayerController)
    assert by_seat is controller
    assert action.action_type is ActionType.CHECK
    assert registry.get_registration_by_player_id("player-1").controller_type is ControllerType.BOT


async def test_controller_outputs_serialize_without_pokerkit_objects() -> None:
    bot = BotPlayerController()
    action = await bot.request_action(FakeObservation())
    context = _context()
    payload = {
        "action": action.to_dict(),
        "context": context.to_dict(),
        "future_agent_type": FutureAgentPlayerController.controller_type.value,
    }

    serialized = json.dumps(payload, sort_keys=True)

    assert "pokerkit" not in serialized.casefold()
    assert "<" not in serialized

    source_path = Path(__file__).resolve().parents[1] / "src" / "mcx_poker" / "players"
    tree = ast.parse((source_path / "controllers.py").read_text(encoding="utf-8"))
    imported_roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".", 1)[0])

    assert "pokerkit" not in imported_roots
