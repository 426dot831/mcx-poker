from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATIC = ROOT / "src" / "mcx_poker" / "delivery" / "static"
INDEX = STATIC / "index.html"
STYLES = STATIC / "styles.css"
APP = STATIC / "app.js"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_static_frontend_files_exist() -> None:
    assert INDEX.exists()
    assert STYLES.exists()
    assert APP.exists()


def test_index_is_first_screen_six_seat_table() -> None:
    html = read(INDEX)

    assert "data-app" in html
    assert 'class="table-scene"' in html
    assert html.count('data-seat-index="') == 6
    assert "data-board-cards" in html
    assert "data-pot-summary" in html
    assert "data-connection-status" in html
    assert "landing" not in html.lower()


def test_index_contains_controls_and_action_bar_contract() -> None:
    html = read(INDEX)

    for command in ("start", "pause", "resume", "reset"):
        assert f'data-command="{command}"' in html

    for action in ("Fold", "Check", "Call", "RaiseTo", "AllIn"):
        assert f'data-action="{action}"' in html

    assert 'name="raise_to_amount"' in html
    assert "Table Controls" in html
    assert "Your Hand" in html
    assert "mcx-poker = mcx_poker.delivery.api:main" in html


def test_styles_define_fixed_desktop_table_layout() -> None:
    css = read(STYLES)

    for selector in (".seat-0", ".seat-1", ".seat-2", ".seat-3", ".seat-4", ".seat-5"):
        assert selector in css

    assert "min-width: 960px" in css
    assert ".table-felt" in css
    assert ".action-bar" in css
    assert ".card.back" in css


def test_frontend_does_not_import_pokerkit_or_calculate_winners() -> None:
    combined = f"{read(INDEX)}\n{read(STYLES)}\n{read(APP)}".lower()

    assert "pokerkit" not in combined
    assert "winner" not in combined
    assert "evaluate" not in combined


def run_node(script: str) -> dict[str, object]:
    node = shutil.which("node")
    assert node is not None, "node is required for frontend helper tests"

    completed = subprocess.run(
        [node, "-e", script],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    )
    return json.loads(completed.stdout)


def test_action_payload_helper_uses_pending_turn_and_raise_to_total() -> None:
    result = run_node(
        """
        const poker = require("./src/mcx_poker/delivery/static/app.js");
        const state = poker.createInitialState({ playerId: "p1", seatIndex: 3 });
        poker.applyServerEvent(state, {
          type: "action_requested",
          payload: {
            hand_id: "hand-7",
            turn_id: "turn-11",
            player_id: "p1",
            seat_index: 3,
            observation: {
              legal_actions: ["Fold", "Call", { action_type: "RaiseTo", min_total: 80 }]
            }
          }
        });
        const payload = poker.buildActionPayload(state, "RaiseTo", "120");
        console.log(JSON.stringify(payload));
        """,
    )

    assert result == {
        "player_id": "p1",
        "seat_index": 3,
        "hand_id": "hand-7",
        "turn_id": "turn-11",
        "action_type": "RaiseTo",
        "amount": 120,
    }


def test_all_in_payload_has_no_amount() -> None:
    result = run_node(
        """
        const poker = require("./src/mcx_poker/delivery/static/app.js");
        const state = poker.createInitialState({ playerId: "hero", seatIndex: 0 });
        poker.applyServerEvent(state, {
          type: "action_requested",
          payload: {
            hand_id: "h1",
            turn_id: "t1",
            player_id: "hero",
            seat_index: 0,
            legal_actions: ["AllIn"]
          }
        });
        const payload = poker.buildClientEvent(state, "AllIn", "999");
        console.log(JSON.stringify(payload));
        """,
    )

    assert result["event_type"] == "submit_action"
    payload = result["payload"]
    assert isinstance(payload, dict)
    assert payload["action_type"] == "AllIn"
    assert "amount" not in payload


def test_action_rejected_keeps_pending_turn_and_table_state() -> None:
    result = run_node(
        """
        const poker = require("./src/mcx_poker/delivery/static/app.js");
        const state = poker.createInitialState({ playerId: "hero", seatIndex: 0 });
        poker.applyServerEvent(state, {
          type: "table_snapshot",
          payload: { hand_id: "h1", pot_total: 30, seats: [] }
        });
        poker.applyServerEvent(state, {
          type: "action_requested",
          payload: {
            hand_id: "h1",
            turn_id: "t1",
            player_id: "hero",
            seat_index: 0,
            legal_actions: ["Call", "RaiseTo"]
          }
        });
        state.awaitingConfirmation = true;
        poker.applyServerEvent(state, {
          type: "action_rejected",
          payload: { code: "stale_turn", message: "turn expired" }
        });
        console.log(JSON.stringify({
          handId: state.tableSnapshot.hand_id,
          potTotal: state.tableSnapshot.pot_total,
          pendingTurn: state.pendingAction.turn_id,
          pendingActions: state.pendingAction.legal_actions,
          awaiting: state.awaitingConfirmation,
          error: state.lastError
        }));
        """,
    )

    assert result == {
        "handId": "h1",
        "potTotal": 30,
        "pendingTurn": "t1",
        "pendingActions": ["Call", "RaiseTo"],
        "awaiting": False,
        "error": "turn expired",
    }


def test_player_acted_confirmation_is_required_before_pending_turn_clears() -> None:
    result = run_node(
        """
        const poker = require("./src/mcx_poker/delivery/static/app.js");
        const state = poker.createInitialState({ playerId: "hero", seatIndex: 0 });
        poker.applyServerEvent(state, {
          type: "action_requested",
          payload: {
            hand_id: "h1",
            turn_id: "t1",
            player_id: "hero",
            seat_index: 0,
            legal_actions: ["Call"]
          }
        });
        const before = state.pendingAction && state.pendingAction.turn_id;
        poker.applyServerEvent(state, {
          type: "player_acted",
          payload: { player_id: "hero", turn_id: "t1", action_type: "Call" }
        });
        console.log(JSON.stringify({
          before,
          after: state.pendingAction,
          lastAction: state.lastPlayerActed.action_type
        }));
        """,
    )

    assert result["before"] == "t1"
    assert result["after"] is None
    assert result["lastAction"] == "Call"
