from __future__ import annotations

from dataclasses import fields, is_dataclass
from pathlib import Path
from typing import Any

import pytest
from pokerkit import State

from mcx_poker.engine.pokerkit_adapter import (
    ActionType,
    ActorRef,
    CreateHandRequest,
    PlayerAction,
    PokerKitAdapter,
    PokerKitAdapterError,
)


def _six_player_request(hand_id: str, stacks: tuple[int, ...] | None = None) -> CreateHandRequest:
    return CreateHandRequest(
        hand_id=hand_id,
        seat_to_player={seat: f"p{seat}" for seat in range(6)},
        starting_stacks=stacks or (200, 200, 200, 200, 200, 200),
        button_seat_index=5,
        small_blind=1,
        big_blind=2,
        ante=0,
    )


def _three_player_request(
    hand_id: str,
    stacks: tuple[int, int, int],
) -> CreateHandRequest:
    return CreateHandRequest(
        hand_id=hand_id,
        seat_to_player={0: "p0", 1: "p1", 2: "p2"},
        starting_stacks=stacks,
        button_seat_index=2,
        small_blind=1,
        big_blind=2,
        ante=0,
    )


def _current_action(
    adapter: PokerKitAdapter,
    hand_id: str,
    action_type: ActionType,
    amount: int | None = None,
) -> PlayerAction:
    summary = adapter.get_state_summary(hand_id)
    assert summary.current_actor is not None
    return PlayerAction(
        player_id=summary.current_actor.player_id,
        seat_index=summary.current_actor.seat_index,
        hand_id=hand_id,
        turn_id="turn-1",
        action_type=action_type,
        amount=amount,
        source="test",
    )


def _contains_pokerkit_state(value: Any) -> bool:
    if isinstance(value, State):
        return True
    if is_dataclass(value):
        return any(_contains_pokerkit_state(getattr(value, field.name)) for field in fields(value))
    if isinstance(value, dict):
        return any(
            _contains_pokerkit_state(key) or _contains_pokerkit_state(item)
            for key, item in value.items()
        )
    if isinstance(value, (tuple, list, set, frozenset)):
        return any(_contains_pokerkit_state(item) for item in value)
    return False


def test_only_adapter_and_adapter_test_import_pokerkit() -> None:
    repo_root = Path(__file__).parents[1]
    matches = []
    for root in (repo_root / "src", repo_root / "tests"):
        for path in root.rglob("*.py"):
            text = path.read_text()
            if "from pokerkit" in text or "import pokerkit" in text:
                matches.append(path.relative_to(repo_root).as_posix())

    assert matches == [
        "src/mcx_poker/engine/pokerkit_adapter.py",
        "tests/test_pokerkit_adapter.py",
    ]


def test_sparse_active_seats_map_to_pokerkit_indices_from_button() -> None:
    adapter = PokerKitAdapter()

    summary = adapter.create_hand(
        CreateHandRequest(
            hand_id="sparse",
            seat_to_player={0: "small-blind", 2: "big-blind", 5: "button"},
            starting_stacks=(100, 200, 300),
            button_seat_index=5,
            small_blind=1,
            big_blind=2,
            ante=0,
        )
    )

    mapping = adapter.get_hand_mapping("sparse")
    assert dict(mapping.seat_to_pokerkit_index) == {0: 0, 2: 1, 5: 2}
    assert dict(mapping.pokerkit_index_to_seat) == {0: 0, 1: 2, 2: 5}
    assert dict(mapping.player_to_pokerkit_index) == {
        "small-blind": 0,
        "big-blind": 1,
        "button": 2,
    }
    assert summary.current_actor == ActorRef(seat_index=5, player_id="button")
    assert dict(summary.stacks) == {0: 99, 2: 198, 5: 300}


def test_state_summary_does_not_expose_pokerkit_state() -> None:
    adapter = PokerKitAdapter()
    summary = adapter.create_hand(_six_player_request("summary"))

    assert not _contains_pokerkit_state(summary)
    assert all(
        isinstance(card, str) for cards in summary.hole_cards_by_seat.values() for card in cards
    )
    assert all(isinstance(card, str) for card in summary.board_cards)


def test_fold_call_and_raise_to_map_to_expected_pokerkit_operations() -> None:
    fold_adapter = PokerKitAdapter()
    fold_adapter.create_hand(_six_player_request("fold"))
    fold_result = fold_adapter.submit_action(_current_action(fold_adapter, "fold", ActionType.FOLD))
    assert fold_result.operation.operation_type == "Folding"
    assert fold_result.operation.details["seat_index"] == 2

    call_adapter = PokerKitAdapter()
    call_adapter.create_hand(_six_player_request("call"))
    call_result = call_adapter.submit_action(_current_action(call_adapter, "call", ActionType.CALL))
    assert call_result.operation.operation_type == "CheckingOrCalling"
    assert call_result.operation.details["amount"] == 2
    assert call_result.state_summary.stacks[2] == 198
    assert call_result.state_summary.bets[2] == 2

    raise_adapter = PokerKitAdapter()
    raise_adapter.create_hand(_six_player_request("raise"))
    raise_result = raise_adapter.submit_action(
        _current_action(raise_adapter, "raise", ActionType.RAISE_TO, amount=4)
    )
    assert raise_result.operation.operation_type == "CompletionBettingOrRaisingTo"
    assert raise_result.operation.details["amount"] == 4
    assert raise_result.state_summary.stacks[2] == 196
    assert raise_result.state_summary.bets[2] == 4


def test_pokerkit_exceptions_map_to_platform_error_without_raw_exception(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    adapter = PokerKitAdapter()
    adapter.create_hand(_six_player_request("pk-error"))
    record = adapter._hands["pk-error"]

    def boom(amount: int | None = None, *, commentary: str | None = None) -> None:
        raise ValueError("raw pokerkit rejection details")

    monkeypatch.setattr(record.state, "complete_bet_or_raise_to", boom)

    with pytest.raises(PokerKitAdapterError) as exc_info:
        adapter.submit_action(_current_action(adapter, "pk-error", ActionType.RAISE_TO, amount=4))

    error = exc_info.value
    assert error.code == "pokerkit_illegal_action"
    assert error.message == "PokerKit rejected the submitted action."
    assert "raw pokerkit rejection details" not in error.message
    assert error.__cause__ is None


def test_six_player_cash_game_initializes_with_automated_blinds_and_hole_cards() -> None:
    adapter = PokerKitAdapter()
    summary = adapter.create_hand(_six_player_request("cash"))

    mapping = adapter.get_hand_mapping("cash")
    assert len(mapping.seat_to_pokerkit_index) == 6
    assert set(summary.stacks) == set(range(6))
    assert dict(summary.bets) == {0: 1, 1: 2, 2: 0, 3: 0, 4: 0, 5: 0}
    assert summary.pot_summary.total_amount == 3
    assert all(len(cards) == 2 for cards in summary.hole_cards_by_seat.values())


def test_automation_after_create_hand_sets_first_preflop_actor() -> None:
    adapter = PokerKitAdapter()
    summary = adapter.create_hand(_six_player_request("first-actor"))

    assert summary.current_actor == ActorRef(seat_index=2, player_id="p2")


def test_preflop_call_updates_stacks_bets_pot_and_actor() -> None:
    adapter = PokerKitAdapter()
    adapter.create_hand(_six_player_request("preflop-call"))

    result = adapter.submit_action(_current_action(adapter, "preflop-call", ActionType.CALL))

    assert result.state_summary.stacks[2] == 198
    assert result.state_summary.bets[2] == 2
    assert result.state_summary.pot_summary.total_amount == 5
    assert result.state_summary.current_actor == ActorRef(seat_index=3, player_id="p3")


def test_initial_legal_action_boundaries_match_pokerkit_no_limit_values() -> None:
    adapter = PokerKitAdapter()
    summary = adapter.create_hand(_six_player_request("boundaries"))
    boundaries = summary.legal_action_boundaries

    assert boundaries.fold.enabled
    assert not boundaries.check.enabled
    assert boundaries.call.enabled
    assert boundaries.call_amount == 2
    assert boundaries.call.amount_fixed == 2
    assert boundaries.raise_to.enabled
    assert boundaries.min_raise_to == 4
    assert boundaries.max_raise_to == 200
    assert boundaries.raise_to.amount_min == 4
    assert boundaries.raise_to.amount_max == 200
    assert boundaries.all_in.enabled
    assert boundaries.all_in.amount_fixed == 200


def test_legal_raise_to_four_succeeds() -> None:
    adapter = PokerKitAdapter()
    adapter.create_hand(_six_player_request("raise-four"))

    result = adapter.submit_action(_current_action(adapter, "raise-four", ActionType.RAISE_TO, 4))

    assert result.operation.operation_type == "CompletionBettingOrRaisingTo"
    assert result.operation.details["amount"] == 4
    assert result.state_summary.stacks[2] == 196
    assert result.state_summary.bets[2] == 4
    assert result.state_summary.current_actor == ActorRef(seat_index=3, player_id="p3")


def test_illegal_raise_to_two_and_above_stack_fail_without_advancing_state() -> None:
    adapter = PokerKitAdapter()
    initial = adapter.create_hand(_six_player_request("illegal-raise"))

    for amount in (2, 201):
        with pytest.raises(PokerKitAdapterError) as exc_info:
            adapter.submit_action(
                _current_action(adapter, "illegal-raise", ActionType.RAISE_TO, amount)
            )
        assert exc_info.value.code == "pokerkit_illegal_action"

    after = adapter.get_state_summary("illegal-raise")
    assert after.stacks == initial.stacks
    assert after.bets == initial.bets
    assert after.current_actor == initial.current_actor


def test_folding_to_hand_end_returns_settlement() -> None:
    adapter = PokerKitAdapter()
    adapter.create_hand(_six_player_request("settlement"))

    while adapter.get_state_summary("settlement").is_active:
        summary = adapter.get_state_summary("settlement")
        assert summary.legal_action_boundaries.fold.enabled
        adapter.submit_action(_current_action(adapter, "settlement", ActionType.FOLD))

    settlement = adapter.get_hand_settlement("settlement")
    assert dict(settlement.final_stacks) == {0: 199, 1: 201, 2: 200, 3: 200, 4: 200, 5: 200}
    assert dict(settlement.payoffs) == {0: -1, 1: 1, 2: 0, 3: 0, 4: 0, 5: 0}
    assert settlement.winners[0].seat_index == 1
    assert settlement.winners[0].payoff == 1
    assert settlement.final_board == ()
    assert any(
        operation.operation_type == "ChipsPulling" for operation in settlement.operations_summary
    )


def test_all_in_maps_to_raise_to_max_call_and_short_stack_boundary() -> None:
    max_adapter = PokerKitAdapter()
    max_summary = max_adapter.create_hand(_six_player_request("all-in-max"))
    assert max_summary.legal_action_boundaries.all_in.amount_fixed == 200

    max_result = max_adapter.submit_action(
        _current_action(max_adapter, "all-in-max", ActionType.ALL_IN)
    )
    assert max_result.operation.operation_type == "CompletionBettingOrRaisingTo"
    assert max_result.operation.details["amount"] == 200
    assert max_result.state_summary.stacks[2] == 0
    assert max_result.state_summary.bets[2] == 200

    call_adapter = PokerKitAdapter()
    call_summary = call_adapter.create_hand(_three_player_request("all-in-call", (200, 200, 2)))
    assert call_summary.legal_action_boundaries.call_amount == 2
    assert call_summary.legal_action_boundaries.min_raise_to is None
    assert call_summary.legal_action_boundaries.max_raise_to is None
    assert call_summary.legal_action_boundaries.all_in.amount_fixed == 2

    call_result = call_adapter.submit_action(
        _current_action(call_adapter, "all-in-call", ActionType.ALL_IN)
    )
    assert call_result.operation.operation_type == "CheckingOrCalling"
    assert call_result.operation.details["amount"] == 2
    assert call_result.state_summary.stacks[2] == 0
    assert call_result.state_summary.bets[2] == 2

    short_raise_adapter = PokerKitAdapter()
    short_summary = short_raise_adapter.create_hand(
        _three_player_request("short-all-in-raise", (200, 200, 3))
    )
    # PokerKit exposes a short all-in that can exceed the call as min=max RaiseTo(3).
    assert short_summary.legal_action_boundaries.call_amount == 2
    assert short_summary.legal_action_boundaries.min_raise_to == 3
    assert short_summary.legal_action_boundaries.max_raise_to == 3
    assert short_summary.legal_action_boundaries.all_in.amount_fixed == 3

    short_result = short_raise_adapter.submit_action(
        _current_action(short_raise_adapter, "short-all-in-raise", ActionType.ALL_IN)
    )
    assert short_result.operation.operation_type == "CompletionBettingOrRaisingTo"
    assert short_result.operation.details["amount"] == 3
    assert short_result.state_summary.stacks[2] == 0
    assert short_result.state_summary.bets[2] == 3
