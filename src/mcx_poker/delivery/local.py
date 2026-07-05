"""Local MVP application composition.

This module wires the platform modules into a playable local prototype. It is
the composition root only; poker rules still enter exclusively through the
PokerKit adapter.
"""

from __future__ import annotations

import asyncio
from collections.abc import Mapping
from typing import Any, cast

from mcx_poker.delivery.websocket import WebSocketGateway
from mcx_poker.engine.game_loop import GameLoop
from mcx_poker.engine.pokerkit_adapter import PokerKitAdapter
from mcx_poker.engine.validator import ActionContext, validate_action
from mcx_poker.history import HandEventLog
from mcx_poker.observation import build_player_observation
from mcx_poker.players import BotPlayerController, ControllerRegistry, HumanPlayerController
from mcx_poker.table import (
    DEFAULT_STARTING_STACK,
    DEFAULT_TABLE_ID,
    ControllerType,
    TableManager,
    TableSnapshot,
    TableStatus,
)


class LocalObservationSystem:
    """Adapter between GameLoop actor requests and observation builder inputs."""

    def __init__(
        self,
        table_manager: TableManager,
        adapter: PokerKitAdapter,
        event_log: HandEventLog,
    ) -> None:
        self.table_manager = table_manager
        self.adapter = adapter
        self.event_log = event_log

    def build(self, actor: Any, context: Any) -> Any:
        table_snapshot = self.table_manager.get_table_snapshot(str(context.table_id))
        state_summary = self.adapter.get_state_summary(str(context.hand_id))
        public_events = self.event_log.list_public_events(str(context.hand_id))
        return build_player_observation(
            table_snapshot,
            state_summary,
            public_events,
            observer_player_id=actor.player_id,
            observer_seat_index=actor.seat_index,
            turn_id=actor.turn_id,
        )


class LocalActionValidator:
    """Supplies the current legal-action and table context to validate_action."""

    def __init__(self, table_manager: TableManager, adapter: PokerKitAdapter) -> None:
        self.table_manager = table_manager
        self.adapter = adapter

    def validate(self, action: Any, context: Any) -> Any:
        state_summary = self.adapter.get_state_summary(str(context.hand_id))
        validation_context = ActionContext(
            table_id=context.table_id,
            hand_id=context.hand_id,
            turn_id=context.turn_id,
            actor_player_id=context.player_id,
            actor_seat_index=context.seat_index,
        )
        table_snapshot = self.table_manager.get_table_snapshot(str(context.table_id))
        return validate_action(
            action,
            validation_context,
            state_summary.legal_action_boundaries,
            table_snapshot,
        )


class LocalPokerService:
    """Single-table local MVP service consumed by FastAPI and WebSocket."""

    def __init__(self) -> None:
        self.adapter = PokerKitAdapter()
        self.table_manager = TableManager(adapter=cast(Any, self.adapter))
        self.event_log = HandEventLog()
        self.human_controller = HumanPlayerController()
        self.controller_registry = ControllerRegistry()
        self.observation_system = LocalObservationSystem(
            self.table_manager,
            self.adapter,
            self.event_log,
        )
        self.action_validator = LocalActionValidator(self.table_manager, self.adapter)
        self.websocket_gateway = WebSocketGateway(table_manager=self, human_controller=self)
        self.game_loop = GameLoop(
            table_manager=cast(Any, self.table_manager),
            adapter=cast(Any, self.adapter),
            observation_system=self.observation_system,
            controller_registry=cast(Any, self.controller_registry),
            action_validator=self.action_validator,
            hand_event_log=self.event_log,
            websocket_gateway=self.websocket_gateway,
        )
        self._loop_task: asyncio.Task[Any] | None = None
        self.initialize_table()
        self._seat_default_players()

    def initialize_table(self, config: Mapping[str, Any] | None = None) -> dict[str, Any]:
        snapshot = self.table_manager.initialize_table(config)
        self.controller_registry = ControllerRegistry()
        if hasattr(self, "game_loop"):
            cast(Any, self.game_loop).controller_registry = self.controller_registry
        self._loop_task = None
        return self._public_snapshot(snapshot)

    def seat_player(
        self,
        seat_index: int,
        player_name: str,
        controller_type: str,
        starting_stack: int,
    ) -> dict[str, Any]:
        snapshot = self.table_manager.seat_player(
            seat_index,
            player_name,
            controller_type,
            starting_stack,
        )
        seat = snapshot.seats[seat_index]
        if seat.player_id is not None:
            self._register_controller(seat.player_id, seat.seat_index, controller_type)
        return self._public_snapshot(snapshot)

    async def start_table(self, table_id: str = DEFAULT_TABLE_ID) -> dict[str, Any]:
        snapshot = self.table_manager.get_table_snapshot(table_id)
        if snapshot.status is TableStatus.IDLE:
            snapshot = self.table_manager.start_table(table_id)
        if snapshot.current_hand_id is None:
            self.table_manager.create_next_hand(table_id)
        self._ensure_loop_running()
        return self.get_table(table_id)

    def pause_table(self, table_id: str = DEFAULT_TABLE_ID) -> dict[str, Any]:
        return self._public_snapshot(self.table_manager.pause_table(table_id))

    async def resume_table(self, table_id: str = DEFAULT_TABLE_ID) -> dict[str, Any]:
        snapshot = self.table_manager.resume_table(table_id)
        self._ensure_loop_running()
        return self._public_snapshot(snapshot)

    async def reset_table(self, table_id: str = DEFAULT_TABLE_ID) -> dict[str, Any]:
        if self._loop_task is not None:
            self._loop_task.cancel()
            self._loop_task = None
        await self.human_controller.notify_hand_ended({"reason": "table_reset"})
        snapshot = self.table_manager.reset_table(table_id)
        self._seat_default_players()
        return self._public_snapshot(snapshot)

    def get_table(self, table_id: str = DEFAULT_TABLE_ID) -> dict[str, Any]:
        return self._public_snapshot(self.table_manager.get_table_snapshot(table_id))

    async def submit_action(self, action: Mapping[str, Any]) -> dict[str, Any]:
        submitted = await self.human_controller.submit_action(action)
        return {"ok": True, "action": submitted.to_dict()}

    async def invalidate_pending_actions(self, table_id: str) -> None:
        del table_id
        await self.human_controller.notify_hand_ended({"reason": "table_reset"})

    async def on_table_paused(self, table_id: str) -> None:
        del table_id

    def _seat_default_players(self) -> None:
        snapshot = self.table_manager.get_table_snapshot()
        if any(seat.player_id is not None for seat in snapshot.seats):
            return
        self.table_manager.seat_player(
            0,
            player_id="hero",
            player_name="Hero",
            controller_type=ControllerType.HUMAN,
            starting_stack=DEFAULT_STARTING_STACK,
        )
        self.controller_registry.register(
            "hero",
            self.human_controller,
            seat_index=0,
            controller_type="human",
        )
        for seat_index in range(1, 6):
            player_id = f"bot-{seat_index}"
            self.table_manager.seat_player(
                seat_index,
                player_id=player_id,
                player_name=f"Bot {seat_index}",
                controller_type=ControllerType.BOT,
                starting_stack=DEFAULT_STARTING_STACK,
            )
            self._register_controller(player_id, seat_index, "bot")

    def _register_controller(
        self,
        player_id: str,
        seat_index: int,
        controller_type: str,
    ) -> None:
        normalized_type = str(getattr(controller_type, "value", controller_type))
        controller = self.human_controller if normalized_type == "human" else BotPlayerController()
        self.controller_registry.register(
            player_id,
            controller,
            seat_index=seat_index,
            controller_type=normalized_type,
        )

    def _ensure_loop_running(self) -> None:
        if self._loop_task is not None and not self._loop_task.done():
            return
        context = self.table_manager.get_table_snapshot().current_hand
        if context is None:
            return
        self._loop_task = asyncio.create_task(self._run_table_loop())

    async def _run_table_loop(self) -> None:
        while True:
            snapshot = self.table_manager.get_table_snapshot()
            if snapshot.status is not TableStatus.RUNNING or snapshot.current_hand is None:
                return
            result = await self.game_loop.start_hand(snapshot.current_hand)
            if result.status != "completed":
                return

    def _public_snapshot(self, snapshot: TableSnapshot) -> dict[str, Any]:
        payload = snapshot.to_dict()
        hand_id = snapshot.current_hand_id
        if hand_id is not None:
            state_summary = self.adapter.get_state_summary(hand_id)
            payload["current_actor"] = (
                None
                if state_summary.current_actor is None
                else {
                    "seat_index": state_summary.current_actor.seat_index,
                    "player_id": state_summary.current_actor.player_id,
                }
            )
            payload["board_cards"] = list(state_summary.board_cards)
            payload["board"] = list(state_summary.board_cards)
            payload["pot_total"] = state_summary.pot_summary.total_amount
            payload["pot_summary"] = {
                "total_amount": state_summary.pot_summary.total_amount,
                "pots": [
                    {
                        "index": pot.index,
                        "amount": pot.amount,
                        "eligible_seats": list(pot.eligible_seats),
                    }
                    for pot in state_summary.pot_summary.pots
                ],
            }
            payload["bets"] = dict(state_summary.bets)
            payload["stacks"] = dict(state_summary.stacks)
            seats = payload.get("seats")
            if isinstance(seats, list):
                for seat in seats:
                    if isinstance(seat, dict):
                        seat_index = seat.get("seat_index")
                        if isinstance(seat_index, int) and seat_index in state_summary.stacks:
                            seat["stack"] = state_summary.stacks[seat_index]
                        if isinstance(seat_index, int) and seat_index in state_summary.bets:
                            seat["current_bet"] = state_summary.bets[seat_index]
                            seat["hole_card_count"] = 2
        return payload


def create_local_service() -> LocalPokerService:
    return LocalPokerService()


__all__ = [
    "LocalActionValidator",
    "LocalObservationSystem",
    "LocalPokerService",
    "create_local_service",
]
