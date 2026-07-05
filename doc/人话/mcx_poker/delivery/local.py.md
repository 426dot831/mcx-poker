# `mcx_poker/delivery/local.py` 人话讲解

源文件：`/Users/machengqi/Documents/mcx-poker/src/mcx_poker/delivery/local.py`

## 这个文件是干什么的

源码说明：Local MVP application composition.

This module wires the platform modules into a playable local prototype. It is
the composition root only; poker rules still enter exclusively through the
PokerKit adapter.

人话概括：

负责把牌桌/玩家动作和外部世界连接起来，例如本地运行、HTTP API 或 WebSocket。

## 导入区

- 第 8 行：从 `__future__` 导入 `annotations`。
- 第 10 行：导入 `asyncio`。
- 第 11 行：从 `collections.abc` 导入 `Mapping`。
- 第 12 行：从 `typing` 导入 `Any, cast`。
- 第 14 行：从 `mcx_poker.delivery.websocket` 导入 `WebSocketGateway`。
- 第 15 行：从 `mcx_poker.engine.game_loop` 导入 `GameLoop`。
- 第 16 行：从 `mcx_poker.engine.pokerkit_adapter` 导入 `PokerKitAdapter`。
- 第 17 行：从 `mcx_poker.engine.validator` 导入 `ActionContext, validate_action`。
- 第 18 行：从 `mcx_poker.history` 导入 `HandEventLog`。
- 第 19 行：从 `mcx_poker.observation` 导入 `build_player_observation`。
- 第 20 行：从 `mcx_poker.players` 导入 `BotPlayerController, ControllerRegistry, HumanPlayerController`。
- 第 21-28 行：从 `mcx_poker.table` 导入 `DEFAULT_STARTING_STACK, DEFAULT_TABLE_ID, ControllerType, TableManager, TableSnapshot, TableStatus`。

人话：导入区是在声明“这个文件需要哪些外部工具”。标准库通常提供基础能力，项目内导入则说明它依赖哪些业务模块。

## 顶层常量和类型

- 第 284-289 行：`__all__` = `['LocalActionValidator', 'LocalObservationSystem', 'LocalPokerService', 'create_local_service']`。人话：在模块级别准备一个后面会反复使用的值。

## 类 `LocalObservationSystem`（第 31-55 行）

源码说明：Adapter between GameLoop actor requests and observation builder inputs.

人话：把一组相关数据和行为封装到一个类型里，供其他模块按统一接口使用。

这个类里的方法：

### `__init__`（第 34-42 行）

签名：

```python
def __init__(self, table_manager: TableManager, adapter: PokerKitAdapter, event_log: HandEventLog) -> None
```

人话：初始化对象，接收外部传入的数据并准备对象内部状态。

关键代码块：

- 第 40 行：给 `self.table_manager` 赋值，准备后面逻辑要用的数据。
- 第 41 行：给 `self.adapter` 赋值，准备后面逻辑要用的数据。
- 第 42 行：给 `self.event_log` 赋值，准备后面逻辑要用的数据。

### `build`（第 44-55 行）

签名：

```python
def build(self, actor: Any, context: Any) -> Any
```

人话：根据已有状态组装更高层的数据对象。

关键代码块：

- 第 45 行：给 `table_snapshot` 赋值，准备后面逻辑要用的数据。
- 第 46 行：给 `state_summary` 赋值，准备后面逻辑要用的数据。
- 第 47 行：给 `public_events` 赋值，准备后面逻辑要用的数据。
- 第 48-55 行：返回计算结果，把这个函数的最终答案交给调用者。

## 类 `LocalActionValidator`（第 58-80 行）

源码说明：Supplies the current legal-action and table context to validate_action.

人话：把一组相关数据和行为封装到一个类型里，供其他模块按统一接口使用。

这个类里的方法：

### `__init__`（第 61-63 行）

签名：

```python
def __init__(self, table_manager: TableManager, adapter: PokerKitAdapter) -> None
```

人话：初始化对象，接收外部传入的数据并准备对象内部状态。

关键代码块：

- 第 62 行：给 `self.table_manager` 赋值，准备后面逻辑要用的数据。
- 第 63 行：给 `self.adapter` 赋值，准备后面逻辑要用的数据。

### `validate`（第 65-80 行）

签名：

```python
def validate(self, action: Any, context: Any) -> Any
```

人话：校验输入或状态是否合法，发现问题时返回错误或抛出异常。

关键代码块：

- 第 66 行：给 `state_summary` 赋值，准备后面逻辑要用的数据。
- 第 67-73 行：给 `validation_context` 赋值，准备后面逻辑要用的数据。
- 第 74 行：给 `table_snapshot` 赋值，准备后面逻辑要用的数据。
- 第 75-80 行：返回计算结果，把这个函数的最终答案交给调用者。

## 类 `LocalPokerService`（第 83-277 行）

源码说明：Single-table local MVP service consumed by FastAPI and WebSocket.

人话：把一组相关数据和行为封装到一个类型里，供其他模块按统一接口使用。

这个类里的方法：

### `__init__`（第 86-110 行）

签名：

```python
def __init__(self) -> None
```

人话：初始化对象，接收外部传入的数据并准备对象内部状态。

关键代码块：

- 第 87 行：给 `self.adapter` 赋值，准备后面逻辑要用的数据。
- 第 88 行：给 `self.table_manager` 赋值，准备后面逻辑要用的数据。
- 第 89 行：给 `self.event_log` 赋值，准备后面逻辑要用的数据。
- 第 90 行：给 `self.human_controller` 赋值，准备后面逻辑要用的数据。
- 第 91 行：给 `self.controller_registry` 赋值，准备后面逻辑要用的数据。
- 第 92-96 行：给 `self.observation_system` 赋值，准备后面逻辑要用的数据。
- 第 97 行：给 `self.action_validator` 赋值，准备后面逻辑要用的数据。
- 第 98 行：给 `self.websocket_gateway` 赋值，准备后面逻辑要用的数据。
- 第 99-107 行：给 `self.game_loop` 赋值，准备后面逻辑要用的数据。
- 第 108 行：声明字段或变量 `self._loop_task`，类型是 `asyncio.Task[Any] | None`。
- 第 109 行：调用 `self.initialize_table`，执行一个有副作用或校验性质的动作。
- 第 110 行：调用 `self._seat_default_players`，执行一个有副作用或校验性质的动作。

### `initialize_table`（第 112-118 行）

签名：

```python
def initialize_table(self, config: Mapping[str, Any] | None = None) -> dict[str, Any]
```

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 113 行：给 `snapshot` 赋值，准备后面逻辑要用的数据。
- 第 114 行：给 `self.controller_registry` 赋值，准备后面逻辑要用的数据。
- 第 115-116 行：根据条件 `hasattr(self, 'game_loop')` 分支处理不同情况。
- 第 117 行：给 `self._loop_task` 赋值，准备后面逻辑要用的数据。
- 第 118 行：返回计算结果，把这个函数的最终答案交给调用者。

### `seat_player`（第 120-136 行）

签名：

```python
def seat_player(self, seat_index: int, player_name: str, controller_type: str, starting_stack: int) -> dict[str, Any]
```

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 127-132 行：给 `snapshot` 赋值，准备后面逻辑要用的数据。
- 第 133 行：给 `seat` 赋值，准备后面逻辑要用的数据。
- 第 134-135 行：根据条件 `seat.player_id is not None` 分支处理不同情况。
- 第 136 行：返回计算结果，把这个函数的最终答案交给调用者。

### `start_table`（第 138-145 行）

签名：

```python
async def start_table(self, table_id: str = DEFAULT_TABLE_ID) -> dict[str, Any]
```

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 139 行：给 `snapshot` 赋值，准备后面逻辑要用的数据。
- 第 140-141 行：根据条件 `snapshot.status is TableStatus.IDLE` 分支处理不同情况。
- 第 142-143 行：根据条件 `snapshot.current_hand_id is None` 分支处理不同情况。
- 第 144 行：调用 `self._ensure_loop_running`，执行一个有副作用或校验性质的动作。
- 第 145 行：返回计算结果，把这个函数的最终答案交给调用者。

### `pause_table`（第 147-148 行）

签名：

```python
def pause_table(self, table_id: str = DEFAULT_TABLE_ID) -> dict[str, Any]
```

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 148 行：返回计算结果，把这个函数的最终答案交给调用者。

### `resume_table`（第 150-153 行）

签名：

```python
async def resume_table(self, table_id: str = DEFAULT_TABLE_ID) -> dict[str, Any]
```

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 151 行：给 `snapshot` 赋值，准备后面逻辑要用的数据。
- 第 152 行：调用 `self._ensure_loop_running`，执行一个有副作用或校验性质的动作。
- 第 153 行：返回计算结果，把这个函数的最终答案交给调用者。

### `reset_table`（第 155-162 行）

签名：

```python
async def reset_table(self, table_id: str = DEFAULT_TABLE_ID) -> dict[str, Any]
```

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 156-158 行：根据条件 `self._loop_task is not None` 分支处理不同情况。
- 第 159 行：等待一个异步操作完成，常见于 WebSocket、控制器或异步队列。
- 第 160 行：给 `snapshot` 赋值，准备后面逻辑要用的数据。
- 第 161 行：调用 `self._seat_default_players`，执行一个有副作用或校验性质的动作。
- 第 162 行：返回计算结果，把这个函数的最终答案交给调用者。

### `get_table`（第 164-165 行）

签名：

```python
def get_table(self, table_id: str = DEFAULT_TABLE_ID) -> dict[str, Any]
```

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 165 行：返回计算结果，把这个函数的最终答案交给调用者。

### `submit_action`（第 167-169 行）

签名：

```python
async def submit_action(self, action: Mapping[str, Any]) -> dict[str, Any]
```

人话：提交动作或请求，把外部输入交给下一层处理。

关键代码块：

- 第 168 行：给 `submitted` 赋值，准备后面逻辑要用的数据。
- 第 169 行：返回计算结果，把这个函数的最终答案交给调用者。

### `invalidate_pending_actions`（第 171-173 行）

签名：

```python
async def invalidate_pending_actions(self, table_id: str) -> None
```

人话：校验输入或状态是否合法，发现问题时返回错误或抛出异常。

关键代码块：

- 第 172 行：处理 `Delete` 语句。
- 第 173 行：等待一个异步操作完成，常见于 WebSocket、控制器或异步队列。

### `on_table_paused`（第 175-176 行）

签名：

```python
async def on_table_paused(self, table_id: str) -> None
```

人话：事件回调函数，在某个牌桌或连接事件发生时被调用。

关键代码块：

- 第 176 行：处理 `Delete` 语句。

### `_seat_default_players`（第 178-204 行）

签名：

```python
def _seat_default_players(self) -> None
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 179 行：给 `snapshot` 赋值，准备后面逻辑要用的数据。
- 第 180-181 行：根据条件 `any((seat.player_id is not None for seat in snapshot.seats))` 分支处理不同情况。
- 第 182-188 行：调用 `self.table_manager.seat_player`，执行一个有副作用或校验性质的动作。
- 第 189-194 行：调用 `self.controller_registry.register`，执行一个有副作用或校验性质的动作。
- 第 195-204 行：循环遍历 `range(1, 6)`，逐个处理里面的元素。

### `_register_controller`（第 206-219 行）

签名：

```python
def _register_controller(self, player_id: str, seat_index: int, controller_type: str) -> None
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 212 行：给 `normalized_type` 赋值，准备后面逻辑要用的数据。
- 第 213 行：给 `controller` 赋值，准备后面逻辑要用的数据。
- 第 214-219 行：调用 `self.controller_registry.register`，执行一个有副作用或校验性质的动作。

### `_ensure_loop_running`（第 221-227 行）

签名：

```python
def _ensure_loop_running(self) -> None
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 222-223 行：根据条件 `self._loop_task is not None and (not self._loop_task.done())` 分支处理不同情况。
- 第 224 行：给 `context` 赋值，准备后面逻辑要用的数据。
- 第 225-226 行：根据条件 `context is None` 分支处理不同情况。
- 第 227 行：给 `self._loop_task` 赋值，准备后面逻辑要用的数据。

### `_run_table_loop`（第 229-236 行）

签名：

```python
async def _run_table_loop(self) -> None
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 230-236 行：只要 `True` 还成立，就持续执行循环。

### `_public_snapshot`（第 238-277 行）

签名：

```python
def _public_snapshot(self, snapshot: TableSnapshot) -> dict[str, Any]
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 239 行：给 `payload` 赋值，准备后面逻辑要用的数据。
- 第 240 行：给 `hand_id` 赋值，准备后面逻辑要用的数据。
- 第 241-276 行：根据条件 `hand_id is not None` 分支处理不同情况。
- 第 277 行：返回计算结果，把这个函数的最终答案交给调用者。

## 模块级函数

### `create_local_service`（第 280-281 行）

签名：

```python
def create_local_service() -> LocalPokerService
```

人话：创建并返回一个新对象，通常会把多个输入整理到统一格式。

关键代码块：

- 第 281 行：返回计算结果，把这个函数的最终答案交给调用者。

## 对外公开接口

`__all__` 声明这个模块希望别人主要使用这些名字：

- `LocalActionValidator`
- `LocalObservationSystem`
- `LocalPokerService`
- `create_local_service`

## 初学者阅读建议

先看“这个文件是干什么的”，再看类和函数标题。遇到以下划线开头的函数，可以先理解成内部工具；遇到 `to_dict/from_dict/to_json/from_json`，重点记住它们是在对象、字典和 JSON 之间转换。
