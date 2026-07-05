from __future__ import annotations

import asyncio
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest

from mcx_poker.engine.actions import ActionError, ActionSource, ActionType, PlayerAction
from mcx_poker.engine.game_loop import (
    ActionRequestContext,
    CurrentActor,
    GameLoop,
    ValidatedAction,
    ValidationResult,
)
from mcx_poker.engine.pokerkit_adapter import CreateHandRequest, PokerKitAdapter


@dataclass(slots=True)
class ActorRef:
    seat_index: int
    player_id: str


class AdapterRejected(Exception):
    def __init__(self, action: ValidatedAction) -> None:
        super().__init__("adapter rejected action")
        self.code = "adapter_illegal_action"
        self.message = "adapter rejected action"
        self.player_id = action.player_id
        self.hand_id = action.hand_id
        self.turn_id = action.turn_id
        self.retry_same_player = True


class FakeAdapter:
    def __init__(
        self,
        *,
        active: bool = True,
        actor: ActorRef | None = None,
        reject_submissions: int = 0,
        raw_submission_value: Any | None = None,
    ) -> None:
        self.active = active
        self.actor = actor if actor is not None else ActorRef(0, "p1")
        self.reject_submissions = reject_submissions
        self.raw_submission_value = raw_submission_value
        self.submitted: list[Any] = []
        self.advances = 0
        self.settlement = {
            "hand_id": "hand-1",
            "final_stacks": {0: 210, 1: 190},
            "payoffs": {0: 10, 1: -10},
        }

    def hand_is_active(self, hand_id: str) -> bool:
        return self.active

    def get_current_actor(self, hand_id: str) -> ActorRef | None:
        return self.actor

    def advance_non_player_state(self, hand_id: str) -> None:
        self.advances += 1
        self.active = False

    def submit_action(self, validated_action: ValidatedAction) -> dict[str, Any]:
        self.submitted.append(validated_action)
        if self.reject_submissions:
            self.reject_submissions -= 1
            raise AdapterRejected(validated_action)

        self.active = False
        result = {
            "ok": True,
            "hand_id": validated_action.hand_id,
            "action": validated_action,
            "state_summary": {"is_active": False},
        }
        if self.raw_submission_value is not None:
            result["raw_state"] = self.raw_submission_value
        return result

    def get_hand_settlement(self, hand_id: str) -> dict[str, Any]:
        return {**self.settlement, "hand_id": hand_id}


class FakeObservationSystem:
    def __init__(self, raw_value: Any | None = None) -> None:
        self.raw_value = raw_value
        self.calls: list[tuple[CurrentActor, ActionRequestContext]] = []

    def build(self, actor: CurrentActor, context: ActionRequestContext) -> dict[str, Any]:
        self.calls.append((actor, context))
        observation = {
            "observer_player_id": actor.player_id,
            "observer_seat_index": actor.seat_index,
            "hand_id": actor.hand_id,
            "turn_id": actor.turn_id,
            "legal_actions": [{"action_type": "Call", "enabled": True}],
        }
        if self.raw_value is not None:
            observation["raw_state"] = self.raw_value
        return observation


class QueueController:
    def __init__(self, action_plan: list[Any] | None = None) -> None:
        self.action_plan = action_plan or [ActionType.CALL]
        self.requests: list[tuple[Any, ActionRequestContext]] = []
        self.rejections: list[ActionError] = []
        self.pending_future: asyncio.Future[Any] | None = None

    async def request_action(self, observation: Any, context: ActionRequestContext) -> PlayerAction:
        self.requests.append((observation, context))
        if self.pending_future is not None:
            return await self.pending_future

        next_action = self.action_plan.pop(0) if self.action_plan else ActionType.CALL
        if callable(next_action):
            return next_action(context)
        if isinstance(next_action, PlayerAction):
            return next_action
        return make_action(context, next_action)

    def notify_action_rejected(self, action_error: ActionError) -> None:
        self.rejections.append(action_error)


class ControllerRegistry:
    def __init__(self, controller: QueueController) -> None:
        self.controller = controller
        self.requested_players: list[str] = []

    def get_controller(self, player_id: str) -> QueueController:
        self.requested_players.append(player_id)
        return self.controller


class QueueValidator:
    def __init__(self, outcomes: list[str] | None = None) -> None:
        self.outcomes = outcomes or ["accept"]
        self.calls: list[tuple[PlayerAction, ActionRequestContext]] = []

    def validate(
        self,
        action: PlayerAction,
        context: ActionRequestContext,
    ) -> ValidationResult:
        self.calls.append((action, context))
        outcome = self.outcomes.pop(0) if self.outcomes else "accept"
        if outcome == "reject":
            return ValidationResult.rejected(
                ActionError(
                    code="amount_out_of_range",
                    message="raise amount is outside the legal range",
                    player_id=context.player_id,
                    hand_id=context.hand_id,
                    turn_id=context.turn_id,
                )
            )

        validated = ValidatedAction(
            action=action,
            normalized_type=str(action.action_type.value),
            normalized_amount=action.amount,
        )
        return ValidationResult.accepted(validated)


class TableManager:
    def __init__(self, *, status: str = "running") -> None:
        self.status = status
        self.applied_settlements: list[Any] = []
        self.next_hand_requests: list[str] = []

    def get_table_snapshot(self, table_id: str) -> dict[str, Any]:
        return {"table_id": table_id, "status": self.status}

    def apply_hand_settlement(self, settlement: Any) -> None:
        self.applied_settlements.append(settlement)

    def create_next_hand(self, table_id: str) -> dict[str, str]:
        self.next_hand_requests.append(table_id)
        return {"table_id": table_id, "hand_id": "next-hand"}


class EventLog:
    def __init__(self) -> None:
        self.events: list[dict[str, Any]] = []

    def record_hand_started(self, hand_id: str, payload: dict[str, Any] | None = None) -> None:
        self.events.append({"type": "hand_started", "hand_id": hand_id, "payload": payload or {}})

    def record_actor_requested(
        self,
        hand_id: str,
        player_id: str,
        seat_index: int,
        turn_id: str,
        payload: dict[str, Any] | None = None,
    ) -> None:
        self.events.append(
            {
                "type": "actor_requested",
                "hand_id": hand_id,
                "player_id": player_id,
                "seat_index": seat_index,
                "turn_id": turn_id,
                "payload": payload or {},
            }
        )

    def record_action_succeeded(
        self,
        hand_id: str,
        player_id: str,
        action: str,
        *,
        amount: int | float | None = None,
        seat_index: int | None = None,
        payload: dict[str, Any] | None = None,
    ) -> None:
        self.events.append(
            {
                "type": "action_succeeded",
                "hand_id": hand_id,
                "player_id": player_id,
                "action": action,
                "amount": amount,
                "seat_index": seat_index,
                "payload": payload or {},
            }
        )

    def record_action_rejected(
        self,
        hand_id: str,
        player_id: str,
        reason: str,
        *,
        attempted_action: str | None = None,
        seat_index: int | None = None,
        payload: dict[str, Any] | None = None,
    ) -> None:
        self.events.append(
            {
                "type": "action_rejected",
                "hand_id": hand_id,
                "player_id": player_id,
                "reason": reason,
                "attempted_action": attempted_action,
                "seat_index": seat_index,
                "payload": payload or {},
            }
        )

    def record_settlement(self, hand_id: str, settlement: dict[str, Any]) -> None:
        self.events.append({"type": "settlement", "hand_id": hand_id, "payload": settlement})

    def record_hand_ended(self, hand_id: str, payload: dict[str, Any] | None = None) -> None:
        self.events.append({"type": "hand_ended", "hand_id": hand_id, "payload": payload or {}})


class Gateway:
    def __init__(self) -> None:
        self.events: list[dict[str, Any]] = []

    async def broadcast_event(
        self,
        event_type: str,
        payload: Any,
        *,
        table_id: str | None = None,
    ) -> None:
        self.events.append({"type": event_type, "table_id": table_id, "payload": payload})

    async def send_action_requested(
        self,
        player_id: str,
        seat_index: int,
        payload: Any,
        table_id: str | None = None,
    ) -> None:
        self.events.append(
            {
                "type": "action_requested",
                "table_id": table_id,
                "player_id": player_id,
                "seat_index": seat_index,
                "payload": payload,
            }
        )


def make_action(
    context: ActionRequestContext,
    action_type: ActionType = ActionType.CALL,
    amount: int | None = None,
) -> PlayerAction:
    return PlayerAction(
        player_id=context.player_id,
        seat_index=context.seat_index,
        hand_id=context.hand_id,
        turn_id=context.turn_id,
        action_type=action_type,
        amount=amount,
        source=ActionSource.BOT,
    )


def build_loop(
    *,
    adapter: Any | None = None,
    observation_system: Any | None = None,
    controller: QueueController | None = None,
    validator: QueueValidator | None = None,
    table_manager: TableManager | None = None,
    event_log: EventLog | None = None,
    gateway: Gateway | None = None,
    turn_ids: list[str] | None = None,
) -> tuple[GameLoop, dict[str, Any]]:
    controller = controller or QueueController()
    services: dict[str, Any] = {
        "adapter": adapter or FakeAdapter(),
        "observation_system": observation_system or FakeObservationSystem(),
        "controller": controller,
        "registry": ControllerRegistry(controller),
        "validator": validator or QueueValidator(),
        "table_manager": table_manager or TableManager(),
        "event_log": event_log or EventLog(),
        "gateway": gateway or Gateway(),
    }
    ids = iter(turn_ids or ["turn-1", "turn-2", "turn-3", "turn-4", "turn-5", "turn-6"])
    loop = GameLoop(
        table_manager=services["table_manager"],
        adapter=services["adapter"],
        observation_system=services["observation_system"],
        controller_registry=services["registry"],
        action_validator=services["validator"],
        hand_event_log=services["event_log"],
        websocket_gateway=services["gateway"],
        turn_id_factory=lambda: next(ids),
    )
    return loop, services


@pytest.mark.asyncio
async def test_gl_t01_normal_action_progresses_hand_to_settlement() -> None:
    game_loop, services = build_loop()

    result = await game_loop.start_hand({"table_id": "table-1", "hand_id": "hand-1"})

    assert result.status == "completed"
    assert len(services["adapter"].submitted) == 1
    assert services["table_manager"].applied_settlements == [result.settlement]
    assert services["table_manager"].next_hand_requests == ["table-1"]
    assert [event["type"] for event in services["gateway"].events] == [
        "hand_started",
        "action_requested",
        "player_acted",
        "hand_ended",
    ]


@pytest.mark.asyncio
async def test_gl_t02_validator_rejection_retries_same_actor_without_adapter_submit() -> None:
    controller = QueueController(
        [lambda context: make_action(context, ActionType.RAISE_TO, 999), ActionType.CALL]
    )
    validator = QueueValidator(["reject", "accept"])
    game_loop, services = build_loop(controller=controller, validator=validator)

    result = await game_loop.start_hand({"table_id": "table-1", "hand_id": "hand-1"})

    assert result.status == "completed"
    assert len(controller.requests) == 2
    assert [request[1].seat_index for request in controller.requests] == [0, 0]
    assert [request[1].turn_id for request in controller.requests] == ["turn-1", "turn-2"]
    assert len(controller.rejections) == 1
    assert controller.rejections[0].code == "amount_out_of_range"
    assert len(services["adapter"].submitted) == 1
    assert len(validator.calls) == 2
    assert "action_succeeded" in [event["type"] for event in services["event_log"].events]


@pytest.mark.asyncio
async def test_gl_t03_adapter_rejection_retries_same_actor_without_settlement() -> None:
    controller = QueueController([ActionType.CALL, ActionType.CALL])
    adapter = FakeAdapter(reject_submissions=1)
    game_loop, services = build_loop(adapter=adapter, controller=controller)

    result = await game_loop.start_hand({"table_id": "table-1", "hand_id": "hand-1"})

    assert result.status == "completed"
    assert len(controller.requests) == 2
    assert [request[1].seat_index for request in controller.requests] == [0, 0]
    assert len(controller.rejections) == 1
    assert controller.rejections[0].code == "adapter_illegal_action"
    assert len(adapter.submitted) == 2
    assert len(services["table_manager"].applied_settlements) == 1


@pytest.mark.asyncio
async def test_gl_t04_pending_human_action_does_not_advance_or_settle() -> None:
    controller = QueueController()
    game_loop, services = build_loop(controller=controller)
    controller.pending_future = asyncio.Future()

    task = asyncio.create_task(game_loop.start_hand({"table_id": "table-1", "hand_id": "hand-1"}))
    await asyncio.sleep(0.01)

    assert len(controller.requests) == 1
    assert services["adapter"].submitted == []
    assert services["table_manager"].applied_settlements == []
    assert "hand_ended" not in [event["type"] for event in services["event_log"].events]

    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task


@pytest.mark.asyncio
async def test_gl_t05_settlement_is_applied_when_hand_is_already_inactive() -> None:
    adapter = FakeAdapter(active=False, actor=None)
    game_loop, services = build_loop(adapter=adapter)

    result = await game_loop.start_hand({"table_id": "table-1", "hand_id": "hand-1"})

    assert result.status == "completed"
    assert services["table_manager"].applied_settlements == [result.settlement]
    assert adapter.submitted == []


@pytest.mark.asyncio
async def test_gl_t06_event_order_matches_hand_actor_action_and_end() -> None:
    game_loop, services = build_loop()

    await game_loop.start_hand({"table_id": "table-1", "hand_id": "hand-1"})

    assert [event["type"] for event in services["event_log"].events] == [
        "hand_started",
        "actor_requested",
        "action_succeeded",
        "settlement",
        "hand_ended",
    ]


@pytest.mark.asyncio
async def test_gl_t07_paused_table_blocks_new_action_request_at_safe_boundary() -> None:
    table_manager = TableManager(status="paused")
    controller = QueueController()
    game_loop, services = build_loop(table_manager=table_manager, controller=controller)

    result = await game_loop.start_hand({"table_id": "table-1", "hand_id": "hand-1"})

    assert result.status == "paused"
    assert controller.requests == []
    assert services["adapter"].submitted == []
    assert table_manager.applied_settlements == []
    assert [event["type"] for event in services["event_log"].events] == ["hand_started"]


@pytest.mark.asyncio
async def test_gl_t08_reset_after_pending_action_invalidates_action_before_submit() -> None:
    table_manager = TableManager(status="running")

    def reset_then_call(context: ActionRequestContext) -> PlayerAction:
        table_manager.status = "resetting"
        return make_action(context)

    controller = QueueController([reset_then_call])
    validator = QueueValidator()
    game_loop, services = build_loop(
        controller=controller,
        validator=validator,
        table_manager=table_manager,
    )

    result = await game_loop.start_hand({"table_id": "table-1", "hand_id": "hand-1"})

    assert result.status == "reset"
    assert services["adapter"].submitted == []
    assert validator.calls == []
    assert len(controller.rejections) == 1
    assert controller.rejections[0].code == "table_reset"
    assert "action_rejected" in [event["type"] for event in services["event_log"].events]


@pytest.mark.asyncio
async def test_gl_t09_payloads_do_not_propagate_raw_runtime_objects() -> None:
    class RuntimeState:
        __module__ = "pokerkit.state"

    raw_state = RuntimeState()
    adapter = FakeAdapter(raw_submission_value=raw_state)
    observation_system = FakeObservationSystem(raw_value=raw_state)
    game_loop, services = build_loop(adapter=adapter, observation_system=observation_system)

    await game_loop.start_hand(
        {
            "table_id": "table-1",
            "hand_id": "hand-1",
            "adapter_hand_ref": raw_state,
            "hole_cards_by_seat": {0: ["As", "Kd"]},
        }
    )

    assert not contains_object(services["event_log"].events, raw_state)
    assert not contains_object(services["gateway"].events, raw_state)
    assert "As" not in repr(services["event_log"].events)
    assert "As" not in repr(services["gateway"].events)
    source = Path("src/mcx_poker/engine/game_loop.py").read_text()
    forbidden_imports = ("from " + "pokerkit", "import " + "pokerkit")
    assert all(forbidden not in source for forbidden in forbidden_imports)


@pytest.mark.asyncio
async def test_gl_t10_real_adapter_smoke_reaches_first_actor_and_settlement() -> None:
    adapter = PokerKitAdapter()
    adapter.create_hand(
        CreateHandRequest(
            hand_id="real-hand",
            seat_to_player={seat: f"p{seat}" for seat in range(6)},
            starting_stacks=(200, 200, 200, 200, 200, 200),
            button_seat_index=5,
            small_blind=1,
            big_blind=2,
            ante=0,
        )
    )
    controller = QueueController([ActionType.FOLD] * 8)
    game_loop, services = build_loop(adapter=adapter, controller=controller)

    result = await game_loop.start_hand({"table_id": "table-1", "hand_id": "real-hand"})

    assert controller.requests[0][1].seat_index == 2
    assert controller.requests[0][1].player_id == "p2"
    assert result.status == "completed"
    assert services["table_manager"].applied_settlements == [result.settlement]


def contains_object(value: Any, needle: object) -> bool:
    if value is needle:
        return True
    if isinstance(value, dict):
        return any(
            contains_object(key, needle) or contains_object(item, needle)
            for key, item in value.items()
        )
    if isinstance(value, (list, tuple, set, frozenset)):
        return any(contains_object(item, needle) for item in value)
    if hasattr(value, "__dict__"):
        return contains_object(vars(value), needle)
    return False
