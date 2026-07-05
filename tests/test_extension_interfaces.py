from __future__ import annotations

import ast
import json
import sys
from pathlib import Path
from typing import Any

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from mcx_poker.extensions import (  # noqa: E402
    ActionRequestContext,
    ActionType,
    ControllerRegistry,
    DeterministicLLMClient,
    ExtensionInputRejected,
    GTOPlayerController,
    HandEvent,
    LegalAction,
    LLMPlayerController,
    PlayerAction,
    PlayerObservation,
    StrategyQuery,
    VisibleSeat,
    validate_extension_input,
)


def _observation(
    *,
    legal_actions: tuple[LegalAction, ...] = (LegalAction(ActionType.CHECK),),
) -> PlayerObservation:
    seats = (
        VisibleSeat(
            seat_index=0,
            player_id="p1",
            player_name="Alice",
            stack=1_000,
            current_bet=0,
            status="active",
            hole_card_count=2,
        ),
        VisibleSeat(
            seat_index=1,
            player_id="p2",
            player_name="Bob",
            stack=980,
            current_bet=20,
            status="active",
            hole_card_count=2,
        ),
        VisibleSeat(seat_index=2),
        VisibleSeat(seat_index=3),
        VisibleSeat(seat_index=4),
        VisibleSeat(seat_index=5),
    )
    return PlayerObservation(
        observer_player_id="p1",
        observer_seat_index=0,
        table_id="table-1",
        hand_id="hand-1",
        turn_id="turn-1",
        is_actor=True,
        button_seat_index=5,
        own_hole_cards=("As", "Ah"),
        board_cards=("2c", "7d", "Jh"),
        visible_seats=seats,
        pot_summary={"total": 40},
        bet_summary={"to_call": 20},
        visible_action_history=(
            HandEvent(
                event_id="event-1",
                hand_id="hand-1",
                event_type="blind_posted",
                payload={"seat_index": 1, "amount": 20},
            ),
        ),
        legal_actions=legal_actions,
    )


def test_fake_future_controller_observation_to_action_and_registry() -> None:
    observation = _observation(
        legal_actions=(
            LegalAction(ActionType.CALL),
            LegalAction(ActionType.FOLD),
        )
    )
    controller = LLMPlayerController(client=DeterministicLLMClient("Call"))
    registry = ControllerRegistry()
    registry.register("p1", controller)

    action = registry.request_action(
        "p1",
        observation,
        ActionRequestContext(
            table_id="table-1",
            hand_id="hand-1",
            turn_id="turn-1",
            player_id="p1",
            seat_index=0,
        ),
    )

    assert isinstance(action, PlayerAction)
    assert action.action_type is ActionType.CALL
    assert action.player_id == "p1"
    assert action.hand_id == "hand-1"
    assert action.turn_id == "turn-1"


def test_fake_llm_controller_initializes_without_llm_dependency() -> None:
    controller = LLMPlayerController()
    observation = _observation()

    action = controller.request_action(observation)

    assert isinstance(controller.client, DeterministicLLMClient)
    assert action.action_type is ActionType.CHECK
    assert controller.last_error is None


def test_fake_solver_failure_falls_back_and_game_loop_continues() -> None:
    class FailingSolver:
        def solve(self, query: StrategyQuery) -> Any:
            raise RuntimeError("solver unavailable")

    def ordinary_game_loop_step(controller: GTOPlayerController) -> PlayerAction:
        return controller.request_action(_observation())

    controller = GTOPlayerController(solver_client=FailingSolver())

    action = ordinary_game_loop_step(controller)

    assert action.action_type is ActionType.CHECK
    assert isinstance(controller.last_error, RuntimeError)


def test_extension_interfaces_do_not_import_pokerkit() -> None:
    source_path = SRC_ROOT / "mcx_poker" / "extensions" / "interfaces.py"
    tree = ast.parse(source_path.read_text(encoding="utf-8"))
    imported_roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".", 1)[0])

    assert "pokerkit" not in imported_roots


def test_extension_input_payload_omits_hidden_information() -> None:
    observation = _observation()

    payload = observation.to_extension_payload()
    serialized = json.dumps(payload, sort_keys=True)

    assert "As" in serialized
    assert "Ah" in serialized
    assert "hole_card_count" in serialized
    assert "opponent_hole_cards" not in serialized
    assert "undealt_cards" not in serialized
    assert "deck_order" not in serialized
    assert "pokerkit" not in serialized.lower()
    assert "Ks" not in serialized
    assert "Kd" not in serialized
    with pytest.raises(ExtensionInputRejected):
        validate_extension_input({"opponent_hole_cards": ("Ks", "Kd")})
