"""WebSocket delivery gateway for table events and human actions."""

from __future__ import annotations

import inspect
from dataclasses import dataclass
from typing import Any
from uuid import uuid4

from fastapi import WebSocket, WebSocketDisconnect
from fastapi.encoders import jsonable_encoder

from mcx_poker.delivery.api import DeliveryError, map_exception, to_public_dto

SERVER_EVENT_TYPES = {
    "table_snapshot",
    "hand_started",
    "hole_cards_dealt",
    "board_updated",
    "action_requested",
    "player_acted",
    "action_rejected",
    "hand_ended",
    "table_paused",
    "table_resumed",
    "table_reset",
}
BROADCAST_EVENT_TYPES = {
    "table_snapshot",
    "hand_started",
    "board_updated",
    "player_acted",
    "hand_ended",
    "table_paused",
    "table_resumed",
    "table_reset",
}
PRIVATE_EVENT_TYPES = {"hole_cards_dealt", "action_requested", "action_rejected"}
CLIENT_EVENT_TYPES = {"submit_action", "request_snapshot"}
REQUIRED_ACTION_FIELDS = {"player_id", "seat_index", "hand_id", "turn_id", "action_type"}


@dataclass(slots=True)
class ConnectionState:
    """Per-WebSocket state required by the gateway contract."""

    connection_id: str
    socket: Any
    table_id: str
    player_id: str | None = None
    seat_index: int | None = None
    visibility_scope: str = "table"


@dataclass(slots=True)
class PendingTurn:
    table_id: str
    player_id: str
    seat_index: int
    hand_id: str
    turn_id: str


class WebSocketGateway:
    """Protocol layer around FastAPI WebSockets.

    The gateway only validates message shape, connection ownership, and current
    turn identity. Business legality remains delegated to the injected human
    controller.
    """

    def __init__(
        self,
        *,
        table_manager: Any | None = None,
        human_controller: Any | None = None,
    ) -> None:
        self.table_manager = table_manager
        self.human_controller = human_controller
        self.connections: dict[str, ConnectionState] = {}
        self._socket_to_connection_id: dict[int, str] = {}
        self._current_turn_by_table: dict[str, PendingTurn] = {}

    async def websocket_endpoint(self, websocket: WebSocket) -> None:
        table_id = websocket.query_params.get("table_id", "local-table")
        player_id = websocket.query_params.get("player_id")
        seat_index = _parse_optional_int(websocket.query_params.get("seat_index"))

        state = await self.connect(
            websocket,
            table_id=table_id,
            player_id=player_id,
            seat_index=seat_index,
        )
        try:
            while True:
                try:
                    message = await websocket.receive_json()
                except ValueError:
                    await self.send_action_rejected(
                        state.connection_id,
                        "invalid_message",
                        "message must be valid JSON",
                    )
                    continue
                await self.handle_client_event(state.connection_id, message)
        except WebSocketDisconnect:
            await self.disconnect(state.connection_id)

    async def connect(
        self,
        socket: Any,
        *,
        table_id: str = "local-table",
        player_id: str | None = None,
        seat_index: int | None = None,
        visibility_scope: str | None = None,
        accept: bool = True,
    ) -> ConnectionState:
        if accept and hasattr(socket, "accept"):
            result = socket.accept()
            if inspect.isawaitable(result):
                await result

        connection_id = uuid4().hex
        state = ConnectionState(
            connection_id=connection_id,
            socket=socket,
            table_id=table_id,
            player_id=player_id,
            seat_index=seat_index,
            visibility_scope=visibility_scope
            or ("player" if player_id is not None or seat_index is not None else "table"),
        )
        self.connections[connection_id] = state
        self._socket_to_connection_id[id(socket)] = connection_id
        return state

    async def disconnect(self, connection_id: str) -> None:
        state = self.connections.pop(connection_id, None)
        if state is not None:
            self._socket_to_connection_id.pop(id(state.socket), None)

    def bind_connection(
        self,
        connection_id: str,
        *,
        player_id: str,
        seat_index: int,
        table_id: str | None = None,
        visibility_scope: str = "player",
    ) -> ConnectionState:
        state = self._require_connection(connection_id)
        state.player_id = player_id
        state.seat_index = seat_index
        if table_id is not None:
            state.table_id = table_id
        state.visibility_scope = visibility_scope
        return state

    async def handle_client_event(self, connection_id: str, message: Any) -> None:
        if not isinstance(message, dict):
            await self.send_action_rejected(
                connection_id,
                "invalid_message",
                "message must be an object",
            )
            return

        event_type = message.get("type") or message.get("event_type") or message.get("event")
        payload = message.get("payload", {})
        if not isinstance(event_type, str):
            await self.send_action_rejected(
                connection_id,
                "invalid_message",
                "message type is required",
            )
            return
        if event_type not in CLIENT_EVENT_TYPES:
            await self.send_action_rejected(
                connection_id,
                "unknown_event_type",
                f"unknown event type: {event_type}",
            )
            return

        if event_type == "request_snapshot":
            await self._handle_request_snapshot(connection_id)
            return

        if not isinstance(payload, dict):
            await self.send_action_rejected(
                connection_id,
                "invalid_message",
                "payload must be an object",
            )
            return
        await self._handle_submit_action(connection_id, payload)

    async def broadcast_table_snapshot(self, snapshot: Any, *, table_id: str | None = None) -> None:
        await self.broadcast_event("table_snapshot", snapshot, table_id=table_id)

    async def broadcast_event(
        self,
        event_type: str,
        payload: Any,
        *,
        table_id: str | None = None,
    ) -> None:
        if event_type not in BROADCAST_EVENT_TYPES:
            raise DeliveryError("invalid_message", f"{event_type} is not a broadcast event")

        public_payload = to_public_dto(payload)
        await self._send_to_matching_connections(event_type, public_payload, table_id=table_id)

    async def send_hole_cards_dealt(
        self,
        player_id: str,
        seat_index: int,
        payload: Any,
        table_id: str | None = None,
    ) -> None:
        await self.send_private_event(
            "hole_cards_dealt",
            payload,
            player_id=player_id,
            seat_index=seat_index,
            table_id=table_id,
        )

    async def send_action_requested(
        self,
        player_id: str,
        seat_index: int,
        payload: Any,
        table_id: str | None = None,
    ) -> None:
        table_keys = self._matching_table_ids(player_id, seat_index, table_id)
        if not table_keys:
            table_keys = {table_id or _payload_str(payload, "table_id") or "local-table"}
        hand_id = _payload_str(payload, "hand_id")
        turn_id = _payload_str(payload, "turn_id")
        if hand_id is not None and turn_id is not None:
            for table_key in table_keys:
                self._current_turn_by_table[table_key] = PendingTurn(
                    table_id=table_key,
                    player_id=player_id,
                    seat_index=seat_index,
                    hand_id=hand_id,
                    turn_id=turn_id,
                )

        await self.send_private_event(
            "action_requested",
            payload,
            player_id=player_id,
            seat_index=seat_index,
            table_id=table_id,
        )

    async def send_action_rejected(
        self,
        connection_id: str,
        code: str,
        message: str,
        *,
        payload: dict[str, Any] | None = None,
    ) -> None:
        error_payload = {
            "error": {
                "code": code,
                "message": message,
            }
        }
        if payload:
            error_payload.update(to_public_dto(payload))
        await self.send_to_connection(connection_id, "action_rejected", error_payload)

    async def send_action_rejected_to_player(
        self,
        player_id: str,
        seat_index: int,
        payload: Any,
        table_id: str | None = None,
    ) -> None:
        await self.send_private_event(
            "action_rejected",
            payload,
            player_id=player_id,
            seat_index=seat_index,
            table_id=table_id,
        )

    async def send_private_event(
        self,
        event_type: str,
        payload: Any,
        *,
        player_id: str,
        seat_index: int,
        table_id: str | None = None,
    ) -> None:
        if event_type not in PRIVATE_EVENT_TYPES:
            raise DeliveryError("invalid_message", f"{event_type} is not a private event")

        for state in list(self.connections.values()):
            if table_id is not None and state.table_id != table_id:
                continue
            if state.player_id == player_id and state.seat_index == seat_index:
                await self.send_to_connection(state.connection_id, event_type, payload)

    async def send_to_connection(self, connection_id: str, event_type: str, payload: Any) -> None:
        state = self._require_connection(connection_id)
        await self._send_socket_json(
            state.socket,
            {
                "type": event_type,
                "payload": _encode_event_payload(event_type, payload),
            },
        )

    async def _handle_request_snapshot(self, connection_id: str) -> None:
        state = self._require_connection(connection_id)
        if self.table_manager is None:
            await self.send_action_rejected(
                connection_id,
                "table_unavailable",
                "table manager is not configured",
            )
            return

        try:
            snapshot = await _call_service_method(
                self.table_manager,
                ("get_table", "get_table_snapshot"),
                {"table_id": state.table_id},
                ("table_id",),
            )
        except Exception as exc:
            error = map_exception(exc)
            await self.send_action_rejected(connection_id, error.code, error.message)
            return

        await self.send_to_connection(connection_id, "table_snapshot", snapshot)

    async def _handle_submit_action(self, connection_id: str, payload: dict[str, Any]) -> None:
        missing_fields = sorted(REQUIRED_ACTION_FIELDS - set(payload))
        if missing_fields:
            await self.send_action_rejected(
                connection_id,
                "invalid_message",
                "submit_action payload is missing required fields",
                payload={"missing_fields": missing_fields},
            )
            return

        action_type = payload.get("action_type")
        if action_type == "RaiseTo" and payload.get("amount") is None:
            await self.send_action_rejected(
                connection_id,
                "invalid_message",
                "RaiseTo requires amount",
            )
            return
        if action_type != "RaiseTo" and payload.get("amount") is not None:
            await self.send_action_rejected(
                connection_id,
                "invalid_message",
                "amount is only valid for RaiseTo",
            )
            return

        state = self._require_connection(connection_id)
        player_id = str(payload["player_id"])
        seat_index = payload["seat_index"]
        if state.player_id is None or state.seat_index is None:
            await self.send_action_rejected(
                connection_id,
                "connection_not_bound_to_player",
                "connection is not bound to a player",
            )
            return
        if player_id != state.player_id or seat_index != state.seat_index:
            await self.send_action_rejected(
                connection_id,
                "connection_not_bound_to_player",
                "connection does not own the submitted player and seat",
            )
            return

        pending_turn = self._current_turn_by_table.get(state.table_id)
        if pending_turn is not None:
            if pending_turn.player_id != player_id or pending_turn.seat_index != seat_index:
                await self.send_action_rejected(
                    connection_id,
                    "not_current_actor",
                    "submitted player is not the current actor",
                )
                return
            if pending_turn.hand_id != str(payload["hand_id"]) or pending_turn.turn_id != str(
                payload["turn_id"]
            ):
                await self.send_action_rejected(
                    connection_id,
                    "stale_turn",
                    "submitted action is for a stale turn",
                )
                return

        if self.human_controller is None:
            await self.send_action_rejected(
                connection_id,
                "table_unavailable",
                "human controller is not configured",
            )
            return

        try:
            result = await _call_service_method(
                self.human_controller,
                ("submit_action", "receive_action", "handle_action"),
                {**payload, "source": payload.get("source", "human")},
            )
        except Exception as exc:
            error = map_exception(exc)
            await self.send_action_rejected(connection_id, error.code, error.message)
            return

        if isinstance(result, dict) and result.get("ok") is False:
            raw_error = result.get("error") or {}
            code = str(raw_error.get("code", "action_rejected"))
            message = str(raw_error.get("message", code.replace("_", " ")))
            await self.send_action_rejected(connection_id, code, message)

    async def _send_to_matching_connections(
        self,
        event_type: str,
        payload: Any,
        *,
        table_id: str | None = None,
    ) -> None:
        for state in list(self.connections.values()):
            if table_id is not None and state.table_id != table_id:
                continue
            await self.send_to_connection(state.connection_id, event_type, payload)

    async def _send_socket_json(self, socket: Any, message: dict[str, Any]) -> None:
        if hasattr(socket, "send_json"):
            result = socket.send_json(message)
        elif hasattr(socket, "send"):
            result = socket.send(message)
        else:
            raise DeliveryError("table_unavailable", "socket does not support JSON send")

        if inspect.isawaitable(result):
            await result

    def _require_connection(self, connection_id: str) -> ConnectionState:
        try:
            return self.connections[connection_id]
        except KeyError as exc:
            raise DeliveryError(
                "connection_not_bound_to_player",
                f"unknown connection: {connection_id}",
            ) from exc

    def _matching_table_ids(
        self,
        player_id: str,
        seat_index: int,
        table_id: str | None,
    ) -> set[str]:
        if table_id is not None:
            return {table_id}
        return {
            state.table_id
            for state in self.connections.values()
            if state.player_id == player_id and state.seat_index == seat_index
        }


async def _call_service_method(
    service: Any,
    method_names: tuple[str, ...],
    payload: dict[str, Any],
    positional_order: tuple[str, ...] = (),
) -> Any:
    target = None
    for method_name in method_names:
        candidate = getattr(service, method_name, None)
        if callable(candidate):
            target = candidate
            break
    if target is None:
        raise DeliveryError("table_unavailable", "service method is not configured")

    result = _call_with_supported_arguments(target, payload, positional_order)
    if inspect.isawaitable(result):
        return await result
    return result


def _call_with_supported_arguments(
    target: Any,
    payload: dict[str, Any],
    positional_order: tuple[str, ...],
) -> Any:
    signature = inspect.signature(target)
    parameters = list(signature.parameters.values())

    if any(parameter.kind == inspect.Parameter.VAR_KEYWORD for parameter in parameters):
        return target(**payload)

    supported_keyword_names = {
        parameter.name
        for parameter in parameters
        if parameter.kind
        in (inspect.Parameter.POSITIONAL_OR_KEYWORD, inspect.Parameter.KEYWORD_ONLY)
    }
    if set(payload).issubset(supported_keyword_names):
        return target(**payload)

    positional_parameters = [
        parameter
        for parameter in parameters
        if parameter.kind
        in (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD)
    ]
    if not positional_parameters:
        return target()

    if len(positional_parameters) == 1 and not positional_order:
        return target(payload)

    ordered_args = [payload[name] for name in positional_order if name in payload]
    if len(positional_parameters) == 1 and ordered_args:
        return target(ordered_args[0])

    return target(*ordered_args[: len(positional_parameters)])


def _payload_str(payload: Any, key: str) -> str | None:
    if isinstance(payload, dict) and payload.get(key) is not None:
        return str(payload[key])
    return None


def _parse_optional_int(value: str | None) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except ValueError:
        return None


def _encode_event_payload(event_type: str, payload: Any) -> Any:
    if event_type == "table_snapshot" or event_type in BROADCAST_EVENT_TYPES:
        return to_public_dto(payload)
    return _to_json_dto(payload)


def _to_json_dto(value: Any) -> Any:
    if value is None or isinstance(value, str | int | float | bool):
        return value

    value_type = value.__class__
    if "pokerkit" in getattr(value_type, "__module__", "").lower():
        return None

    if isinstance(value, dict):
        return {
            str(key): _to_json_dto(inner_value)
            for key, inner_value in value.items()
            if "pokerkit" not in str(key).lower()
        }

    if isinstance(value, list | tuple | set | frozenset):
        return [_to_json_dto(item) for item in value]

    if hasattr(value, "model_dump"):
        return _to_json_dto(value.model_dump())

    if hasattr(value, "__dataclass_fields__"):
        return _to_json_dto(
            {field_name: getattr(value, field_name) for field_name in value.__dataclass_fields__}
        )

    if hasattr(value, "__dict__"):
        return _to_json_dto(vars(value))

    try:
        return jsonable_encoder(value)
    except Exception:
        return repr(value)
    try:
        return int(value)
    except ValueError:
        return None


__all__ = [
    "ConnectionState",
    "PendingTurn",
    "WebSocketGateway",
]
