# `mcx_poker/delivery/api.py` 人话讲解

源文件：`/Users/machengqi/Documents/mcx-poker/src/mcx_poker/delivery/api.py`

## 这个文件是干什么的

源码说明：FastAPI delivery boundary for local table control.

The delivery layer intentionally depends on injected services instead of poker
engine internals. Table managers and human controllers can be synchronous or
asynchronous; tests use fakes and the real app can provide concrete services
later.

人话概括：

负责把牌桌/玩家动作和外部世界连接起来，例如本地运行、HTTP API 或 WebSocket。

## 导入区

- 第 9 行：从 `__future__` 导入 `annotations`。
- 第 11 行：导入 `inspect`。
- 第 12 行：从 `collections.abc` 导入 `Awaitable, Callable, Mapping`。
- 第 13 行：从 `pathlib` 导入 `Path`。
- 第 14 行：从 `typing` 导入 `Any, Literal, Protocol`。
- 第 16 行：导入 `uvicorn`。
- 第 17 行：从 `fastapi` 导入 `Body, Depends, FastAPI, Request, status`。
- 第 18 行：从 `fastapi.encoders` 导入 `jsonable_encoder`。
- 第 19 行：从 `fastapi.exceptions` 导入 `RequestValidationError`。
- 第 20 行：从 `fastapi.responses` 导入 `JSONResponse`。
- 第 21 行：从 `fastapi.staticfiles` 导入 `StaticFiles`。
- 第 22 行：从 `pydantic` 导入 `BaseModel, ConfigDict, Field, field_validator`。

人话：导入区是在声明“这个文件需要哪些外部工具”。标准库通常提供基础能力，项目内导入则说明它依赖哪些业务模块。

## 顶层常量和类型

- 第 24 行：`ApiRouteReturn` = `dict[str, Any] | JSONResponse`。人话：在模块级别准备一个后面会反复使用的值。
- 第 25 行：`DEFAULT_LOCAL_TABLE_ID` = `'local-table'`。人话：在模块级别准备一个后面会反复使用的值。
- 第 26 行：`STATIC_DIR` = `Path(__file__).resolve().parent / 'static'`。人话：在模块级别准备一个后面会反复使用的值。
- 第 28-43 行：`ErrorCode` = `Literal['invalid_request', 'table_not_initialized', 'table_state_conflict', 'seat_not_found', 'seat_occupied', 'player_already_seated', 'unknown_controller_type', 'game_not_started', 'internal_error', 'connection_not_bound_to_player', 'stale_turn', 'not_current_actor', 'action_rejected', 'table_unavailable']`。人话：在模块级别准备一个后面会反复使用的值。
- 第 223 行：`PUBLIC_CONTROLLER_TYPES` = `{'human', 'bot'}`。人话：在模块级别准备一个后面会反复使用的值。
- 第 224-231 行：`HIDDEN_SNAPSHOT_KEYS` = `{'adapter_hand_ref', 'deck', 'hole_cards', 'hidden_hole_cards', 'private_cards', 'private_hole_cards'}`。人话：在模块级别准备一个后面会反复使用的值。
- 第 232-247 行：`ERROR_STATUS` = `{'invalid_request': status.HTTP_400_BAD_REQUEST, 'unknown_controller_type': status.HTTP_400_BAD_REQUEST, 'seat_not_found': status.HTTP_404_NOT_FOUND, 'table_not_initialized': status.HTTP_404_NOT_FOUND, 'table_unavailable': status.HTTP_503_SERVICE_UNAVAILABLE, 'seat_occupied': status.HTTP_409_CONFLICT, 'player_already_seated': status.HTTP_409_CONFLICT, 'table_state_conflict': status.HTTP_409_CONFLICT, 'game_not_started': status.HTTP_409_CONFLICT, 'connection_not_bound_to_player': status.HTTP_409_CONFLICT, 'stale_turn': status.HTTP_409_CONFLICT, 'not_current_actor': status.HTTP_409_CONFLICT, 'action_rejected': status.HTTP_409_CONFLICT, 'internal_error': status.HTTP_500_INTERNAL_SERVER_ERROR}`。人话：在模块级别准备一个后面会反复使用的值。
- 第 764 行：`app` = `create_default_app()`。人话：在模块级别准备一个后面会反复使用的值。
- 第 773-789 行：`__all__` = `['ApiError', 'ApiResponse', 'DeliveryError', 'HumanControllerProtocol', 'PlayerActionRequest', 'SeatPlayerRequest', 'TableControlRequest', 'TableManagerProtocol', 'app', 'create_app', 'create_default_app', 'error_response', 'main', 'success_response', 'to_public_dto']`。人话：在模块级别准备一个后面会反复使用的值。

## 类 `ApiError`（第 46-51 行）

继承：`BaseModel`。

源码说明：Stable platform error returned to API clients.

人话：把一组相关数据和行为封装到一个类型里，供其他模块按统一接口使用。

字段/类变量：

- `code`：类型 `str`。
- `message`：类型 `str`。
- `details`：类型 `dict[str, Any] | None`，默认值 `None`。

## 类 `ApiResponse`（第 54-59 行）

继承：`BaseModel`。

源码说明：Uniform HTTP response envelope.

人话：把一组相关数据和行为封装到一个类型里，供其他模块按统一接口使用。

字段/类变量：

- `ok`：类型 `bool`。
- `data`：类型 `Any`，默认值 `None`。
- `error`：类型 `ApiError | None`，默认值 `None`。

## 类 `DeliveryError`（第 62-77 行）

继承：`Exception`。

源码说明：Platform-layer error that can be rendered as an ApiResponse.

人话：把一组相关数据和行为封装到一个类型里，供其他模块按统一接口使用。

这个类里的方法：

### `__init__`（第 65-77 行）

签名：

```python
def __init__(self, code: str, message: str | None = None, *, status_code: int | None = None, details: Mapping[str, Any] | None = None) -> None
```

人话：初始化对象，接收外部传入的数据并准备对象内部状态。

关键代码块：

- 第 73 行：调用 `super().__init__`，执行一个有副作用或校验性质的动作。
- 第 74 行：给 `self.code` 赋值，准备后面逻辑要用的数据。
- 第 75 行：给 `self.message` 赋值，准备后面逻辑要用的数据。
- 第 76 行：给 `self.status_code` 赋值，准备后面逻辑要用的数据。
- 第 77 行：给 `self.details` 赋值，准备后面逻辑要用的数据。

## 类 `TableManagerProtocol`（第 80-101 行）

继承：`Protocol`。

源码说明：Minimal table-manager surface consumed by the delivery API.

人话：把一组相关数据和行为封装到一个类型里，供其他模块按统一接口使用。

这个类里的方法：

### `initialize_table`（第 83 行）

签名：

```python
def initialize_table(self, config: Mapping[str, Any] | None = None) -> Any
```

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 83 行：执行一个表达式，通常是调用函数或触发某个对象行为。

### `seat_player`（第 85-91 行）

签名：

```python
def seat_player(self, seat_index: int, player_name: str, controller_type: str, starting_stack: int) -> Any
```

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 91 行：执行一个表达式，通常是调用函数或触发某个对象行为。

### `start_table`（第 93 行）

签名：

```python
def start_table(self, table_id: str) -> Any
```

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 93 行：执行一个表达式，通常是调用函数或触发某个对象行为。

### `pause_table`（第 95 行）

签名：

```python
def pause_table(self, table_id: str) -> Any
```

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 95 行：执行一个表达式，通常是调用函数或触发某个对象行为。

### `resume_table`（第 97 行）

签名：

```python
def resume_table(self, table_id: str) -> Any
```

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 97 行：执行一个表达式，通常是调用函数或触发某个对象行为。

### `reset_table`（第 99 行）

签名：

```python
def reset_table(self, table_id: str) -> Any
```

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 99 行：执行一个表达式，通常是调用函数或触发某个对象行为。

### `get_table`（第 101 行）

签名：

```python
def get_table(self, table_id: str) -> Any
```

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 101 行：执行一个表达式，通常是调用函数或触发某个对象行为。

## 类 `HumanControllerProtocol`（第 104-111 行）

继承：`Protocol`。

源码说明：Optional human-controller hooks used at delivery boundaries.

人话：把一组相关数据和行为封装到一个类型里，供其他模块按统一接口使用。

这个类里的方法：

### `submit_action`（第 107 行）

签名：

```python
def submit_action(self, action: Mapping[str, Any]) -> Any
```

人话：提交动作或请求，把外部输入交给下一层处理。

关键代码块：

- 第 107 行：执行一个表达式，通常是调用函数或触发某个对象行为。

### `invalidate_pending_actions`（第 109 行）

签名：

```python
def invalidate_pending_actions(self, table_id: str) -> Any
```

人话：校验输入或状态是否合法，发现问题时返回错误或抛出异常。

关键代码块：

- 第 109 行：执行一个表达式，通常是调用函数或触发某个对象行为。

### `on_table_paused`（第 111 行）

签名：

```python
def on_table_paused(self, table_id: str) -> Any
```

人话：事件回调函数，在某个牌桌或连接事件发生时被调用。

关键代码块：

- 第 111 行：执行一个表达式，通常是调用函数或触发某个对象行为。

## 类 `SeatPlayerRequest`（第 114-144 行）

继承：`BaseModel`。

源码说明：Request body for seating a player.

人话：把一组相关数据和行为封装到一个类型里，供其他模块按统一接口使用。

字段/类变量：

- `model_config`：类级变量，值 `ConfigDict(extra='forbid')`。
- `seat_index`：类型 `int`。
- `player_name`：类型 `str`，默认值 `Field(min_length=1)`。
- `controller_type`：类型 `str`，默认值 `Field(min_length=1)`。
- `starting_stack`：类型 `int`。

这个类里的方法：

### `validate_seat_index`（第 126-129 行）

签名：

```python
def validate_seat_index(cls, value: int) -> int
```

装饰器：`@field_validator('seat_index')`、`@classmethod`。

人话：校验输入或状态是否合法，发现问题时返回错误或抛出异常。

关键代码块：

- 第 127-128 行：根据条件 `value < 0 or value > 5` 分支处理不同情况。
- 第 129 行：返回计算结果，把这个函数的最终答案交给调用者。

### `validate_player_name`（第 133-137 行）

签名：

```python
def validate_player_name(cls, value: str) -> str
```

装饰器：`@field_validator('player_name')`、`@classmethod`。

人话：校验输入或状态是否合法，发现问题时返回错误或抛出异常。

关键代码块：

- 第 134 行：给 `stripped` 赋值，准备后面逻辑要用的数据。
- 第 135-136 行：根据条件 `not stripped` 分支处理不同情况。
- 第 137 行：返回计算结果，把这个函数的最终答案交给调用者。

### `validate_starting_stack`（第 141-144 行）

签名：

```python
def validate_starting_stack(cls, value: int) -> int
```

装饰器：`@field_validator('starting_stack')`、`@classmethod`。

人话：校验输入或状态是否合法，发现问题时返回错误或抛出异常。

关键代码块：

- 第 142-143 行：根据条件 `value <= 0` 分支处理不同情况。
- 第 144 行：返回计算结果，把这个函数的最终答案交给调用者。

## 类 `TableControlRequest`（第 147-161 行）

继承：`BaseModel`。

源码说明：Request body for table control operations.

人话：把一组相关数据和行为封装到一个类型里，供其他模块按统一接口使用。

字段/类变量：

- `model_config`：类级变量，值 `ConfigDict(extra='forbid')`。
- `table_id`：类型 `str`，默认值 `Field(min_length=1)`。
- `command`：类型 `Literal['start', 'pause', 'resume', 'reset']`。

这个类里的方法：

### `validate_table_id`（第 157-161 行）

签名：

```python
def validate_table_id(cls, value: str) -> str
```

装饰器：`@field_validator('table_id')`、`@classmethod`。

人话：校验输入或状态是否合法，发现问题时返回错误或抛出异常。

关键代码块：

- 第 158 行：给 `stripped` 赋值，准备后面逻辑要用的数据。
- 第 159-160 行：根据条件 `not stripped` 分支处理不同情况。
- 第 161 行：返回计算结果，把这个函数的最终答案交给调用者。

## 类 `PlayerActionRequest`（第 164-189 行）

继承：`BaseModel`。

源码说明：Reserved HTTP shape for future human action submission.

人话：把一组相关数据和行为封装到一个类型里，供其他模块按统一接口使用。

字段/类变量：

- `model_config`：类级变量，值 `ConfigDict(extra='forbid')`。
- `player_id`：类型 `str`，默认值 `Field(min_length=1)`。
- `seat_index`：类型 `int`。
- `hand_id`：类型 `str`，默认值 `Field(min_length=1)`。
- `turn_id`：类型 `str`，默认值 `Field(min_length=1)`。
- `action_type`：类型 `str`，默认值 `Field(min_length=1)`。
- `amount`：类型 `int | None`，默认值 `None`。
- `source`：类型 `str`，默认值 `'human'`。

这个类里的方法：

### `validate_seat_index`（第 179-182 行）

签名：

```python
def validate_seat_index(cls, value: int) -> int
```

装饰器：`@field_validator('seat_index')`、`@classmethod`。

人话：校验输入或状态是否合法，发现问题时返回错误或抛出异常。

关键代码块：

- 第 180-181 行：根据条件 `value < 0 or value > 5` 分支处理不同情况。
- 第 182 行：返回计算结果，把这个函数的最终答案交给调用者。

### `validate_amount`（第 186-189 行）

签名：

```python
def validate_amount(cls, value: int | None) -> int | None
```

装饰器：`@field_validator('amount')`、`@classmethod`。

人话：校验输入或状态是否合法，发现问题时返回错误或抛出异常。

关键代码块：

- 第 187-188 行：根据条件 `value is not None and value <= 0` 分支处理不同情况。
- 第 189 行：返回计算结果，把这个函数的最终答案交给调用者。

## 类 `_UnavailableTableManager`（第 192-220 行）

源码说明：Default app dependency until a real table manager is wired in.

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

这个类里的方法：

### `initialize_table`（第 195-196 行）

签名：

```python
def initialize_table(self, config: Mapping[str, Any] | None = None) -> Any
```

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 196 行：主动抛出错误，表示传入数据或当前状态不符合要求。

### `seat_player`（第 198-205 行）

签名：

```python
def seat_player(self, seat_index: int, player_name: str, controller_type: str, starting_stack: int) -> Any
```

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 205 行：主动抛出错误，表示传入数据或当前状态不符合要求。

### `start_table`（第 207-208 行）

签名：

```python
def start_table(self, table_id: str) -> Any
```

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 208 行：主动抛出错误，表示传入数据或当前状态不符合要求。

### `pause_table`（第 210-211 行）

签名：

```python
def pause_table(self, table_id: str) -> Any
```

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 211 行：主动抛出错误，表示传入数据或当前状态不符合要求。

### `resume_table`（第 213-214 行）

签名：

```python
def resume_table(self, table_id: str) -> Any
```

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 214 行：主动抛出错误，表示传入数据或当前状态不符合要求。

### `reset_table`（第 216-217 行）

签名：

```python
def reset_table(self, table_id: str) -> Any
```

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 217 行：主动抛出错误，表示传入数据或当前状态不符合要求。

### `get_table`（第 219-220 行）

签名：

```python
def get_table(self, table_id: str) -> Any
```

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 220 行：主动抛出错误，表示传入数据或当前状态不符合要求。

## 模块级函数

### `status_for_error`（第 250-251 行）

签名：

```python
def status_for_error(code: str) -> int
```

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 251 行：返回计算结果，把这个函数的最终答案交给调用者。

### `success_response`（第 254-255 行）

签名：

```python
def success_response(data: Any) -> dict[str, Any]
```

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 255 行：返回计算结果，把这个函数的最终答案交给调用者。

### `error_response`（第 258-271 行）

签名：

```python
def error_response(code: str, message: str | None = None, *, status_code: int | None = None, details: Mapping[str, Any] | None = None) -> JSONResponse
```

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 265-269 行：给 `error` 赋值，准备后面逻辑要用的数据。
- 第 270 行：给 `body` 赋值，准备后面逻辑要用的数据。
- 第 271 行：返回计算结果，把这个函数的最终答案交给调用者。

### `to_public_dto`（第 274-311 行）

签名：

```python
def to_public_dto(value: Any) -> Any
```

源码说明：Convert platform DTOs into JSON-safe data while dropping hidden fields.

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 277-278 行：根据条件 `value is None or isinstance(value, str | int | float | bool)` 分支处理不同情况。
- 第 280 行：给 `value_type` 赋值，准备后面逻辑要用的数据。
- 第 281-282 行：根据条件 `'pokerkit' in getattr(value_type, '__module__', '').lower()` 分支处理不同情况。
- 第 284-292 行：根据条件 `isinstance(value, Mapping)` 分支处理不同情况。
- 第 294-295 行：根据条件 `isinstance(value, list | tuple | set | frozenset)` 分支处理不同情况。
- 第 297-298 行：根据条件 `hasattr(value, 'model_dump')` 分支处理不同情况。
- 第 300-303 行：根据条件 `hasattr(value, '__dataclass_fields__')` 分支处理不同情况。
- 第 305-306 行：根据条件 `hasattr(value, '__dict__')` 分支处理不同情况。
- 第 308-311 行：尝试执行可能失败的操作，并在异常发生时转成项目自己的处理方式。

### `create_app`（第 314-589 行）

签名：

```python
def create_app(table_manager: Any | None = None, *, human_controller: Any | None = None, websocket_gateway: Any | None = None) -> FastAPI
```

源码说明：Create the FastAPI app with injected delivery dependencies.

人话：创建并返回一个新对象，通常会把多个输入整理到统一格式。

关键代码块：

- 第 322 行：给 `manager` 赋值，准备后面逻辑要用的数据。
- 第 323 行：给 `app` 赋值，准备后面逻辑要用的数据。
- 第 324 行：给 `app.state.table_manager` 赋值，准备后面逻辑要用的数据。
- 第 325 行：给 `app.state.human_controller` 赋值，准备后面逻辑要用的数据。
- 第 328-337 行：定义函数 `validation_exception_handler`。
- 第 340-346 行：定义函数 `delivery_exception_handler`。
- 第 349-350 行：定义函数 `health`。
- 第 352-353 行：定义函数 `manager_dep`。
- 第 355-356 行：定义函数 `human_controller_dep`。
- 第 358 行：给 `initialize_body` 赋值，准备后面逻辑要用的数据。
- 第 359 行：给 `manager_dependency` 赋值，准备后面逻辑要用的数据。
- 第 360 行：给 `human_controller_dependency` 赋值，准备后面逻辑要用的数据。
- 第 362-372 行：定义函数 `initialize_table`。
- 第 374-398 行：定义函数 `seat_player`。
- 第 400-434 行：定义函数 `table_control`。
- 第 436-447 行：定义函数 `start_table`。
- 后面还有 30 个语句块，主要继续完成这个函数的收尾、返回或异常处理。

### `_run_api_operation`（第 592-618 行）

签名：

```python
async def _run_api_operation(operation: Callable[[], Any]) -> ApiRouteReturn
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 593-618 行：尝试执行可能失败的操作，并在异常发生时转成项目自己的处理方式。

### `map_exception`（第 621-665 行）

签名：

```python
def map_exception(exc: Exception) -> DeliveryError
```

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 622-623 行：根据条件 `isinstance(exc, DeliveryError)` 分支处理不同情况。
- 第 625 行：给 `code` 赋值，准备后面逻辑要用的数据。
- 第 626 行：给 `message` 赋值，准备后面逻辑要用的数据。
- 第 627 行：给 `details` 赋值，准备后面逻辑要用的数据。
- 第 629-632 行：根据条件 `code is None and exc.args` 分支处理不同情况。
- 第 634-635 行：根据条件 `isinstance(code, str) and code in ERROR_STATUS and (code != 'internal_error')` 分支处理不同情况。
- 第 637 行：给 `class_name` 赋值，准备后面逻辑要用的数据。
- 第 638-651 行：给 `class_name_map` 赋值，准备后面逻辑要用的数据。
- 第 652-659 行：根据条件 `class_name in class_name_map` 分支处理不同情况。
- 第 661-665 行：返回计算结果，把这个函数的最终答案交给调用者。

### `_call_service_method`（第 668-679 行）

签名：

```python
async def _call_service_method(service: Any, method_names: tuple[str, ...], *, payload: Mapping[str, Any] | None = None, positional_order: tuple[str, ...] = ()) -> Any
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 675 行：给 `target` 赋值，准备后面逻辑要用的数据。
- 第 676 行：给 `result` 赋值，准备后面逻辑要用的数据。
- 第 677-678 行：根据条件 `inspect.isawaitable(result)` 分支处理不同情况。
- 第 679 行：返回计算结果，把这个函数的最终答案交给调用者。

### `_find_method`（第 682-688 行）

签名：

```python
def _find_method(service: Any, method_names: tuple[str, ...]) -> Callable[..., Any]
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 683-686 行：循环遍历 `method_names`，逐个处理里面的元素。
- 第 687 行：给 `joined` 赋值，准备后面逻辑要用的数据。
- 第 688 行：主动抛出错误，表示传入数据或当前状态不符合要求。

### `_call_with_supported_arguments`（第 691-727 行）

签名：

```python
def _call_with_supported_arguments(target: Callable[..., Any], payload: Mapping[str, Any], positional_order: tuple[str, ...]) -> Any
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 696 行：给 `signature` 赋值，准备后面逻辑要用的数据。
- 第 697 行：给 `parameters` 赋值，准备后面逻辑要用的数据。
- 第 699-700 行：根据条件 `any((parameter.kind == inspect.Parameter.VAR_KEYWORD for parameter in parameters))` 分支处理不同情况。
- 第 702-707 行：给 `supported_keyword_names` 赋值，准备后面逻辑要用的数据。
- 第 708-709 行：根据条件 `payload and set(payload).issubset(supported_keyword_names)` 分支处理不同情况。
- 第 711-716 行：给 `positional_parameters` 赋值，准备后面逻辑要用的数据。
- 第 717-718 行：根据条件 `not positional_parameters` 分支处理不同情况。
- 第 720-721 行：根据条件 `len(positional_parameters) == 1 and (not positional_order)` 分支处理不同情况。
- 第 723 行：给 `ordered_args` 赋值，准备后面逻辑要用的数据。
- 第 724-725 行：根据条件 `len(positional_parameters) == 1 and ordered_args` 分支处理不同情况。
- 第 727 行：返回计算结果，把这个函数的最终答案交给调用者。

### `_notify_optional_hook`（第 730-744 行）

签名：

```python
async def _notify_optional_hook(service: Any | None, method_names: tuple[str, ...], table_id: str) -> None
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 735-736 行：根据条件 `service is None` 分支处理不同情况。
- 第 738-744 行：循环遍历 `method_names`，逐个处理里面的元素。

### `maybe_await`（第 747-748 行）

签名：

```python
def maybe_await(value: Any) -> Awaitable[Any] | Any
```

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 748 行：返回计算结果，把这个函数的最终答案交给调用者。

### `create_default_app`（第 751-761 行）

签名：

```python
def create_default_app() -> FastAPI
```

源码说明：Create the default local playable MVP app.

人话：创建并返回一个新对象，通常会把多个输入整理到统一格式。

关键代码块：

- 第 754 行：导入其他模块提供的类、函数或类型。
- 第 756 行：给 `service` 赋值，准备后面逻辑要用的数据。
- 第 757-761 行：返回计算结果，把这个函数的最终答案交给调用者。

### `main`（第 767-770 行）

签名：

```python
def main() -> None
```

源码说明：Local development entry point.

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 770 行：调用 `uvicorn.run`，执行一个有副作用或校验性质的动作。

## 对外公开接口

`__all__` 声明这个模块希望别人主要使用这些名字：

- `ApiError`
- `ApiResponse`
- `DeliveryError`
- `HumanControllerProtocol`
- `PlayerActionRequest`
- `SeatPlayerRequest`
- `TableControlRequest`
- `TableManagerProtocol`
- `app`
- `create_app`
- `create_default_app`
- `error_response`
- `main`
- `success_response`
- `to_public_dto`

## 初学者阅读建议

先看“这个文件是干什么的”，再看类和函数标题。遇到以下划线开头的函数，可以先理解成内部工具；遇到 `to_dict/from_dict/to_json/from_json`，重点记住它们是在对象、字典和 JSON 之间转换。
