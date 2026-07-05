from __future__ import annotations

import copy
import inspect
from types import SimpleNamespace
from typing import Any

import pytest

import mcx_poker.engine.validator as validator_module
from mcx_poker.engine.actions import (
    ActionError,
    ActionSource,
    ActionType,
    LegalAction,
    LegalActionSet,
    PlayerAction,
)
from mcx_poker.engine.validator import (
    ActionContext,
    ValidatedAction,
    adapter_error_to_action_error,
    validate_action,
)


def action_context() -> ActionContext:
    return ActionContext(
        table_id="table-1",
        hand_id="hand-1",
        turn_id="turn-1",
        actor_player_id="p1",
        actor_seat_index=0,
    )


def table_snapshot() -> dict[str, Any]:
    return {
        "table_id": "table-1",
        "hand_id": "hand-1",
        "seats": [
            {"seat_index": 0, "player_id": "p1", "stack": 100},
            {"seat_index": 1, "player_id": "p2", "stack": 100},
        ],
    }


def legal_actions(*actions: LegalAction) -> LegalActionSet:
    return LegalActionSet(actions)


def make_action(
    action_type: ActionType,
    *,
    player_id: str = "p1",
    seat_index: int = 0,
    hand_id: str = "hand-1",
    turn_id: str = "turn-1",
    amount: int | None = None,
) -> PlayerAction:
    return PlayerAction(
        player_id=player_id,
        seat_index=seat_index,
        hand_id=hand_id,
        turn_id=turn_id,
        action_type=action_type,
        amount=amount,
        source=ActionSource.HUMAN,
    )


def loose_action(action_type: ActionType, amount: int | None = None) -> SimpleNamespace:
    return SimpleNamespace(
        player_id="p1",
        seat_index=0,
        hand_id="hand-1",
        turn_id="turn-1",
        action_type=action_type,
        amount=amount,
    )


def assert_action_error(result: object, code: str) -> ActionError:
    assert isinstance(result, ActionError)
    assert result.code == code
    assert result.retry_same_player is True
    return result


def test_av_t01_current_actor_available_fold_succeeds() -> None:
    action = make_action(ActionType.FOLD)

    result = validate_action(
        action,
        action_context(),
        legal_actions(LegalAction(ActionType.FOLD)),
        table_snapshot(),
    )

    assert isinstance(result, ValidatedAction)
    assert result.action is action
    assert result.normalized_type is ActionType.FOLD
    assert result.normalized_amount is None
    assert result.validation_source == "platform"


def test_av_t02_non_current_player_returns_not_current_actor() -> None:
    action = make_action(ActionType.FOLD, player_id="p2", seat_index=1)

    result = validate_action(
        action,
        action_context(),
        legal_actions(LegalAction(ActionType.FOLD)),
        table_snapshot(),
    )

    error = assert_action_error(result, "not_current_actor")
    assert error.player_id == "p2"
    assert error.hand_id == "hand-1"
    assert error.turn_id == "turn-1"


def test_av_t03_stale_turn_returns_turn_mismatch() -> None:
    action = make_action(ActionType.FOLD, turn_id="old-turn")

    result = validate_action(
        action,
        action_context(),
        legal_actions(LegalAction(ActionType.FOLD)),
        table_snapshot(),
    )

    assert_action_error(result, "turn_mismatch")


def test_av_t04_hand_mismatch_returns_hand_mismatch() -> None:
    action = make_action(ActionType.FOLD, hand_id="old-hand")

    result = validate_action(
        action,
        action_context(),
        legal_actions(LegalAction(ActionType.FOLD)),
        table_snapshot(),
    )

    assert_action_error(result, "hand_mismatch")


def test_av_t05_player_not_in_submitted_seat_returns_player_not_seated() -> None:
    action = make_action(ActionType.FOLD, player_id="p2", seat_index=0)

    result = validate_action(
        action,
        action_context(),
        legal_actions(LegalAction(ActionType.FOLD)),
        table_snapshot(),
    )

    assert_action_error(result, "player_not_seated")


@pytest.mark.parametrize(
    "current_legal_actions",
    [
        legal_actions(),
        legal_actions(LegalAction(ActionType.FOLD, enabled=False, reason_if_disabled="blocked")),
    ],
)
def test_av_t06_unavailable_action_returns_action_not_available(
    current_legal_actions: LegalActionSet,
) -> None:
    action = make_action(ActionType.FOLD)

    result = validate_action(action, action_context(), current_legal_actions, table_snapshot())

    assert_action_error(result, "action_not_available")


def test_av_t07_raise_to_without_amount_returns_amount_required() -> None:
    action = loose_action(ActionType.RAISE_TO, amount=None)

    result = validate_action(
        action,
        action_context(),
        legal_actions(LegalAction(ActionType.RAISE_TO, amount_min=40, amount_max=200)),
        table_snapshot(),
    )

    assert_action_error(result, "amount_required")


def test_av_t08_all_in_with_amount_returns_amount_not_allowed() -> None:
    action = loose_action(ActionType.ALL_IN, amount=100)

    result = validate_action(
        action,
        action_context(),
        legal_actions(LegalAction(ActionType.ALL_IN, amount_fixed=100)),
        table_snapshot(),
    )

    assert_action_error(result, "amount_not_allowed")


def test_av_t09_raise_to_below_min_returns_amount_out_of_range() -> None:
    action = make_action(ActionType.RAISE_TO, amount=39)

    result = validate_action(
        action,
        action_context(),
        legal_actions(LegalAction(ActionType.RAISE_TO, amount_min=40, amount_max=200)),
        table_snapshot(),
    )

    assert_action_error(result, "amount_out_of_range")


def test_av_t10_raise_to_above_max_returns_amount_out_of_range() -> None:
    action = make_action(ActionType.RAISE_TO, amount=201)

    result = validate_action(
        action,
        action_context(),
        legal_actions(LegalAction(ActionType.RAISE_TO, amount_min=40, amount_max=200)),
        table_snapshot(),
    )

    assert_action_error(result, "amount_out_of_range")


def test_av_t11_validator_failure_does_not_mutate_snapshot_or_legal_actions() -> None:
    snapshot = table_snapshot()
    current_legal_actions = {
        "actions": [
            {
                "action_type": "RaiseTo",
                "enabled": True,
                "amount_min": 40,
                "amount_max": 200,
            }
        ]
    }
    before_snapshot = copy.deepcopy(snapshot)
    before_legal_actions = copy.deepcopy(current_legal_actions)

    result = validate_action(
        make_action(ActionType.RAISE_TO, amount=20),
        action_context(),
        current_legal_actions,
        snapshot,
    )

    assert_action_error(result, "amount_out_of_range")
    assert snapshot == before_snapshot
    assert current_legal_actions == before_legal_actions


def test_av_t12_adapter_action_error_converts_to_action_error() -> None:
    class AdapterError(Exception):
        def to_dict(self) -> dict[str, object]:
            return {
                "code": "adapter_illegal_action",
                "message": "adapter rejected action",
                "player_id": "p1",
                "hand_id": "hand-1",
                "turn_id": "turn-1",
                "retry_same_player": False,
            }

    error = adapter_error_to_action_error(AdapterError())

    assert error == ActionError(
        code="adapter_illegal_action",
        message="adapter rejected action",
        player_id="p1",
        hand_id="hand-1",
        turn_id="turn-1",
        retry_same_player=True,
    )


@pytest.mark.parametrize(
    ("action_type", "amount_fixed"),
    [
        (ActionType.CHECK, 5),
        (ActionType.CALL, 0),
    ],
)
def test_check_and_call_amount_fixed_semantics_are_enforced(
    action_type: ActionType,
    amount_fixed: int,
) -> None:
    action = make_action(action_type)

    result = validate_action(
        action,
        action_context(),
        legal_actions(LegalAction(action_type, amount_fixed=amount_fixed)),
        table_snapshot(),
    )

    assert_action_error(result, "action_not_available")


def test_mapping_table_snapshot_and_boundary_object_are_supported() -> None:
    action = make_action(ActionType.CALL)
    boundaries = SimpleNamespace(
        fold=LegalAction(ActionType.FOLD),
        check=LegalAction(ActionType.CHECK, enabled=False),
        call=LegalAction(ActionType.CALL, enabled=True, amount_fixed=20),
        raise_to=LegalAction(ActionType.RAISE_TO, amount_min=40, amount_max=200),
        all_in=LegalAction(ActionType.ALL_IN, amount_fixed=100),
    )

    result = validate_action(
        action,
        action_context(),
        boundaries,
        {"seat_to_player": {"0": "p1", "1": "p2"}},
    )

    assert isinstance(result, ValidatedAction)
    assert result.normalized_type is ActionType.CALL


def test_validator_module_does_not_import_adapter_or_rule_engine() -> None:
    source = inspect.getsource(validator_module).casefold()

    assert "pokerkit_adapter" not in source
    assert "from " + "pokerkit" not in source
    assert "import " + "pokerkit" not in source
