# `mcx_poker/delivery/websocket.py` 人话讲解

源文件：`/Users/machengqi/Documents/mcx-poker/src/mcx_poker/delivery/websocket.py`

## 这个文件是干什么的

源码说明：WebSocket delivery gateway for table events and human actions.

人话概括：

负责把牌桌/玩家动作和外部世界连接起来，例如本地运行、HTTP API 或 WebSocket。

## 导入区

- 第 3 行：从 `__future__` 导入 `annotations`。
- 第 5 行：导入 `inspect`。
- 第 6 行：从 `dataclasses` 导入 `dataclass`。
- 第 7 行：从 `typing` 导入 `Any`。
- 第 8 行：从 `uuid` 导入 `uuid4`。
- 第 10 行：从 `fastapi` 导入 `WebSocket, WebSocketDisconnect`。
- 第 11 行：从 `fastapi.encoders` 导入 `jsonable_encoder`。
- 第 13 行：从 `mcx_poker.delivery.api` 导入 `DeliveryError, map_exception, to_public_dto`。

人话：导入区是在声明“这个文件需要哪些外部工具”。标准库通常提供基础能力，项目内导入则说明它依赖哪些业务模块。

## 顶层常量和类型

- 第 15-27 行：`SERVER_EVENT_TYPES` = `{'table_snapshot', 'hand_started', 'hole_cards_dealt', 'board_updated', 'action_requested', 'player_acted', 'action_rejected', 'hand_ended', 'table_paused', 'table_resumed', 'table_reset'}`。人话：在模块级别准备一个后面会反复使用的值。
- 第 28-37 行：`BROADCAST_EVENT_TYPES` = `{'table_snapshot', 'hand_started', 'board_updated', 'player_acted', 'hand_ended', 'table_paused', 'table_resumed', 'table_reset'}`。人话：在模块级别准备一个后面会反复使用的值。
- 第 38 行：`PRIVATE_EVENT_TYPES` = `{'hole_cards_dealt', 'action_requested', 'action_rejected'}`。人话：在模块级别准备一个后面会反复使用的值。
- 第 39 行：`CLIENT_EVENT_TYPES` = `{'submit_action', 'request_snapshot'}`。人话：在模块级别准备一个后面会反复使用的值。
- 第 40 行：`REQUIRED_ACTION_FIELDS` = `{'player_id', 'seat_index', 'hand_id', 'turn_id', 'action_type'}`。人话：在模块级别准备一个后面会反复使用的值。
- 第 602-606 行：`__all__` = `['ConnectionState', 'PendingTurn', 'WebSocketGateway']`。人话：在模块级别准备一个后面会反复使用的值。

## 类 `ConnectionState`（第 44-52 行）

装饰器：`@dataclass(slots=True)`。

源码说明：Per-WebSocket state required by the gateway contract.

人话：把一组相关数据和行为封装到一个类型里，供其他模块按统一接口使用。

字段/类变量：

- `connection_id`：类型 `str`。
- `socket`：类型 `Any`。
- `table_id`：类型 `str`。
- `player_id`：类型 `str | None`，默认值 `None`。
- `seat_index`：类型 `int | None`，默认值 `None`。
- `visibility_scope`：类型 `str`，默认值 `'table'`。

## 类 `PendingTurn`（第 56-61 行）

装饰器：`@dataclass(slots=True)`。

人话：把一组相关数据和行为封装到一个类型里，供其他模块按统一接口使用。

字段/类变量：

- `table_id`：类型 `str`。
- `player_id`：类型 `str`。
- `seat_index`：类型 `int`。
- `hand_id`：类型 `str`。
- `turn_id`：类型 `str`。

## 类 `WebSocketGateway`（第 64-479 行）

源码说明：Protocol layer around FastAPI WebSockets.

The gateway only validates message shape, connection ownership, and current
turn identity. Business legality remains delegated to the injected human
controller.

人话：把一组相关数据和行为封装到一个类型里，供其他模块按统一接口使用。

这个类里的方法：

### `__init__`（第 72-82 行）

签名：

```python
def __init__(self, *, table_manager: Any | None = None, human_controller: Any | None = None) -> None
```

人话：初始化对象，接收外部传入的数据并准备对象内部状态。

关键代码块：

- 第 78 行：给 `self.table_manager` 赋值，准备后面逻辑要用的数据。
- 第 79 行：给 `self.human_controller` 赋值，准备后面逻辑要用的数据。
- 第 80 行：声明字段或变量 `self.connections`，类型是 `dict[str, ConnectionState]`。
- 第 81 行：声明字段或变量 `self._socket_to_connection_id`，类型是 `dict[int, str]`。
- 第 82 行：声明字段或变量 `self._current_turn_by_table`，类型是 `dict[str, PendingTurn]`。

### `websocket_endpoint`（第 84-108 行）

签名：

```python
async def websocket_endpoint(self, websocket: WebSocket) -> None
```

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 85 行：给 `table_id` 赋值，准备后面逻辑要用的数据。
- 第 86 行：给 `player_id` 赋值，准备后面逻辑要用的数据。
- 第 87 行：给 `seat_index` 赋值，准备后面逻辑要用的数据。
- 第 89-94 行：给 `state` 赋值，准备后面逻辑要用的数据。
- 第 95-108 行：尝试执行可能失败的操作，并在异常发生时转成项目自己的处理方式。

### `connect`（第 110-137 行）

签名：

```python
async def connect(self, socket: Any, *, table_id: str = 'local-table', player_id: str | None = None, seat_index: int | None = None, visibility_scope: str | None = None, accept: bool = True) -> ConnectionState
```

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 120-123 行：根据条件 `accept and hasattr(socket, 'accept')` 分支处理不同情况。
- 第 125 行：给 `connection_id` 赋值，准备后面逻辑要用的数据。
- 第 126-134 行：给 `state` 赋值，准备后面逻辑要用的数据。
- 第 135 行：给 `self.connections[connection_id]` 赋值，准备后面逻辑要用的数据。
- 第 136 行：给 `self._socket_to_connection_id[id(socket)]` 赋值，准备后面逻辑要用的数据。
- 第 137 行：返回计算结果，把这个函数的最终答案交给调用者。

### `disconnect`（第 139-142 行）

签名：

```python
async def disconnect(self, connection_id: str) -> None
```

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 140 行：给 `state` 赋值，准备后面逻辑要用的数据。
- 第 141-142 行：根据条件 `state is not None` 分支处理不同情况。

### `bind_connection`（第 144-159 行）

签名：

```python
def bind_connection(self, connection_id: str, *, player_id: str, seat_index: int, table_id: str | None = None, visibility_scope: str = 'player') -> ConnectionState
```

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 153 行：给 `state` 赋值，准备后面逻辑要用的数据。
- 第 154 行：给 `state.player_id` 赋值，准备后面逻辑要用的数据。
- 第 155 行：给 `state.seat_index` 赋值，准备后面逻辑要用的数据。
- 第 156-157 行：根据条件 `table_id is not None` 分支处理不同情况。
- 第 158 行：给 `state.visibility_scope` 赋值，准备后面逻辑要用的数据。
- 第 159 行：返回计算结果，把这个函数的最终答案交给调用者。

### `handle_client_event`（第 161-198 行）

签名：

```python
async def handle_client_event(self, connection_id: str, message: Any) -> None
```

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 162-168 行：根据条件 `not isinstance(message, dict)` 分支处理不同情况。
- 第 170 行：给 `event_type` 赋值，准备后面逻辑要用的数据。
- 第 171 行：给 `payload` 赋值，准备后面逻辑要用的数据。
- 第 172-178 行：根据条件 `not isinstance(event_type, str)` 分支处理不同情况。
- 第 179-185 行：根据条件 `event_type not in CLIENT_EVENT_TYPES` 分支处理不同情况。
- 第 187-189 行：根据条件 `event_type == 'request_snapshot'` 分支处理不同情况。
- 第 191-197 行：根据条件 `not isinstance(payload, dict)` 分支处理不同情况。
- 第 198 行：等待一个异步操作完成，常见于 WebSocket、控制器或异步队列。

### `broadcast_table_snapshot`（第 200-201 行）

签名：

```python
async def broadcast_table_snapshot(self, snapshot: Any, *, table_id: str | None = None) -> None
```

人话：向客户端、连接或订阅者发送消息。

关键代码块：

- 第 201 行：等待一个异步操作完成，常见于 WebSocket、控制器或异步队列。

### `broadcast_event`（第 203-214 行）

签名：

```python
async def broadcast_event(self, event_type: str, payload: Any, *, table_id: str | None = None) -> None
```

人话：向客户端、连接或订阅者发送消息。

关键代码块：

- 第 210-211 行：根据条件 `event_type not in BROADCAST_EVENT_TYPES` 分支处理不同情况。
- 第 213 行：给 `public_payload` 赋值，准备后面逻辑要用的数据。
- 第 214 行：等待一个异步操作完成，常见于 WebSocket、控制器或异步队列。

### `send_hole_cards_dealt`（第 216-229 行）

签名：

```python
async def send_hole_cards_dealt(self, player_id: str, seat_index: int, payload: Any, table_id: str | None = None) -> None
```

人话：向客户端、连接或订阅者发送消息。

关键代码块：

- 第 223-229 行：等待一个异步操作完成，常见于 WebSocket、控制器或异步队列。

### `send_action_requested`（第 231-259 行）

签名：

```python
async def send_action_requested(self, player_id: str, seat_index: int, payload: Any, table_id: str | None = None) -> None
```

人话：向客户端、连接或订阅者发送消息。

关键代码块：

- 第 238 行：给 `table_keys` 赋值，准备后面逻辑要用的数据。
- 第 239-240 行：根据条件 `not table_keys` 分支处理不同情况。
- 第 241 行：给 `hand_id` 赋值，准备后面逻辑要用的数据。
- 第 242 行：给 `turn_id` 赋值，准备后面逻辑要用的数据。
- 第 243-251 行：根据条件 `hand_id is not None and turn_id is not None` 分支处理不同情况。
- 第 253-259 行：等待一个异步操作完成，常见于 WebSocket、控制器或异步队列。

### `send_action_rejected`（第 261-277 行）

签名：

```python
async def send_action_rejected(self, connection_id: str, code: str, message: str, *, payload: dict[str, Any] | None = None) -> None
```

人话：向客户端、连接或订阅者发送消息。

关键代码块：

- 第 269-274 行：给 `error_payload` 赋值，准备后面逻辑要用的数据。
- 第 275-276 行：根据条件 `payload` 分支处理不同情况。
- 第 277 行：等待一个异步操作完成，常见于 WebSocket、控制器或异步队列。

### `send_action_rejected_to_player`（第 279-292 行）

签名：

```python
async def send_action_rejected_to_player(self, player_id: str, seat_index: int, payload: Any, table_id: str | None = None) -> None
```

人话：向客户端、连接或订阅者发送消息。

关键代码块：

- 第 286-292 行：等待一个异步操作完成，常见于 WebSocket、控制器或异步队列。

### `send_private_event`（第 294-310 行）

签名：

```python
async def send_private_event(self, event_type: str, payload: Any, *, player_id: str, seat_index: int, table_id: str | None = None) -> None
```

人话：向客户端、连接或订阅者发送消息。

关键代码块：

- 第 303-304 行：根据条件 `event_type not in PRIVATE_EVENT_TYPES` 分支处理不同情况。
- 第 306-310 行：循环遍历 `list(self.connections.values())`，逐个处理里面的元素。

### `send_to_connection`（第 312-320 行）

签名：

```python
async def send_to_connection(self, connection_id: str, event_type: str, payload: Any) -> None
```

人话：向客户端、连接或订阅者发送消息。

关键代码块：

- 第 313 行：给 `state` 赋值，准备后面逻辑要用的数据。
- 第 314-320 行：等待一个异步操作完成，常见于 WebSocket、控制器或异步队列。

### `_handle_request_snapshot`（第 322-344 行）

签名：

```python
async def _handle_request_snapshot(self, connection_id: str) -> None
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 323 行：给 `state` 赋值，准备后面逻辑要用的数据。
- 第 324-330 行：根据条件 `self.table_manager is None` 分支处理不同情况。
- 第 332-342 行：尝试执行可能失败的操作，并在异常发生时转成项目自己的处理方式。
- 第 344 行：等待一个异步操作完成，常见于 WebSocket、控制器或异步队列。

### `_handle_submit_action`（第 346-433 行）

签名：

```python
async def _handle_submit_action(self, connection_id: str, payload: dict[str, Any]) -> None
```

人话：提交动作或请求，把外部输入交给下一层处理。

关键代码块：

- 第 347 行：给 `missing_fields` 赋值，准备后面逻辑要用的数据。
- 第 348-355 行：根据条件 `missing_fields` 分支处理不同情况。
- 第 357 行：给 `action_type` 赋值，准备后面逻辑要用的数据。
- 第 358-364 行：根据条件 `action_type == 'RaiseTo' and payload.get('amount') is None` 分支处理不同情况。
- 第 365-371 行：根据条件 `action_type != 'RaiseTo' and payload.get('amount') is not None` 分支处理不同情况。
- 第 373 行：给 `state` 赋值，准备后面逻辑要用的数据。
- 第 374 行：给 `player_id` 赋值，准备后面逻辑要用的数据。
- 第 375 行：给 `seat_index` 赋值，准备后面逻辑要用的数据。
- 第 376-382 行：根据条件 `state.player_id is None or state.seat_index is None` 分支处理不同情况。
- 第 383-389 行：根据条件 `player_id != state.player_id or seat_index != state.seat_index` 分支处理不同情况。
- 第 391 行：给 `pending_turn` 赋值，准备后面逻辑要用的数据。
- 第 392-408 行：根据条件 `pending_turn is not None` 分支处理不同情况。
- 第 410-416 行：根据条件 `self.human_controller is None` 分支处理不同情况。
- 第 418-427 行：尝试执行可能失败的操作，并在异常发生时转成项目自己的处理方式。
- 第 429-433 行：根据条件 `isinstance(result, dict) and result.get('ok') is False` 分支处理不同情况。

### `_send_to_matching_connections`（第 435-445 行）

签名：

```python
async def _send_to_matching_connections(self, event_type: str, payload: Any, *, table_id: str | None = None) -> None
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 442-445 行：循环遍历 `list(self.connections.values())`，逐个处理里面的元素。

### `_send_socket_json`（第 447-456 行）

签名：

```python
async def _send_socket_json(self, socket: Any, message: dict[str, Any]) -> None
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 448-453 行：根据条件 `hasattr(socket, 'send_json')` 分支处理不同情况。
- 第 455-456 行：根据条件 `inspect.isawaitable(result)` 分支处理不同情况。

### `_require_connection`（第 458-465 行）

签名：

```python
def _require_connection(self, connection_id: str) -> ConnectionState
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 459-465 行：尝试执行可能失败的操作，并在异常发生时转成项目自己的处理方式。

### `_matching_table_ids`（第 467-479 行）

签名：

```python
def _matching_table_ids(self, player_id: str, seat_index: int, table_id: str | None) -> set[str]
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 473-474 行：根据条件 `table_id is not None` 分支处理不同情况。
- 第 475-479 行：返回计算结果，把这个函数的最终答案交给调用者。

## 模块级函数

### `_call_service_method`（第 482-500 行）

签名：

```python
async def _call_service_method(service: Any, method_names: tuple[str, ...], payload: dict[str, Any], positional_order: tuple[str, ...] = ()) -> Any
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 488 行：给 `target` 赋值，准备后面逻辑要用的数据。
- 第 489-493 行：循环遍历 `method_names`，逐个处理里面的元素。
- 第 494-495 行：根据条件 `target is None` 分支处理不同情况。
- 第 497 行：给 `result` 赋值，准备后面逻辑要用的数据。
- 第 498-499 行：根据条件 `inspect.isawaitable(result)` 分支处理不同情况。
- 第 500 行：返回计算结果，把这个函数的最终答案交给调用者。

### `_call_with_supported_arguments`（第 503-539 行）

签名：

```python
def _call_with_supported_arguments(target: Any, payload: dict[str, Any], positional_order: tuple[str, ...]) -> Any
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 508 行：给 `signature` 赋值，准备后面逻辑要用的数据。
- 第 509 行：给 `parameters` 赋值，准备后面逻辑要用的数据。
- 第 511-512 行：根据条件 `any((parameter.kind == inspect.Parameter.VAR_KEYWORD for parameter in parameters))` 分支处理不同情况。
- 第 514-519 行：给 `supported_keyword_names` 赋值，准备后面逻辑要用的数据。
- 第 520-521 行：根据条件 `set(payload).issubset(supported_keyword_names)` 分支处理不同情况。
- 第 523-528 行：给 `positional_parameters` 赋值，准备后面逻辑要用的数据。
- 第 529-530 行：根据条件 `not positional_parameters` 分支处理不同情况。
- 第 532-533 行：根据条件 `len(positional_parameters) == 1 and (not positional_order)` 分支处理不同情况。
- 第 535 行：给 `ordered_args` 赋值，准备后面逻辑要用的数据。
- 第 536-537 行：根据条件 `len(positional_parameters) == 1 and ordered_args` 分支处理不同情况。
- 第 539 行：返回计算结果，把这个函数的最终答案交给调用者。

### `_payload_str`（第 542-545 行）

签名：

```python
def _payload_str(payload: Any, key: str) -> str | None
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 543-544 行：根据条件 `isinstance(payload, dict) and payload.get(key) is not None` 分支处理不同情况。
- 第 545 行：返回计算结果，把这个函数的最终答案交给调用者。

### `_parse_optional_int`（第 548-554 行）

签名：

```python
def _parse_optional_int(value: str | None) -> int | None
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 549-550 行：根据条件 `value is None or value == ''` 分支处理不同情况。
- 第 551-554 行：尝试执行可能失败的操作，并在异常发生时转成项目自己的处理方式。

### `_encode_event_payload`（第 557-560 行）

签名：

```python
def _encode_event_payload(event_type: str, payload: Any) -> Any
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 558-559 行：根据条件 `event_type == 'table_snapshot' or event_type in BROADCAST_EVENT_TYPES` 分支处理不同情况。
- 第 560 行：返回计算结果，把这个函数的最终答案交给调用者。

### `_to_json_dto`（第 563-599 行）

签名：

```python
def _to_json_dto(value: Any) -> Any
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 564-565 行：根据条件 `value is None or isinstance(value, str | int | float | bool)` 分支处理不同情况。
- 第 567 行：给 `value_type` 赋值，准备后面逻辑要用的数据。
- 第 568-569 行：根据条件 `'pokerkit' in getattr(value_type, '__module__', '').lower()` 分支处理不同情况。
- 第 571-576 行：根据条件 `isinstance(value, dict)` 分支处理不同情况。
- 第 578-579 行：根据条件 `isinstance(value, list | tuple | set | frozenset)` 分支处理不同情况。
- 第 581-582 行：根据条件 `hasattr(value, 'model_dump')` 分支处理不同情况。
- 第 584-587 行：根据条件 `hasattr(value, '__dataclass_fields__')` 分支处理不同情况。
- 第 589-590 行：根据条件 `hasattr(value, '__dict__')` 分支处理不同情况。
- 第 592-595 行：尝试执行可能失败的操作，并在异常发生时转成项目自己的处理方式。
- 第 596-599 行：尝试执行可能失败的操作，并在异常发生时转成项目自己的处理方式。

## 对外公开接口

`__all__` 声明这个模块希望别人主要使用这些名字：

- `ConnectionState`
- `PendingTurn`
- `WebSocketGateway`

## 初学者阅读建议

先看“这个文件是干什么的”，再看类和函数标题。遇到以下划线开头的函数，可以先理解成内部工具；遇到 `to_dict/from_dict/to_json/from_json`，重点记住它们是在对象、字典和 JSON 之间转换。
