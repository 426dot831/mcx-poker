from __future__ import annotations

from typing import Any

import pytest

from mcx_poker.delivery.api import DeliveryError
from mcx_poker.delivery.websocket import WebSocketGateway


class FakeSocket:
    def __init__(self) -> None:
        self.sent: list[dict[str, Any]] = []

    async def send_json(self, message: dict[str, Any]) -> None:
        self.sent.append(message)


class FakeHumanController:
    def __init__(self) -> None:
        self.actions: list[dict[str, Any]] = []
        self.reject = False

    def submit_action(self, action: dict[str, Any]) -> dict[str, Any]:
        self.actions.append(action)
        if self.reject:
            return {
                "ok": False,
                "error": {
                    "code": "action_rejected",
                    "message": "validator rejected action",
                },
            }
        return {"ok": True}


class FakeTableManager:
    def get_table(self, table_id: str) -> dict[str, Any]:
        return {
            "table_id": table_id,
            "status": "running",
            "seats": [{"seat_index": 0, "hole_cards": ["As", "Ah"]}],
        }


async def connect_player(
    gateway: WebSocketGateway,
    *,
    player_id: str,
    seat_index: int,
    table_id: str = "table-1",
) -> tuple[FakeSocket, str]:
    socket = FakeSocket()
    state = await gateway.connect(
        socket,
        table_id=table_id,
        player_id=player_id,
        seat_index=seat_index,
        accept=False,
    )
    return socket, state.connection_id


def action_payload(**overrides: Any) -> dict[str, Any]:
    payload = {
        "player_id": "player-1",
        "seat_index": 0,
        "hand_id": "hand-1",
        "turn_id": "turn-1",
        "action_type": "Check",
    }
    payload.update(overrides)
    return payload


def last_error_code(socket: FakeSocket) -> str:
    message = socket.sent[-1]
    assert message["type"] == "action_rejected"
    return message["payload"]["error"]["code"]


@pytest.mark.asyncio
async def test_ws_t01_action_requested_only_reaches_target_connection() -> None:
    gateway = WebSocketGateway(human_controller=FakeHumanController())
    target_socket, _ = await connect_player(gateway, player_id="player-1", seat_index=0)
    other_socket, _ = await connect_player(gateway, player_id="player-2", seat_index=1)

    await gateway.send_action_requested(
        "player-1",
        0,
        {
            "table_id": "table-1",
            "hand_id": "hand-1",
            "turn_id": "turn-1",
            "observation": {"legal_actions": ["Check"]},
        },
    )

    assert [message["type"] for message in target_socket.sent] == ["action_requested"]
    assert target_socket.sent[0]["payload"]["observation"]["legal_actions"] == ["Check"]
    assert other_socket.sent == []


@pytest.mark.asyncio
async def test_ws_t02_table_snapshot_broadcast_removes_hidden_cards() -> None:
    gateway = WebSocketGateway()
    socket, _ = await connect_player(gateway, player_id="player-1", seat_index=0)

    await gateway.broadcast_table_snapshot(
        {
            "table_id": "table-1",
            "seats": [{"seat_index": 0, "hole_cards": ["As", "Ah"]}],
            "adapter_hand_ref": {"pokerkit_object": "hidden"},
        },
        table_id="table-1",
    )

    assert socket.sent[0]["type"] == "table_snapshot"
    assert "hole_cards" not in str(socket.sent[0])
    assert "pokerkit" not in str(socket.sent[0]).lower()


@pytest.mark.asyncio
async def test_ws_t03_submit_action_missing_fields_is_rejected() -> None:
    controller = FakeHumanController()
    gateway = WebSocketGateway(human_controller=controller)
    socket, connection_id = await connect_player(gateway, player_id="player-1", seat_index=0)

    await gateway.handle_client_event(
        connection_id,
        {
            "type": "submit_action",
            "payload": {"player_id": "player-1"},
        },
    )

    assert last_error_code(socket) == "invalid_message"
    assert controller.actions == []


@pytest.mark.asyncio
async def test_ws_t04_stale_turn_is_rejected_before_controller() -> None:
    controller = FakeHumanController()
    gateway = WebSocketGateway(human_controller=controller)
    socket, connection_id = await connect_player(gateway, player_id="player-1", seat_index=0)
    await gateway.send_action_requested(
        "player-1",
        0,
        {"table_id": "table-1", "hand_id": "hand-1", "turn_id": "turn-1"},
    )

    await gateway.handle_client_event(
        connection_id,
        {
            "type": "submit_action",
            "payload": action_payload(turn_id="old-turn"),
        },
    )

    assert last_error_code(socket) == "stale_turn"
    assert controller.actions == []


@pytest.mark.asyncio
async def test_ws_t05_connection_cannot_submit_for_other_player() -> None:
    controller = FakeHumanController()
    gateway = WebSocketGateway(human_controller=controller)
    socket, connection_id = await connect_player(gateway, player_id="player-1", seat_index=0)

    await gateway.handle_client_event(
        connection_id,
        {
            "type": "submit_action",
            "payload": action_payload(player_id="player-2", seat_index=1),
        },
    )

    assert last_error_code(socket) == "connection_not_bound_to_player"
    assert controller.actions == []


@pytest.mark.asyncio
async def test_ws_t06_controller_rejection_is_sent_to_origin_connection() -> None:
    controller = FakeHumanController()
    controller.reject = True
    gateway = WebSocketGateway(human_controller=controller)
    socket, connection_id = await connect_player(gateway, player_id="player-1", seat_index=0)
    await gateway.send_action_requested(
        "player-1",
        0,
        {"table_id": "table-1", "hand_id": "hand-1", "turn_id": "turn-1"},
    )
    socket.sent.clear()

    await gateway.handle_client_event(
        connection_id,
        {
            "type": "submit_action",
            "payload": action_payload(),
        },
    )

    assert controller.actions[0]["action_type"] == "Check"
    assert last_error_code(socket) == "action_rejected"


@pytest.mark.asyncio
async def test_ws_t07_hole_cards_dealt_is_private_and_preserves_cards() -> None:
    gateway = WebSocketGateway()
    target_socket, _ = await connect_player(gateway, player_id="player-1", seat_index=0)
    other_socket, _ = await connect_player(gateway, player_id="player-2", seat_index=1)

    await gateway.send_hole_cards_dealt(
        "player-1",
        0,
        {"hand_id": "hand-1", "hole_cards": ["As", "Ah"]},
        table_id="table-1",
    )

    assert [message["type"] for message in target_socket.sent] == ["hole_cards_dealt"]
    assert target_socket.sent[0]["payload"]["hole_cards"] == ["As", "Ah"]
    assert other_socket.sent == []


@pytest.mark.asyncio
async def test_ws_t08_fake_human_controller_receives_valid_submit_action() -> None:
    controller = FakeHumanController()
    gateway = WebSocketGateway(
        table_manager=FakeTableManager(),
        human_controller=controller,
    )
    socket, connection_id = await connect_player(gateway, player_id="player-1", seat_index=0)
    await gateway.send_action_requested(
        "player-1",
        0,
        {"table_id": "table-1", "hand_id": "hand-1", "turn_id": "turn-1"},
    )
    socket.sent.clear()

    await gateway.handle_client_event(
        connection_id,
        {
            "type": "submit_action",
            "payload": action_payload(),
        },
    )

    assert controller.actions == [{**action_payload(), "source": "human"}]
    assert socket.sent == []


@pytest.mark.asyncio
async def test_request_snapshot_uses_public_snapshot() -> None:
    gateway = WebSocketGateway(table_manager=FakeTableManager())
    socket, connection_id = await connect_player(gateway, player_id="player-1", seat_index=0)

    await gateway.handle_client_event(connection_id, {"type": "request_snapshot"})

    assert socket.sent[0]["type"] == "table_snapshot"
    assert "hole_cards" not in str(socket.sent[0])


@pytest.mark.asyncio
async def test_controller_exceptions_are_mapped_to_action_rejected() -> None:
    class RejectingController:
        def submit_action(self, action: dict[str, Any]) -> None:
            raise DeliveryError("not_current_actor", "not current actor")

    gateway = WebSocketGateway(human_controller=RejectingController())
    socket, connection_id = await connect_player(gateway, player_id="player-1", seat_index=0)

    await gateway.handle_client_event(
        connection_id,
        {
            "type": "submit_action",
            "payload": action_payload(),
        },
    )

    assert last_error_code(socket) == "not_current_actor"
