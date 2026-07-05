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

from mcx_poker.table import (  # noqa: E402
    DEFAULT_MIN_ACTIVE_PLAYERS,
    DEFAULT_STARTING_STACK,
    SEAT_COUNT,
    CreateHandRequest,
    HandSettlement,
    HandSettlementMismatchError,
    InvalidStackError,
    PlayerAlreadySeatedError,
    SeatNotFoundError,
    SeatOccupiedError,
    SeatStatus,
    TableManager,
    TableStateConflictError,
    TableStatus,
)


class PrivateHandRef:
    def __init__(self) -> None:
        self.deck = ("As", "Kd")
        self.private_hole_cards = {"p2": ("7c", "7d")}
        self.secret_marker = "adapter-secret"


class FakeHandAdapter:
    def __init__(self) -> None:
        self.requests: list[CreateHandRequest] = []

    def create_hand(self, request: CreateHandRequest) -> PrivateHandRef:
        self.requests.append(request)
        return PrivateHandRef()


def make_manager() -> tuple[TableManager, FakeHandAdapter]:
    adapter = FakeHandAdapter()
    manager = TableManager(adapter=adapter)
    manager.initialize_table()
    return manager, adapter


def seat_two_players(
    manager: TableManager,
    *,
    seats: tuple[int, int] = (0, 1),
) -> None:
    manager.seat_player(
        seats[0],
        player_id="p1",
        player_name="Alice",
        controller_type="human",
    )
    manager.seat_player(
        seats[1],
        player_id="p2",
        player_name="Bob",
        controller_type="bot",
    )


def test_initialize_table_creates_fixed_six_empty_seats() -> None:
    manager = TableManager(adapter=FakeHandAdapter())

    snapshot = manager.initialize_table()

    assert snapshot.seat_count == SEAT_COUNT == 6
    assert snapshot.status == TableStatus.IDLE
    assert len(snapshot.seats) == 6
    assert [seat.seat_index for seat in snapshot.seats] == list(range(6))
    assert all(seat.status == SeatStatus.EMPTY for seat in snapshot.seats)


def test_seat_player_places_player_with_default_stack() -> None:
    manager, _adapter = make_manager()

    snapshot = manager.seat_player(
        0,
        player_id="p1",
        player_name="Alice",
        controller_type="human",
    )

    seat = snapshot.seats[0]
    assert seat.player_id == "p1"
    assert seat.player_name == "Alice"
    assert seat.controller_type == "human"
    assert seat.stack == DEFAULT_STARTING_STACK == 200
    assert seat.status == SeatStatus.SEATED


def test_seat_player_supports_api_positional_shape() -> None:
    manager, _adapter = make_manager()

    snapshot = manager.seat_player(1, "Bob", "bot", 300)

    seat = snapshot.seats[1]
    assert seat.player_id == "Bob"
    assert seat.player_name == "Bob"
    assert seat.controller_type == "bot"
    assert seat.stack == 300


def test_duplicate_player_cannot_take_second_seat() -> None:
    manager, _adapter = make_manager()
    manager.seat_player(0, player_id="p1", player_name="Alice")

    with pytest.raises(PlayerAlreadySeatedError) as exc_info:
        manager.seat_player(1, player_id="p1", player_name="Alice Again")

    assert exc_info.value.code == "player_already_seated"
    assert manager.get_table_snapshot().seats[1].status == SeatStatus.EMPTY


def test_occupied_seat_cannot_be_reused() -> None:
    manager, _adapter = make_manager()
    manager.seat_player(0, player_id="p1", player_name="Alice")

    with pytest.raises(SeatOccupiedError) as exc_info:
        manager.seat_player(0, player_id="p2", player_name="Bob")

    assert exc_info.value.code == "seat_occupied"
    assert manager.get_table_snapshot().seats[0].player_id == "p1"


@pytest.mark.parametrize("seat_index", [-1, 6])
def test_invalid_seat_index_is_rejected(seat_index: int) -> None:
    manager, _adapter = make_manager()

    with pytest.raises(SeatNotFoundError) as exc_info:
        manager.seat_player(seat_index, player_id="p1", player_name="Alice")

    assert exc_info.value.code == "seat_not_found"


def test_seat_player_rejects_invalid_starting_stack_without_mutation() -> None:
    manager, _adapter = make_manager()

    with pytest.raises(InvalidStackError) as exc_info:
        manager.seat_player(0, player_id="p1", player_name="Alice", starting_stack=0)

    assert exc_info.value.code == "invalid_stack"
    assert manager.get_table_snapshot().seats[0].status == SeatStatus.EMPTY


def test_start_table_requires_minimum_active_players() -> None:
    manager, _adapter = make_manager()
    manager.seat_player(0, player_id="p1", player_name="Alice")

    with pytest.raises(TableStateConflictError) as exc_info:
        manager.start_table()

    assert exc_info.value.code == "table_state_conflict"
    assert exc_info.value.details == {
        "active_players": 1,
        "minimum_active_players": DEFAULT_MIN_ACTIVE_PLAYERS,
    }

    manager.seat_player(1, player_id="p2", player_name="Bob")
    snapshot = manager.start_table()

    assert snapshot.status == TableStatus.RUNNING


def test_create_next_hand_uses_adapter_with_active_seats_and_starting_stacks() -> None:
    manager, adapter = make_manager()
    seat_two_players(manager)
    manager.start_table()

    context = manager.create_next_hand()

    assert context.hand_id == "hand-1"
    assert context.button_seat_index == 0
    assert context.active_seat_indexes == (0, 1)
    assert context.starting_stacks == {0: 200, 1: 200}
    assert adapter.requests == [
        CreateHandRequest(
            hand_id="hand-1",
            seat_to_player={0: "p1", 1: "p2"},
            starting_stacks={0: 200, 1: 200},
            button_seat_index=0,
            small_blind=1,
            big_blind=2,
            ante=0,
        )
    ]
    assert [seat.status for seat in manager.get_table_snapshot().seats[:2]] == [
        SeatStatus.IN_HAND,
        SeatStatus.IN_HAND,
    ]


def test_apply_hand_settlement_updates_long_lived_stacks() -> None:
    manager, _adapter = make_manager()
    seat_two_players(manager)
    manager.start_table()
    context = manager.create_next_hand()

    snapshot = manager.apply_hand_settlement(
        {
            "hand_id": context.hand_id,
            "final_stacks": {"0": 250, "1": 150},
            "payoffs": {"0": 50, "1": -50},
        }
    )

    assert snapshot.current_hand_id is None
    assert snapshot.seats[0].stack == 250
    assert snapshot.seats[1].stack == 150
    assert snapshot.seats[0].status == SeatStatus.SEATED
    assert snapshot.seats[1].status == SeatStatus.SEATED


def test_settlement_mismatch_does_not_change_stacks_or_clear_hand() -> None:
    manager, _adapter = make_manager()
    seat_two_players(manager)
    manager.start_table()
    context = manager.create_next_hand()

    with pytest.raises(HandSettlementMismatchError) as exc_info:
        manager.apply_hand_settlement(
            HandSettlement(hand_id="other-hand", final_stacks={0: 1, 1: 399})
        )

    snapshot = manager.get_table_snapshot()
    assert exc_info.value.code == "hand_settlement_mismatch"
    assert snapshot.current_hand_id == context.hand_id
    assert snapshot.seats[0].stack == 200
    assert snapshot.seats[1].stack == 200


def test_button_moves_after_formal_hand_end_and_next_hand_can_be_created() -> None:
    manager, adapter = make_manager()
    seat_two_players(manager, seats=(0, 2))
    manager.start_table()
    first_context = manager.create_next_hand()

    assert manager.get_table_snapshot().button_seat_index == 0

    settled = manager.apply_hand_settlement(
        {"hand_id": first_context.hand_id, "final_stacks": {0: 200, 2: 200}}
    )
    second_context = manager.create_next_hand()

    assert settled.button_seat_index == 2
    assert second_context.hand_id == "hand-2"
    assert second_context.button_seat_index == 2
    assert len(adapter.requests) == 2


def test_paused_table_does_not_create_next_hand() -> None:
    manager, adapter = make_manager()
    seat_two_players(manager)
    manager.start_table()

    snapshot = manager.pause_table()
    with pytest.raises(TableStateConflictError) as exc_info:
        manager.create_next_hand()

    assert snapshot.status == TableStatus.PAUSED
    assert exc_info.value.code == "table_state_conflict"
    assert adapter.requests == []
    assert manager.resume_table().status == TableStatus.RUNNING


def test_reset_clears_pending_hand_context_and_seats() -> None:
    manager, _adapter = make_manager()
    seat_two_players(manager)
    manager.start_table()
    manager.create_next_hand()

    snapshot = manager.reset_table()

    assert snapshot.status == TableStatus.IDLE
    assert snapshot.current_hand_id is None
    assert snapshot.current_hand is None
    assert all(seat.status == SeatStatus.EMPTY for seat in snapshot.seats)
    assert all(seat.player_id is None and seat.stack == 0 for seat in snapshot.seats)


def test_snapshot_excludes_adapter_refs_hidden_cards_and_runtime_objects() -> None:
    manager, _adapter = make_manager()
    seat_two_players(manager)
    manager.start_table()
    context = manager.create_next_hand()

    snapshot = manager.get_table_snapshot()
    payload = snapshot.to_dict()
    serialized = json.dumps(payload, sort_keys=True)

    assert context.adapter_hand_ref is not None
    assert payload["current_hand"] == {
        "hand_id": "hand-1",
        "button_seat_index": 0,
        "active_seat_indexes": [0, 1],
        "starting_stacks": {0: 200, 1: 200},
    }
    assert "adapter_hand_ref" not in serialized
    assert "private_hole_cards" not in serialized
    assert "adapter-secret" not in serialized
    assert "As" not in serialized
    assert "Kd" not in serialized
    assert "<" not in serialized


def test_table_manager_does_not_import_rule_engine_package() -> None:
    source_path = SRC_ROOT / "mcx_poker" / "table" / "manager.py"
    tree = ast.parse(source_path.read_text(encoding="utf-8"))
    imported_roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".", 1)[0])

    assert "pokerkit" not in imported_roots


def test_table_snapshot_is_json_safe_public_data() -> None:
    manager, _adapter = make_manager()
    seat_two_players(manager)
    manager.start_table()
    manager.create_next_hand()

    encoded = manager.get_table_snapshot().to_json()
    decoded: dict[str, Any] = json.loads(encoded)

    assert decoded["table_id"] == "local-table"
    assert decoded["seat_count"] == 6
    assert decoded["hand_id"] == "hand-1"
    assert len(decoded["seats"]) == 6
