"""FastAPI delivery boundary for local table control.

The delivery layer intentionally depends on injected services instead of poker
engine internals. Table managers and human controllers can be synchronous or
asynchronous; tests use fakes and the real app can provide concrete services
later.
"""

from __future__ import annotations

import inspect
from collections.abc import Awaitable, Callable, Mapping
from pathlib import Path
from typing import Any, Literal, Protocol

import uvicorn
from fastapi import Body, Depends, FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field, field_validator

ApiRouteReturn = dict[str, Any] | JSONResponse
DEFAULT_LOCAL_TABLE_ID = "local-table"
STATIC_DIR = Path(__file__).resolve().parent / "static"

ErrorCode = Literal[
    "invalid_request",
    "table_not_initialized",
    "table_state_conflict",
    "seat_not_found",
    "seat_occupied",
    "player_already_seated",
    "unknown_controller_type",
    "game_not_started",
    "internal_error",
    "connection_not_bound_to_player",
    "stale_turn",
    "not_current_actor",
    "action_rejected",
    "table_unavailable",
]


class ApiError(BaseModel):
    """Stable platform error returned to API clients."""

    code: str
    message: str
    details: dict[str, Any] | None = None


class ApiResponse(BaseModel):
    """Uniform HTTP response envelope."""

    ok: bool
    data: Any = None
    error: ApiError | None = None


class DeliveryError(Exception):
    """Platform-layer error that can be rendered as an ApiResponse."""

    def __init__(
        self,
        code: str,
        message: str | None = None,
        *,
        status_code: int | None = None,
        details: Mapping[str, Any] | None = None,
    ) -> None:
        super().__init__(message or code)
        self.code = code
        self.message = message or code.replace("_", " ")
        self.status_code = status_code or status_for_error(code)
        self.details = dict(details) if details is not None else None


class TableManagerProtocol(Protocol):
    """Minimal table-manager surface consumed by the delivery API."""

    def initialize_table(self, config: Mapping[str, Any] | None = None) -> Any: ...

    def seat_player(
        self,
        seat_index: int,
        player_name: str,
        controller_type: str,
        starting_stack: int,
    ) -> Any: ...

    def start_table(self, table_id: str) -> Any: ...

    def pause_table(self, table_id: str) -> Any: ...

    def resume_table(self, table_id: str) -> Any: ...

    def reset_table(self, table_id: str) -> Any: ...

    def get_table(self, table_id: str) -> Any: ...


class HumanControllerProtocol(Protocol):
    """Optional human-controller hooks used at delivery boundaries."""

    def submit_action(self, action: Mapping[str, Any]) -> Any: ...

    def invalidate_pending_actions(self, table_id: str) -> Any: ...

    def on_table_paused(self, table_id: str) -> Any: ...


class SeatPlayerRequest(BaseModel):
    """Request body for seating a player."""

    model_config = ConfigDict(extra="forbid")

    seat_index: int
    player_name: str = Field(min_length=1)
    controller_type: str = Field(min_length=1)
    starting_stack: int

    @field_validator("seat_index")
    @classmethod
    def validate_seat_index(cls, value: int) -> int:
        if value < 0 or value > 5:
            raise ValueError("seat_index must be between 0 and 5")
        return value

    @field_validator("player_name")
    @classmethod
    def validate_player_name(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("player_name is required")
        return stripped

    @field_validator("starting_stack")
    @classmethod
    def validate_starting_stack(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("starting_stack must be positive")
        return value


class TableControlRequest(BaseModel):
    """Request body for table control operations."""

    model_config = ConfigDict(extra="forbid")

    table_id: str = Field(min_length=1)
    command: Literal["start", "pause", "resume", "reset"]

    @field_validator("table_id")
    @classmethod
    def validate_table_id(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("table_id is required")
        return stripped


class PlayerActionRequest(BaseModel):
    """Reserved HTTP shape for future human action submission."""

    model_config = ConfigDict(extra="forbid")

    player_id: str = Field(min_length=1)
    seat_index: int
    hand_id: str = Field(min_length=1)
    turn_id: str = Field(min_length=1)
    action_type: str = Field(min_length=1)
    amount: int | None = None
    source: str = "human"

    @field_validator("seat_index")
    @classmethod
    def validate_seat_index(cls, value: int) -> int:
        if value < 0 or value > 5:
            raise ValueError("seat_index must be between 0 and 5")
        return value

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, value: int | None) -> int | None:
        if value is not None and value <= 0:
            raise ValueError("amount must be positive when provided")
        return value


class _UnavailableTableManager:
    """Default app dependency until a real table manager is wired in."""

    def initialize_table(self, config: Mapping[str, Any] | None = None) -> Any:
        raise DeliveryError("table_unavailable", "table manager is not configured")

    def seat_player(
        self,
        seat_index: int,
        player_name: str,
        controller_type: str,
        starting_stack: int,
    ) -> Any:
        raise DeliveryError("table_unavailable", "table manager is not configured")

    def start_table(self, table_id: str) -> Any:
        raise DeliveryError("table_unavailable", "table manager is not configured")

    def pause_table(self, table_id: str) -> Any:
        raise DeliveryError("table_unavailable", "table manager is not configured")

    def resume_table(self, table_id: str) -> Any:
        raise DeliveryError("table_unavailable", "table manager is not configured")

    def reset_table(self, table_id: str) -> Any:
        raise DeliveryError("table_unavailable", "table manager is not configured")

    def get_table(self, table_id: str) -> Any:
        raise DeliveryError("table_unavailable", "table manager is not configured")


PUBLIC_CONTROLLER_TYPES = {"human", "bot"}
HIDDEN_SNAPSHOT_KEYS = {
    "adapter_hand_ref",
    "deck",
    "hole_cards",
    "hidden_hole_cards",
    "private_cards",
    "private_hole_cards",
}
ERROR_STATUS = {
    "invalid_request": status.HTTP_400_BAD_REQUEST,
    "unknown_controller_type": status.HTTP_400_BAD_REQUEST,
    "seat_not_found": status.HTTP_404_NOT_FOUND,
    "table_not_initialized": status.HTTP_404_NOT_FOUND,
    "table_unavailable": status.HTTP_503_SERVICE_UNAVAILABLE,
    "seat_occupied": status.HTTP_409_CONFLICT,
    "player_already_seated": status.HTTP_409_CONFLICT,
    "table_state_conflict": status.HTTP_409_CONFLICT,
    "game_not_started": status.HTTP_409_CONFLICT,
    "connection_not_bound_to_player": status.HTTP_409_CONFLICT,
    "stale_turn": status.HTTP_409_CONFLICT,
    "not_current_actor": status.HTTP_409_CONFLICT,
    "action_rejected": status.HTTP_409_CONFLICT,
    "internal_error": status.HTTP_500_INTERNAL_SERVER_ERROR,
}


def status_for_error(code: str) -> int:
    return ERROR_STATUS.get(code, status.HTTP_400_BAD_REQUEST)


def success_response(data: Any) -> dict[str, Any]:
    return ApiResponse(ok=True, data=to_public_dto(data), error=None).model_dump()


def error_response(
    code: str,
    message: str | None = None,
    *,
    status_code: int | None = None,
    details: Mapping[str, Any] | None = None,
) -> JSONResponse:
    error = ApiError(
        code=code,
        message=message or code.replace("_", " "),
        details=to_public_dto(details) if details is not None else None,
    )
    body = ApiResponse(ok=False, data=None, error=error).model_dump()
    return JSONResponse(status_code=status_code or status_for_error(code), content=body)


def to_public_dto(value: Any) -> Any:
    """Convert platform DTOs into JSON-safe data while dropping hidden fields."""

    if value is None or isinstance(value, str | int | float | bool):
        return value

    value_type = value.__class__
    if "pokerkit" in getattr(value_type, "__module__", "").lower():
        return None

    if isinstance(value, Mapping):
        public: dict[str, Any] = {}
        for raw_key, raw_value in value.items():
            key = str(raw_key)
            normalized = key.lower()
            if normalized in HIDDEN_SNAPSHOT_KEYS or "pokerkit" in normalized:
                continue
            public[key] = to_public_dto(raw_value)
        return public

    if isinstance(value, list | tuple | set | frozenset):
        return [to_public_dto(item) for item in value]

    if hasattr(value, "model_dump"):
        return to_public_dto(value.model_dump())

    if hasattr(value, "__dataclass_fields__"):
        return to_public_dto(
            {field_name: getattr(value, field_name) for field_name in value.__dataclass_fields__}
        )

    if hasattr(value, "__dict__"):
        return to_public_dto(vars(value))

    try:
        return jsonable_encoder(value)
    except Exception:
        return repr(value)


def create_app(
    table_manager: Any | None = None,
    *,
    human_controller: Any | None = None,
    websocket_gateway: Any | None = None,
) -> FastAPI:
    """Create the FastAPI app with injected delivery dependencies."""

    manager = table_manager or _UnavailableTableManager()
    app = FastAPI(title="mcx-poker delivery API")
    app.state.table_manager = manager
    app.state.human_controller = human_controller

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        return error_response(
            "invalid_request",
            "request validation failed",
            status_code=status.HTTP_400_BAD_REQUEST,
            details={"errors": exc.errors()},
        )

    @app.exception_handler(DeliveryError)
    async def delivery_exception_handler(request: Request, exc: DeliveryError) -> JSONResponse:
        return error_response(
            exc.code,
            exc.message,
            status_code=exc.status_code,
            details=exc.details,
        )

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    async def manager_dep() -> Any:
        return app.state.table_manager

    async def human_controller_dep() -> Any:
        return app.state.human_controller

    initialize_body = Body(default=None)
    manager_dependency = Depends(manager_dep)
    human_controller_dependency = Depends(human_controller_dep)

    async def initialize_table(
        config: dict[str, Any] | None = initialize_body,
        current_manager: Any = manager_dependency,
    ) -> ApiRouteReturn:
        return await _run_api_operation(
            lambda: _call_service_method(
                current_manager,
                ("initialize_table",),
                payload=config,
            )
        )

    async def seat_player(
        request: SeatPlayerRequest,
        current_manager: Any = manager_dependency,
    ) -> ApiRouteReturn:
        if request.controller_type not in PUBLIC_CONTROLLER_TYPES:
            raise DeliveryError(
                "unknown_controller_type",
                f"unknown controller type: {request.controller_type}",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        payload = request.model_dump()
        return await _run_api_operation(
            lambda: _call_service_method(
                current_manager,
                ("seat_player",),
                payload=payload,
                positional_order=(
                    "seat_index",
                    "player_name",
                    "controller_type",
                    "starting_stack",
                ),
            )
        )

    async def table_control(
        request: TableControlRequest,
        current_manager: Any = manager_dependency,
        current_human_controller: Any = human_controller_dependency,
    ) -> ApiRouteReturn:
        method_by_command = {
            "start": "start_table",
            "pause": "pause_table",
            "resume": "resume_table",
            "reset": "reset_table",
        }
        command = request.command

        async def operation() -> Any:
            snapshot = await _call_service_method(
                current_manager,
                (method_by_command[command],),
                payload={"table_id": request.table_id},
                positional_order=("table_id",),
            )
            if command == "reset":
                await _notify_optional_hook(
                    current_human_controller,
                    ("invalidate_pending_actions", "reset_pending_actions", "on_table_reset"),
                    request.table_id,
                )
            elif command == "pause":
                await _notify_optional_hook(
                    current_human_controller,
                    ("on_table_paused", "pause_pending_actions"),
                    request.table_id,
                )
            return snapshot

        return await _run_api_operation(operation)

    async def start_table(
        table_id: str,
        current_manager: Any = manager_dependency,
    ) -> ApiRouteReturn:
        return await _run_api_operation(
            lambda: _call_service_method(
                current_manager,
                ("start_table",),
                payload={"table_id": table_id},
                positional_order=("table_id",),
            )
        )

    async def pause_table(
        table_id: str,
        current_manager: Any = manager_dependency,
        current_human_controller: Any = human_controller_dependency,
    ) -> ApiRouteReturn:
        async def operation() -> Any:
            snapshot = await _call_service_method(
                current_manager,
                ("pause_table",),
                payload={"table_id": table_id},
                positional_order=("table_id",),
            )
            await _notify_optional_hook(
                current_human_controller,
                ("on_table_paused", "pause_pending_actions"),
                table_id,
            )
            return snapshot

        return await _run_api_operation(operation)

    async def resume_table(
        table_id: str,
        current_manager: Any = manager_dependency,
    ) -> ApiRouteReturn:
        return await _run_api_operation(
            lambda: _call_service_method(
                current_manager,
                ("resume_table",),
                payload={"table_id": table_id},
                positional_order=("table_id",),
            )
        )

    async def reset_table(
        table_id: str,
        current_manager: Any = manager_dependency,
        current_human_controller: Any = human_controller_dependency,
    ) -> ApiRouteReturn:
        async def operation() -> Any:
            snapshot = await _call_service_method(
                current_manager,
                ("reset_table",),
                payload={"table_id": table_id},
                positional_order=("table_id",),
            )
            await _notify_optional_hook(
                current_human_controller,
                ("invalidate_pending_actions", "reset_pending_actions", "on_table_reset"),
                table_id,
            )
            return snapshot

        return await _run_api_operation(operation)

    async def get_table(
        table_id: str,
        current_manager: Any = manager_dependency,
    ) -> ApiRouteReturn:
        return await _run_api_operation(
            lambda: _call_service_method(
                current_manager,
                ("get_table", "get_table_snapshot"),
                payload={"table_id": table_id},
                positional_order=("table_id",),
            )
        )

    async def get_default_table(
        current_manager: Any = manager_dependency,
    ) -> ApiRouteReturn:
        return await get_table(DEFAULT_LOCAL_TABLE_ID, current_manager)

    async def submit_action(
        request: PlayerActionRequest,
        current_human_controller: Any = human_controller_dependency,
    ) -> ApiRouteReturn:
        if current_human_controller is None:
            raise DeliveryError(
                "table_unavailable",
                "human controller is not configured",
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        return await _run_api_operation(
            lambda: _call_service_method(
                current_human_controller,
                ("submit_action", "receive_action"),
                payload=request.model_dump(),
            )
        )

    def add_route(path: str, endpoint: Callable[..., Any], methods: list[str]) -> None:
        app.add_api_route(path, endpoint, methods=methods, response_model=None)

    add_route("/api/table/initialize", initialize_table, ["POST"])
    add_route("/api/tables/initialize", initialize_table, ["POST"])
    add_route("/table/initialize", initialize_table, ["POST"])

    add_route("/api/table/seats", seat_player, ["POST"])
    add_route("/api/tables/seats", seat_player, ["POST"])
    add_route("/table/seats", seat_player, ["POST"])

    add_route("/api/table/control", table_control, ["POST"])
    add_route("/api/tables/control", table_control, ["POST"])
    add_route("/table/control", table_control, ["POST"])

    add_route("/api/table/{table_id}/start", start_table, ["POST"])
    add_route("/api/table/{table_id}/pause", pause_table, ["POST"])
    add_route("/api/table/{table_id}/resume", resume_table, ["POST"])
    add_route("/api/table/{table_id}/reset", reset_table, ["POST"])

    add_route("/api/table", get_default_table, ["GET"])
    add_route("/table", get_default_table, ["GET"])
    add_route("/api/table/{table_id}", get_table, ["GET"])
    add_route("/api/tables/{table_id}", get_table, ["GET"])
    add_route("/table/{table_id}", get_table, ["GET"])

    add_route("/api/actions/submit", submit_action, ["POST"])

    if websocket_gateway is None:
        try:
            from mcx_poker.delivery.websocket import WebSocketGateway

            websocket_gateway = WebSocketGateway(
                table_manager=manager,
                human_controller=human_controller,
            )
        except Exception:
            websocket_gateway = None

    if websocket_gateway is not None and hasattr(websocket_gateway, "websocket_endpoint"):
        app.state.websocket_gateway = websocket_gateway
        app.add_api_websocket_route("/ws", websocket_gateway.websocket_endpoint)
        app.add_api_websocket_route("/ws/table", websocket_gateway.websocket_endpoint)
        app.add_api_websocket_route("/api/ws", websocket_gateway.websocket_endpoint)
        app.add_api_websocket_route("/api/ws/table", websocket_gateway.websocket_endpoint)

    if STATIC_DIR.exists():
        app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")

    return app


async def _run_api_operation(operation: Callable[[], Any]) -> ApiRouteReturn:
    try:
        result = operation()
        if inspect.isawaitable(result):
            result = await result
        return success_response(result)
    except DeliveryError as exc:
        return error_response(
            exc.code,
            exc.message,
            status_code=exc.status_code,
            details=exc.details,
        )
    except Exception as exc:
        platform_error = map_exception(exc)
        if platform_error.code == "internal_error":
            return error_response(
                platform_error.code,
                platform_error.message,
                status_code=platform_error.status_code,
            )
        return error_response(
            platform_error.code,
            platform_error.message,
            status_code=platform_error.status_code,
            details=platform_error.details,
        )


def map_exception(exc: Exception) -> DeliveryError:
    if isinstance(exc, DeliveryError):
        return exc

    code = getattr(exc, "code", None) or getattr(exc, "error_code", None)
    message = getattr(exc, "message", None) or str(exc) or None
    details = getattr(exc, "details", None)

    if code is None and exc.args:
        first_arg = exc.args[0]
        if isinstance(first_arg, str) and first_arg in ERROR_STATUS:
            code = first_arg

    if isinstance(code, str) and code in ERROR_STATUS and code != "internal_error":
        return DeliveryError(code, message, status_code=status_for_error(code), details=details)

    class_name = exc.__class__.__name__.lower()
    class_name_map = {
        "seatoccupied": "seat_occupied",
        "seatoccupiederror": "seat_occupied",
        "playeralreadyseated": "player_already_seated",
        "playeralreadyseatederror": "player_already_seated",
        "seatnotfound": "seat_not_found",
        "seatnotfounderror": "seat_not_found",
        "tablenotinitialized": "table_not_initialized",
        "tablenotinitializederror": "table_not_initialized",
        "tablestateconflict": "table_state_conflict",
        "tablestateconflicterror": "table_state_conflict",
        "gamenotstarted": "game_not_started",
        "gamenotstartederror": "game_not_started",
    }
    if class_name in class_name_map:
        mapped_code = class_name_map[class_name]
        return DeliveryError(
            mapped_code,
            message,
            status_code=status_for_error(mapped_code),
            details=details,
        )

    return DeliveryError(
        "internal_error",
        "internal server error",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


async def _call_service_method(
    service: Any,
    method_names: tuple[str, ...],
    *,
    payload: Mapping[str, Any] | None = None,
    positional_order: tuple[str, ...] = (),
) -> Any:
    target = _find_method(service, method_names)
    result = _call_with_supported_arguments(target, payload or {}, positional_order)
    if inspect.isawaitable(result):
        return await result
    return result


def _find_method(service: Any, method_names: tuple[str, ...]) -> Callable[..., Any]:
    for method_name in method_names:
        target = getattr(service, method_name, None)
        if callable(target):
            return target
    joined = ", ".join(method_names)
    raise DeliveryError("table_unavailable", f"service does not provide: {joined}")


def _call_with_supported_arguments(
    target: Callable[..., Any],
    payload: Mapping[str, Any],
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
    if payload and set(payload).issubset(supported_keyword_names):
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


async def _notify_optional_hook(
    service: Any | None,
    method_names: tuple[str, ...],
    table_id: str,
) -> None:
    if service is None:
        return

    for method_name in method_names:
        target = getattr(service, method_name, None)
        if callable(target):
            result = target(table_id)
            if inspect.isawaitable(result):
                await result
            return


def maybe_await(value: Any) -> Awaitable[Any] | Any:
    return value


def create_default_app() -> FastAPI:
    """Create the default local playable MVP app."""

    from mcx_poker.delivery.local import create_local_service

    service = create_local_service()
    return create_app(
        service,
        human_controller=service,
        websocket_gateway=service.websocket_gateway,
    )


app = create_default_app()


def main() -> None:
    """Local development entry point."""

    uvicorn.run("mcx_poker.delivery.api:app", host="127.0.0.1", port=8000, reload=False)


__all__ = [
    "ApiError",
    "ApiResponse",
    "DeliveryError",
    "HumanControllerProtocol",
    "PlayerActionRequest",
    "SeatPlayerRequest",
    "TableControlRequest",
    "TableManagerProtocol",
    "app",
    "create_app",
    "create_default_app",
    "error_response",
    "main",
    "success_response",
    "to_public_dto",
]
