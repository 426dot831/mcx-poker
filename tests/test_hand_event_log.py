from __future__ import annotations

from typing import cast

import pytest

from mcx_poker.history import EventType, EventVisibility, HandEvent, HandEventLog, JSONValue


def test_sequence_numbers_are_monotonic_within_hand() -> None:
    log = HandEventLog()

    started = log.record_hand_started("hand-1")
    snapshot = log.record_seat_snapshot(
        "hand-1",
        [{"player_id": "p1", "seat_index": 0, "starting_stack": 100}],
    )
    action = log.record_action_succeeded("hand-1", "p1", "call", amount=10)

    assert [started.sequence_number, snapshot.sequence_number, action.sequence_number] == [
        1,
        2,
        3,
    ]
    assert log.get_last_sequence("hand-1") == 3


def test_public_events_do_not_include_private_hole_cards() -> None:
    log = HandEventLog()

    log.record_hand_started("hand-1")
    log.record_hole_cards_dealt("hand-1", "p1", ["As", "Kd"])
    log.record_board_dealt("hand-1", ["2c", "7d", "Jh"], street="flop")

    public_events = log.list_public_events("hand-1")

    assert [event.event_type for event in public_events] == [
        EventType.HAND_STARTED,
        EventType.BOARD_DEALT,
    ]
    assert all(event.private_payload is None for event in public_events)


def test_player_can_read_own_private_hole_cards() -> None:
    log = HandEventLog()

    log.record_hole_cards_dealt("hand-1", "p1", ["As", "Kd"])

    player_events = log.list_player_events("hand-1", "p1")

    hole_card_events = [
        event for event in player_events if event.event_type == EventType.HOLE_CARDS_DEALT
    ]
    assert len(hole_card_events) == 1
    assert hole_card_events[0].private_payload == {"cards": ["As", "Kd"]}
    assert hole_card_events[0].visibility == EventVisibility.PLAYER_SCOPED


def test_other_players_cannot_read_private_hole_cards() -> None:
    log = HandEventLog()

    log.record_hole_cards_dealt("hand-1", "p1", ["As", "Kd"])

    player_events = log.list_player_events("hand-1", "p2")

    assert all(event.event_type != EventType.HOLE_CARDS_DEALT for event in player_events)


def test_rejected_action_is_not_in_successful_action_flow() -> None:
    log = HandEventLog()

    rejected = log.record_action_rejected(
        "hand-1",
        "p1",
        "not enough chips",
        attempted_action="raise",
    )
    succeeded = log.record_action_succeeded("hand-1", "p1", "call", amount=10)

    assert rejected.event_type == EventType.ACTION_REJECTED
    assert log.list_successful_actions("hand-1") == [succeeded]
    assert rejected not in log.list_public_events("hand-1")


def test_settlement_remains_readable_after_hand_ended() -> None:
    log = HandEventLog()

    settlement = log.record_settlement(
        "hand-1",
        {"winners": [{"player_id": "p1", "amount": 40}], "pot_total": 40},
    )
    ended = log.record_hand_ended("hand-1", {"reason": "settled"})

    public_events = log.list_public_events("hand-1")

    assert settlement in public_events
    assert ended in public_events
    assert public_events[-2:] == [settlement, ended]


def test_clear_hand_removes_events_and_sequence_state() -> None:
    log = HandEventLog()

    log.record_hand_started("hand-1")
    log.record_action_succeeded("hand-1", "p1", "check")

    log.clear_hand("hand-1")

    assert log.list_public_events("hand-1") == []
    assert log.list_player_events("hand-1", "p1") == []
    assert log.get_last_sequence("hand-1") == 0


def test_payload_rejects_pokerkit_runtime_objects() -> None:
    class PokerKitState:
        __module__ = "pokerkit.state"

    log = HandEventLog()

    with pytest.raises(ValueError, match="PokerKit"):
        log.append(
            HandEvent(
                hand_id="hand-1",
                event_type=EventType.POT_UPDATED,
                public_payload=cast(JSONValue, {"raw_state": PokerKitState()}),
            )
        )


def test_public_payload_rejects_private_card_and_deck_keys() -> None:
    with pytest.raises(ValueError, match="public_payload"):
        HandEvent(
            hand_id="hand-1",
            event_type=EventType.ACTION_SUCCEEDED,
            public_payload={"hole_cards": ["As", "Kd"]},
        )

    showdown = HandEvent(
        hand_id="hand-1",
        event_type=EventType.SHOWDOWN,
        public_payload={"players": [{"player_id": "p1", "hole_cards": ["As", "Kd"]}]},
    )
    assert showdown.public_payload == {"players": [{"player_id": "p1", "hole_cards": ["As", "Kd"]}]}

    with pytest.raises(ValueError, match="public_payload"):
        HandEvent(
            hand_id="hand-1",
            event_type=EventType.SHOWDOWN,
            public_payload={"deck_order": ["As", "Kd"]},
        )

    with pytest.raises(ValueError, match="player-scoped"):
        HandEvent(
            hand_id="hand-1",
            event_type=EventType.HOLE_CARDS_DEALT,
            public_payload={"cards": ["As", "Kd"]},
        )
