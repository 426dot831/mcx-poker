import inspect
import json
from typing import Any

import pytest

import mcx_poker.engine.actions as action_model
from mcx_poker.engine.actions import (
    ActionError,
    ActionSource,
    ActionType,
    LegalAction,
    LegalActionSet,
    PlayerAction,
)


def make_action(action_type: ActionType, amount: int | None = None) -> PlayerAction:
    return PlayerAction(
        player_id="player-1",
        seat_index=0,
        hand_id="hand-1",
        turn_id="turn-1",
        action_type=action_type,
        amount=amount,
        source=ActionSource.HUMAN,
    )


@pytest.mark.parametrize(
    ("action_type", "amount"),
    [
        (ActionType.FOLD, None),
        (ActionType.CHECK, None),
        (ActionType.CALL, None),
        (ActionType.RAISE_TO, 120),
        (ActionType.ALL_IN, None),
    ],
)
def test_all_action_types_round_trip_through_dict_and_json(
    action_type: ActionType, amount: int | None
) -> None:
    action = make_action(action_type, amount)

    payload = action.to_dict()
    assert payload["action_type"] == action_type.value
    assert payload["amount"] == amount
    assert payload["source"] == "human"

    assert PlayerAction.from_dict(payload) == action
    assert PlayerAction.from_json(action.to_json()) == action


def test_raise_to_requires_amount() -> None:
    with pytest.raises(ValueError, match="RaiseTo requires amount"):
        make_action(ActionType.RAISE_TO)


@pytest.mark.parametrize(
    "action_type",
    [ActionType.FOLD, ActionType.CHECK, ActionType.CALL, ActionType.ALL_IN],
)
def test_non_raise_actions_reject_amount(action_type: ActionType) -> None:
    with pytest.raises(ValueError, match="does not accept amount"):
        make_action(action_type, 100)


def test_all_in_without_amount_passes_shape_validation() -> None:
    action = make_action(ActionType.ALL_IN)

    assert action.action_type is ActionType.ALL_IN
    assert action.amount is None


@pytest.mark.parametrize("bad_amount", [10.0, -1, "10", True])
def test_amount_rejects_float_negative_or_non_numeric_values(bad_amount: object) -> None:
    with pytest.raises(ValueError):
        make_action(ActionType.RAISE_TO, bad_amount)  # type: ignore[arg-type]


def test_action_error_defaults_retry_same_player_to_true() -> None:
    error = ActionError(
        code="invalid_action",
        message="Action is not available now",
        player_id="player-1",
        hand_id="hand-1",
        turn_id="turn-1",
    )

    assert error.retry_same_player is True
    assert ActionError.from_dict(error.to_dict()) == error
    assert ActionError.from_json(error.to_json()) == error


def test_legal_action_set_round_trips_for_observation_contract() -> None:
    action_set = LegalActionSet(
        (
            LegalAction(ActionType.FOLD),
            LegalAction(ActionType.CALL, amount_fixed=20),
            LegalAction(ActionType.RAISE_TO, amount_min=40, amount_max=200),
            LegalAction(ActionType.ALL_IN),
        )
    )

    payload: dict[str, Any] = action_set.to_dict()
    round_trip = LegalActionSet.from_json(action_set.to_json())
    payload_actions = payload["actions"]
    assert isinstance(payload_actions, list)
    second_action = payload_actions[1]
    assert isinstance(second_action, dict)

    assert second_action["amount_fixed"] == 20
    assert round_trip == action_set
    assert action_set.get("RaiseTo") == LegalAction(
        ActionType.RAISE_TO, amount_min=40, amount_max=200
    )


def test_action_model_serialization_contains_only_platform_json_values() -> None:
    action = make_action(ActionType.RAISE_TO, 100)
    legal_actions = LegalActionSet((LegalAction(ActionType.RAISE_TO, amount_min=40),))
    error = ActionError("invalid_shape", "Amount is required", "player-1", "hand-1", "turn-1")

    serialized = json.dumps(
        [action.to_dict(), legal_actions.to_dict(), error.to_dict()],
        sort_keys=True,
    )

    assert "pokerkit" not in serialized.casefold()
    assert "ActionType" not in serialized
    assert "ActionSource" not in serialized
    assert "<" not in serialized
    assert "pokerkit" not in inspect.getsource(action_model).casefold()
