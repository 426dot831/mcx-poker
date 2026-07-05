from __future__ import annotations

import ast
import json
from pathlib import Path
from typing import Any

from mcx_poker.history import EventType, EventVisibility, HandEvent
from mcx_poker.observation import build_player_observation

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"


HOLE_CARDS_BY_SEAT = {
    0: ("As", "Ah"),
    1: ("Ks", "Kd"),
    2: ("Qs", "Qd"),
    3: ("Js", "Jd"),
    4: ("Ts", "Td"),
    5: ("9s", "9d"),
}


def table_snapshot(seat_count: int = 6) -> dict[str, Any]:
    return {
        "table_id": "table-1",
        "status": "running",
        "current_hand_id": "hand-1",
        "button_seat_index": 5,
        "seats": [
            {
                "seat_index": index,
                "player_id": f"p{index}",
                "player_name": f"Player {index}",
                "stack": 1_000 - index * 10,
                "status": "in_hand",
            }
            for index in range(seat_count)
        ],
    }


def state_summary(**overrides: Any) -> dict[str, Any]:
    summary: dict[str, Any] = {
        "hand_id": "hand-1",
        "turn_id": "turn-1",
        "current_actor": {"seat_index": 0, "player_id": "p0"},
        "board_cards": ("2c", "7d", "Jh"),
        "stacks": {index: 1_000 - index * 10 for index in range(6)},
        "bets": {0: 0, 1: 20, 2: 0, 3: 0, 4: 0, 5: 0},
        "pot_summary": {
            "total_amount": 40,
            "pots": [{"amount": 40, "eligible_seats": [0, 1]}],
        },
        "hole_cards_by_seat": HOLE_CARDS_BY_SEAT,
        "shown_cards_by_seat": {},
        "legal_action_boundaries": {
            "fold": {
                "action_type": "Fold",
                "enabled": True,
            },
            "check": {
                "action_type": "Check",
                "enabled": False,
                "reason_if_disabled": "call_required",
            },
            "call": {
                "action_type": "Call",
                "enabled": True,
                "amount_fixed": 20,
            },
            "raise_to": {
                "action_type": "RaiseTo",
                "enabled": True,
                "amount_min": 40,
                "amount_max": 200,
            },
            "all_in": {
                "action_type": "AllIn",
                "enabled": True,
                "amount_fixed": 1_000,
            },
            "call_amount": 20,
            "min_raise_to": 40,
            "max_raise_to": 200,
        },
    }
    summary.update(overrides)
    return summary


def test_obs_t01_observer_only_receives_own_hole_cards() -> None:
    observation = build_player_observation(
        table_snapshot(),
        state_summary(),
        observer_player_id="p0",
    )
    serialized = json.dumps(observation.to_dict(), sort_keys=True)

    assert observation.own_hole_cards == ("As", "Ah")
    assert "As" in serialized
    assert "Ah" in serialized
    assert "Ks" not in serialized
    assert "Kd" not in serialized
    assert "Qs" not in serialized
    assert "Qd" not in serialized


def test_obs_t02_opponent_unshown_hole_cards_are_counts_only() -> None:
    observation = build_player_observation(
        table_snapshot(),
        state_summary(),
        observer_player_id="p0",
    )
    opponent = observation.visible_seats[1]
    opponent_payload = opponent.to_dict()

    assert opponent.hole_card_count == 2
    assert opponent.shown_cards == ()
    assert "hole_cards" not in opponent_payload


def test_obs_t03_board_cards_are_consistent_for_all_observers() -> None:
    actor_observation = build_player_observation(
        table_snapshot(),
        state_summary(),
        observer_player_id="p0",
    )
    other_observation = build_player_observation(
        table_snapshot(),
        state_summary(),
        observer_player_id="p3",
    )

    assert actor_observation.board_cards == ("2c", "7d", "Jh")
    assert other_observation.board_cards == actor_observation.board_cards


def test_obs_t04_current_actor_receives_legal_actions() -> None:
    observation = build_player_observation(
        table_snapshot(),
        state_summary(),
        observer_player_id="p0",
    )
    actions = {action.action_type.value: action for action in observation.legal_actions}
    websocket_payload = observation.to_websocket_payload()

    assert observation.is_actor is True
    assert actions["Call"].amount_fixed == 20
    assert actions["RaiseTo"].amount_min == 40
    observation_payload = websocket_payload["observation"]
    assert isinstance(observation_payload, dict)
    assert observation_payload["legal_actions"] == websocket_payload["legal_actions"]


def test_obs_t05_non_actor_receives_no_submit_actions() -> None:
    observation = build_player_observation(
        table_snapshot(),
        state_summary(),
        observer_player_id="p2",
    )

    assert observation.is_actor is False
    assert observation.legal_actions == ()
    assert observation.to_dict()["legal_actions"] == []


def test_obs_t06_showdown_cards_appear_only_after_public_reveal() -> None:
    before_reveal = build_player_observation(
        table_snapshot(),
        state_summary(),
        observer_player_id="p0",
    )
    showdown = HandEvent(
        hand_id="hand-1",
        event_type=EventType.SHOWDOWN,
        public_payload={"players": [{"player_id": "p1", "hole_cards": ["Ks", "Kd"]}]},
    )
    after_reveal = build_player_observation(
        table_snapshot(),
        state_summary(),
        [showdown],
        observer_player_id="p0",
    )

    assert before_reveal.visible_seats[1].shown_cards == ()
    assert after_reveal.visible_seats[1].shown_cards == ("Ks", "Kd")
    assert after_reveal.visible_seats[2].shown_cards == ()


def test_obs_t07_serialized_observation_has_no_pokerkit_runtime_objects() -> None:
    class PokerKitState:
        __module__ = "pokerkit.state"

    summary = state_summary(raw_state=PokerKitState())
    observation = build_player_observation(
        table_snapshot(),
        summary,
        observer_player_id="p0",
    )
    serialized = observation.to_json()

    assert "pokerkit" not in serialized.casefold()
    assert "PokerKitState" not in serialized
    assert "<" not in serialized

    source_path = SRC_ROOT / "mcx_poker" / "observation" / "builder.py"
    tree = ast.parse(source_path.read_text(encoding="utf-8"))
    imported_roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".", 1)[0])
    assert "pokerkit" not in imported_roots


def test_obs_t08_visible_seats_are_always_fixed_to_six() -> None:
    observation = build_player_observation(
        table_snapshot(seat_count=2),
        state_summary(hole_cards_by_seat={0: ("As", "Ah"), 1: ("Ks", "Kd")}),
        observer_player_id="p0",
    )

    assert len(observation.visible_seats) == 6
    assert [seat.seat_index for seat in observation.visible_seats] == [0, 1, 2, 3, 4, 5]
    assert observation.visible_seats[5].status == "empty"


def test_obs_t09_visible_action_history_contains_public_events_only() -> None:
    public_action = HandEvent(
        hand_id="hand-1",
        event_type=EventType.ACTION_SUCCEEDED,
        actor_player_id="p1",
        actor_seat_index=1,
        public_payload={"action": "Call", "amount": 20},
    )
    private_rejection = HandEvent(
        hand_id="hand-1",
        event_type=EventType.ACTION_REJECTED,
        actor_player_id="p0",
        actor_seat_index=0,
        private_payload={"reason": "not your turn", "attempted_action": "RaiseTo"},
        visibility=EventVisibility.PLAYER_SCOPED,
    )

    observation = build_player_observation(
        table_snapshot(),
        state_summary(),
        [public_action, private_rejection],
        observer_player_id="p0",
    )

    assert [event["event_type"] for event in observation.visible_action_history] == [
        "action_succeeded"
    ]
    serialized_history = json.dumps(observation.to_dict()["visible_action_history"])
    assert "not your turn" not in serialized_history
    assert "attempted_action" not in serialized_history
