# `mcx_poker/engine/game_loop.py` 人话讲解

源文件：`/Users/machengqi/Documents/mcx-poker/src/mcx_poker/engine/game_loop.py`

## 这个文件是干什么的

源码说明：Asynchronous hand driver for platform-level poker services.

人话概括：

属于牌局引擎层，负责动作、校验、游戏循环或 PokerKit 适配。

## 导入区

- 第 3 行：从 `__future__` 导入 `annotations`。
- 第 5 行：导入 `asyncio`。
- 第 6 行：导入 `inspect`。
- 第 7 行：从 `collections.abc` 导入 `Mapping, Sequence`。
- 第 8 行：从 `dataclasses` 导入 `dataclass, fields, is_dataclass`。
- 第 9 行：从 `enum` 导入 `Enum`。
- 第 10 行：从 `typing` 导入 `Any, Literal, Protocol`。
- 第 11 行：从 `uuid` 导入 `uuid4`。
- 第 13 行：从 `mcx_poker.engine.actions` 导入 `ActionError`。

人话：导入区是在声明“这个文件需要哪些外部工具”。标准库通常提供基础能力，项目内导入则说明它依赖哪些业务模块。

## 顶层常量和类型

- 第 15 行：`Identifier` = `str | int`。人话：在模块级别准备一个后面会反复使用的值。
- 第 16 行：`HandLoopStatus` = `Literal['completed', 'paused', 'reset']`。人话：在模块级别准备一个后面会反复使用的值。
- 第 17-28 行：`_HIDDEN_DTO_KEYS` = `{'adapter_hand_ref', 'deck', 'deck_order', 'hidden_hole_cards', 'hole_cards', 'private_cards', 'private_hole_cards', 'remaining_deck', 'stub', 'undealt_cards'}`。人话：在模块级别准备一个后面会反复使用的值。
- 第 29 行：`_HIDDEN_DTO_KEY_FRAGMENTS` = `('deck', 'hole_cards', 'pocket_cards', 'private_cards', 'undealt')`。人话：在模块级别准备一个后面会反复使用的值。
- 第 1106-1121 行：`__all__` = `['ActionRequestContext', 'ActionValidatorProtocol', 'CurrentActor', 'GameLoop', 'HandEventLogProtocol', 'HandLoopResult', 'ObservationSystemProtocol', 'PlayerControllerProtocol', 'PlayerControllerRegistryProtocol', 'PokerAdapterProtocol', 'TableManagerProtocol', 'ValidatedAction', 'ValidationResult', 'WebSocketGatewayProtocol']`。人话：在模块级别准备一个后面会反复使用的值。

## 类 `CurrentActor`（第 33-47 行）

装饰器：`@dataclass(frozen=True, slots=True)`。

源码说明：Platform actor for the current decision point.

人话：把一组相关数据和行为封装到一个类型里，供其他模块按统一接口使用。

字段/类变量：

- `hand_id`：类型 `Identifier`。
- `turn_id`：类型 `Identifier`。
- `seat_index`：类型 `int`。
- `player_id`：类型 `Identifier`。

这个类里的方法：

### `to_dict`（第 41-47 行）

签名：

```python
def to_dict(self) -> dict[str, object]
```

人话：把对象转成普通字典，方便 API、日志、测试或 JSON 序列化使用。

关键代码块：

- 第 42-47 行：返回计算结果，把这个函数的最终答案交给调用者。

## 类 `ActionRequestContext`（第 51-67 行）

装饰器：`@dataclass(frozen=True, slots=True)`。

源码说明：Context created by the loop for a single action request.

人话：把一组相关数据和行为封装到一个类型里，供其他模块按统一接口使用。

字段/类变量：

- `table_id`：类型 `Identifier`。
- `hand_id`：类型 `Identifier`。
- `turn_id`：类型 `Identifier`。
- `player_id`：类型 `Identifier`。
- `seat_index`：类型 `int`。

这个类里的方法：

### `to_dict`（第 60-67 行）

签名：

```python
def to_dict(self) -> dict[str, object]
```

人话：把对象转成普通字典，方便 API、日志、测试或 JSON 序列化使用。

关键代码块：

- 第 61-67 行：返回计算结果，把这个函数的最终答案交给调用者。

## 类 `ValidatedAction`（第 71-113 行）

装饰器：`@dataclass(frozen=True, slots=True)`。

源码说明：Validator output with adapter-friendly delegated action fields.

人话：校验输入或状态是否合法，发现问题时返回错误或抛出异常。

字段/类变量：

- `action`：类型 `Any`。
- `normalized_type`：类型 `str | None`，默认值 `None`。
- `normalized_amount`：类型 `int | None`，默认值 `None`。
- `validation_source`：类型 `str`，默认值 `'platform'`。

这个类里的方法：

### `player_id`（第 80-81 行）

签名：

```python
def player_id(self) -> Any
```

装饰器：`@property`。

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 81 行：返回计算结果，把这个函数的最终答案交给调用者。

### `seat_index`（第 84-85 行）

签名：

```python
def seat_index(self) -> Any
```

装饰器：`@property`。

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 85 行：返回计算结果，把这个函数的最终答案交给调用者。

### `hand_id`（第 88-89 行）

签名：

```python
def hand_id(self) -> Any
```

装饰器：`@property`。

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 89 行：返回计算结果，把这个函数的最终答案交给调用者。

### `turn_id`（第 92-93 行）

签名：

```python
def turn_id(self) -> Any
```

装饰器：`@property`。

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 93 行：返回计算结果，把这个函数的最终答案交给调用者。

### `action_type`（第 96-97 行）

签名：

```python
def action_type(self) -> Any
```

装饰器：`@property`。

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 97 行：返回计算结果，把这个函数的最终答案交给调用者。

### `amount`（第 100-101 行）

签名：

```python
def amount(self) -> Any
```

装饰器：`@property`。

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 101 行：返回计算结果，把这个函数的最终答案交给调用者。

### `source`（第 104-105 行）

签名：

```python
def source(self) -> Any
```

装饰器：`@property`。

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 105 行：返回计算结果，把这个函数的最终答案交给调用者。

### `to_dict`（第 107-113 行）

签名：

```python
def to_dict(self) -> dict[str, object]
```

人话：把对象转成普通字典，方便 API、日志、测试或 JSON 序列化使用。

关键代码块：

- 第 108-113 行：返回计算结果，把这个函数的最终答案交给调用者。

## 类 `ValidationResult`（第 117-130 行）

装饰器：`@dataclass(frozen=True, slots=True)`。

源码说明：Explicit success/failure envelope accepted from validators.

人话：把一组相关数据和行为封装到一个类型里，供其他模块按统一接口使用。

字段/类变量：

- `ok`：类型 `bool`。
- `validated_action`：类型 `Any | None`，默认值 `None`。
- `error`：类型 `ActionError | None`，默认值 `None`。

这个类里的方法：

### `accepted`（第 125-126 行）

签名：

```python
def accepted(cls, validated_action: Any) -> ValidationResult
```

装饰器：`@classmethod`。

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 126 行：返回计算结果，把这个函数的最终答案交给调用者。

### `rejected`（第 129-130 行）

签名：

```python
def rejected(cls, error: ActionError) -> ValidationResult
```

装饰器：`@classmethod`。

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 130 行：返回计算结果，把这个函数的最终答案交给调用者。

## 类 `HandLoopResult`（第 134-141 行）

装饰器：`@dataclass(frozen=True, slots=True)`。

源码说明：Outcome of driving one hand to a safe boundary.

人话：把一组相关数据和行为封装到一个类型里，供其他模块按统一接口使用。

字段/类变量：

- `hand_id`：类型 `Identifier`。
- `status`：类型 `HandLoopStatus`。
- `settlement`：类型 `Any | None`，默认值 `None`。
- `next_hand_context`：类型 `Any | None`，默认值 `None`。
- `reason`：类型 `str | None`，默认值 `None`。

## 类 `PokerAdapterProtocol`（第 144-155 行）

继承：`Protocol`。

源码说明：Adapter surface consumed by the game loop.

人话：把一组相关数据和行为封装到一个类型里，供其他模块按统一接口使用。

这个类里的方法：

### `hand_is_active`（第 147 行）

签名：

```python
def hand_is_active(self, hand_id: Identifier) -> bool
```

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 147 行：执行一个表达式，通常是调用函数或触发某个对象行为。

### `get_current_actor`（第 149 行）

签名：

```python
def get_current_actor(self, hand_id: Identifier) -> Any | None
```

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 149 行：执行一个表达式，通常是调用函数或触发某个对象行为。

### `advance_non_player_state`（第 151 行）

签名：

```python
def advance_non_player_state(self, hand_id: Identifier) -> Any
```

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 151 行：执行一个表达式，通常是调用函数或触发某个对象行为。

### `submit_action`（第 153 行）

签名：

```python
def submit_action(self, validated_action: Any) -> Any
```

人话：提交动作或请求，把外部输入交给下一层处理。

关键代码块：

- 第 153 行：执行一个表达式，通常是调用函数或触发某个对象行为。

### `get_hand_settlement`（第 155 行）

签名：

```python
def get_hand_settlement(self, hand_id: Identifier) -> Any
```

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 155 行：执行一个表达式，通常是调用函数或触发某个对象行为。

## 类 `ObservationSystemProtocol`（第 158-161 行）

继承：`Protocol`。

源码说明：Builds player-scoped observations from platform state.

人话：把一组相关数据和行为封装到一个类型里，供其他模块按统一接口使用。

这个类里的方法：

### `build`（第 161 行）

签名：

```python
def build(self, actor: CurrentActor, context: ActionRequestContext) -> Any
```

人话：根据已有状态组装更高层的数据对象。

关键代码块：

- 第 161 行：执行一个表达式，通常是调用函数或触发某个对象行为。

## 类 `PlayerControllerProtocol`（第 164-169 行）

继承：`Protocol`。

源码说明：Controller surface used for both human and bot players.

人话：把一组相关数据和行为封装到一个类型里，供其他模块按统一接口使用。

这个类里的方法：

### `request_action`（第 167 行）

签名：

```python
def request_action(self, observation: Any, context: ActionRequestContext) -> Any
```

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 167 行：执行一个表达式，通常是调用函数或触发某个对象行为。

### `notify_action_rejected`（第 169 行）

签名：

```python
def notify_action_rejected(self, action_error: ActionError) -> Any
```

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 169 行：执行一个表达式，通常是调用函数或触发某个对象行为。

## 类 `PlayerControllerRegistryProtocol`（第 172-175 行）

继承：`Protocol`。

源码说明：Finds the controller assigned to a platform player.

人话：把一组相关数据和行为封装到一个类型里，供其他模块按统一接口使用。

这个类里的方法：

### `get_controller`（第 175 行）

签名：

```python
def get_controller(self, player_id: Identifier) -> PlayerControllerProtocol
```

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 175 行：执行一个表达式，通常是调用函数或触发某个对象行为。

## 类 `ActionValidatorProtocol`（第 178-181 行）

继承：`Protocol`。

源码说明：Platform action validator boundary.

人话：把一组相关数据和行为封装到一个类型里，供其他模块按统一接口使用。

这个类里的方法：

### `validate`（第 181 行）

签名：

```python
def validate(self, action: Any, context: ActionRequestContext) -> Any
```

人话：校验输入或状态是否合法，发现问题时返回错误或抛出异常。

关键代码块：

- 第 181 行：执行一个表达式，通常是调用函数或触发某个对象行为。

## 类 `TableManagerProtocol`（第 184-191 行）

继承：`Protocol`。

源码说明：Table lifecycle surface consumed at safe boundaries.

人话：把一组相关数据和行为封装到一个类型里，供其他模块按统一接口使用。

这个类里的方法：

### `get_table_snapshot`（第 187 行）

签名：

```python
def get_table_snapshot(self, table_id: Identifier) -> Any
```

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 187 行：执行一个表达式，通常是调用函数或触发某个对象行为。

### `apply_hand_settlement`（第 189 行）

签名：

```python
def apply_hand_settlement(self, settlement: Any) -> Any
```

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 189 行：执行一个表达式，通常是调用函数或触发某个对象行为。

### `create_next_hand`（第 191 行）

签名：

```python
def create_next_hand(self, table_id: Identifier) -> Any
```

人话：创建并返回一个新对象，通常会把多个输入整理到统一格式。

关键代码块：

- 第 191 行：执行一个表达式，通常是调用函数或触发某个对象行为。

## 类 `HandEventLogProtocol`（第 194-225 行）

继承：`Protocol`。

源码说明：Temporary hand event log boundary.

人话：把一组相关数据和行为封装到一个类型里，供其他模块按统一接口使用。

这个类里的方法：

### `record_hand_started`（第 197-199 行）

签名：

```python
def record_hand_started(self, hand_id: str, payload: Mapping[str, object] | None = None) -> Any
```

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 199 行：执行一个表达式，通常是调用函数或触发某个对象行为。

### `record_action_succeeded`（第 201-210 行）

签名：

```python
def record_action_succeeded(self, hand_id: str, player_id: str, action: str, *, amount: int | float | None = None, seat_index: int | None = None, payload: Mapping[str, object] | None = None) -> Any
```

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 210 行：执行一个表达式，通常是调用函数或触发某个对象行为。

### `record_action_rejected`（第 212-221 行）

签名：

```python
def record_action_rejected(self, hand_id: str, player_id: str, reason: str, *, attempted_action: str | None = None, seat_index: int | None = None, payload: Mapping[str, object] | None = None) -> Any
```

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 221 行：执行一个表达式，通常是调用函数或触发某个对象行为。

### `record_hand_ended`（第 223-225 行）

签名：

```python
def record_hand_ended(self, hand_id: str, payload: Mapping[str, object] | None = None) -> Any
```

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 225 行：执行一个表达式，通常是调用函数或触发某个对象行为。

## 类 `WebSocketGatewayProtocol`（第 228-241 行）

继承：`Protocol`。

源码说明：Gateway event boundary used by the loop.

人话：把一组相关数据和行为封装到一个类型里，供其他模块按统一接口使用。

这个类里的方法：

### `broadcast_event`（第 231-233 行）

签名：

```python
def broadcast_event(self, event_type: str, payload: Any, *, table_id: str | None = None) -> Any
```

人话：向客户端、连接或订阅者发送消息。

关键代码块：

- 第 233 行：执行一个表达式，通常是调用函数或触发某个对象行为。

### `send_action_requested`（第 235-241 行）

签名：

```python
def send_action_requested(self, player_id: str, seat_index: int, payload: Any, table_id: str | None = None) -> Any
```

人话：向客户端、连接或订阅者发送消息。

关键代码块：

- 第 241 行：执行一个表达式，通常是调用函数或触发某个对象行为。

## 类 `_ControlDecision`（第 245-247 行）

装饰器：`@dataclass(frozen=True, slots=True)`。

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

字段/类变量：

- `status`：类型 `Literal['running', 'paused', 'reset']`。
- `reason`：类型 `str | None`，默认值 `None`。

## 类 `GameLoop`（第 250-842 行）

源码说明：Drive one poker hand from start to settlement using injected services.

人话：把一组相关数据和行为封装到一个类型里，供其他模块按统一接口使用。

这个类里的方法：

### `__init__`（第 253-272 行）

签名：

```python
def __init__(self, *, table_manager: TableManagerProtocol, adapter: PokerAdapterProtocol, observation_system: ObservationSystemProtocol, controller_registry: PlayerControllerRegistryProtocol, action_validator: ActionValidatorProtocol, hand_event_log: HandEventLogProtocol, websocket_gateway: WebSocketGatewayProtocol | None = None, turn_id_factory: Any | None = None) -> None
```

人话：初始化对象，接收外部传入的数据并准备对象内部状态。

关键代码块：

- 第 265 行：给 `self.table_manager` 赋值，准备后面逻辑要用的数据。
- 第 266 行：给 `self.adapter` 赋值，准备后面逻辑要用的数据。
- 第 267 行：给 `self.observation_system` 赋值，准备后面逻辑要用的数据。
- 第 268 行：给 `self.controller_registry` 赋值，准备后面逻辑要用的数据。
- 第 269 行：给 `self.action_validator` 赋值，准备后面逻辑要用的数据。
- 第 270 行：给 `self.hand_event_log` 赋值，准备后面逻辑要用的数据。
- 第 271 行：给 `self.websocket_gateway` 赋值，准备后面逻辑要用的数据。
- 第 272 行：给 `self._turn_id_factory` 赋值，准备后面逻辑要用的数据。

### `start_hand`（第 274-367 行）

签名：

```python
async def start_hand(self, hand_context: Any) -> HandLoopResult
```

源码说明：Drive a single hand until settlement, pause, or reset.

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 277 行：给 `hand_id` 赋值，准备后面逻辑要用的数据。
- 第 278 行：给 `table_id` 赋值，准备后面逻辑要用的数据。
- 第 280 行：等待一个异步操作完成，常见于 WebSocket、控制器或异步队列。
- 第 281 行：等待一个异步操作完成，常见于 WebSocket、控制器或异步队列。
- 第 283-349 行：只要 `await self._hand_is_active(hand_id)` 还成立，就持续执行循环。
- 第 351 行：给 `settlement` 赋值，准备后面逻辑要用的数据。
- 第 352 行：等待一个异步操作完成，常见于 WebSocket、控制器或异步队列。
- 第 353 行：等待一个异步操作完成，常见于 WebSocket、控制器或异步队列。
- 第 354 行：等待一个异步操作完成，常见于 WebSocket、控制器或异步队列。
- 第 355 行：等待一个异步操作完成，常见于 WebSocket、控制器或异步队列。
- 第 357 行：给 `next_hand_context` 赋值，准备后面逻辑要用的数据。
- 第 358 行：给 `control` 赋值，准备后面逻辑要用的数据。
- 第 359-360 行：根据条件 `control.status == 'running'` 分支处理不同情况。
- 第 362-367 行：返回计算结果，把这个函数的最终答案交给调用者。

### `_new_turn_id`（第 369-370 行）

签名：

```python
def _new_turn_id(self) -> Identifier
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 370 行：返回计算结果，把这个函数的最终答案交给调用者。

### `_hand_is_active`（第 372-392 行）

签名：

```python
async def _hand_is_active(self, hand_id: Identifier) -> bool
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 373-381 行：根据条件 `_has_callable(self.adapter, 'hand_is_active')` 分支处理不同情况。
- 第 382-390 行：根据条件 `_has_callable(self.adapter, 'is_hand_active')` 分支处理不同情况。
- 第 391 行：给 `summary` 赋值，准备后面逻辑要用的数据。
- 第 392 行：返回计算结果，把这个函数的最终答案交给调用者。

### `_get_current_actor`（第 394-410 行）

签名：

```python
async def _get_current_actor(self, hand_id: Identifier) -> Any | None
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 395-401 行：根据条件 `_has_callable(self.adapter, 'get_current_actor')` 分支处理不同情况。
- 第 402-408 行：根据条件 `_has_callable(self.adapter, 'current_actor')` 分支处理不同情况。
- 第 409 行：给 `summary` 赋值，准备后面逻辑要用的数据。
- 第 410 行：返回计算结果，把这个函数的最终答案交给调用者。

### `_advance_non_player_state`（第 412-429 行）

签名：

```python
async def _advance_non_player_state(self, hand_id: Identifier) -> None
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 413-420 行：根据条件 `_has_callable(self.adapter, 'advance_non_player_state')` 分支处理不同情况。
- 第 421-428 行：根据条件 `_has_callable(self.adapter, 'advance')` 分支处理不同情况。
- 第 429 行：等待一个异步操作完成，常见于 WebSocket、控制器或异步队列。

### `_state_summary`（第 431-437 行）

签名：

```python
async def _state_summary(self, hand_id: Identifier) -> Any
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 432-437 行：返回计算结果，把这个函数的最终答案交给调用者。

### `_build_observation`（第 439-459 行）

签名：

```python
async def _build_observation(self, actor: CurrentActor, context: ActionRequestContext, hand_context: Any) -> Any
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 445-453 行：给 `payload` 赋值，准备后面逻辑要用的数据。
- 第 454-459 行：返回计算结果，把这个函数的最终答案交给调用者。

### `_controller_for`（第 461-472 行）

签名：

```python
async def _controller_for(self, actor: CurrentActor) -> PlayerControllerProtocol
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 462-471 行：给 `controller` 赋值，准备后面逻辑要用的数据。
- 第 472 行：返回计算结果，把这个函数的最终答案交给调用者。

### `_validate_action`（第 474-489 行）

签名：

```python
async def _validate_action(self, action: Any, context: ActionRequestContext) -> ValidationResult
```

人话：校验输入或状态是否合法，发现问题时返回错误或抛出异常。

关键代码块：

- 第 479-487 行：尝试执行可能失败的操作，并在异常发生时转成项目自己的处理方式。
- 第 489 行：返回计算结果，把这个函数的最终答案交给调用者。

### `_submit_action`（第 491-497 行）

签名：

```python
async def _submit_action(self, validated_action: Any) -> Any
```

人话：提交动作或请求，把外部输入交给下一层处理。

关键代码块：

- 第 492-497 行：返回计算结果，把这个函数的最终答案交给调用者。

### `_get_settlement`（第 499-505 行）

签名：

```python
async def _get_settlement(self, hand_id: Identifier) -> Any
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 500-505 行：返回计算结果，把这个函数的最终答案交给调用者。

### `_apply_settlement`（第 507-518 行）

签名：

```python
async def _apply_settlement(self, settlement: Any, table_id: Identifier, hand_id: Identifier) -> None
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 513-518 行：等待一个异步操作完成，常见于 WebSocket、控制器或异步队列。

### `_create_next_hand`（第 520-528 行）

签名：

```python
async def _create_next_hand(self, table_id: Identifier) -> Any
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 521-522 行：根据条件 `not _has_callable(self.table_manager, 'create_next_hand')` 分支处理不同情况。
- 第 523-528 行：返回计算结果，把这个函数的最终答案交给调用者。

### `_control_decision`（第 530-584 行）

签名：

```python
async def _control_decision(self, table_id: Identifier) -> _ControlDecision
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 531 行：声明字段或变量 `status`，类型是 `Any`。
- 第 533-541 行：根据条件 `_has_callable(self.table_manager, 'is_table_resetting')` 分支处理不同情况。
- 第 543-551 行：根据条件 `_has_callable(self.table_manager, 'is_table_paused')` 分支处理不同情况。
- 第 553-577 行：根据条件 `_has_callable(self.table_manager, 'get_table_status')` 分支处理不同情况。
- 第 579 行：给 `normalized` 赋值，准备后面逻辑要用的数据。
- 第 580-581 行：根据条件 `normalized in {'reset', 'resetting'}` 分支处理不同情况。
- 第 582-583 行：根据条件 `normalized in {'paused', 'pausing'}` 分支处理不同情况。
- 第 584 行：返回计算结果，把这个函数的最终答案交给调用者。

### `_record_hand_started`（第 586-593 行）

签名：

```python
async def _record_hand_started(self, hand_id: Identifier, hand_context: Any) -> None
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 587 行：给 `payload` 赋值，准备后面逻辑要用的数据。
- 第 588-593 行：等待一个异步操作完成，常见于 WebSocket、控制器或异步队列。

### `_record_actor_requested`（第 595-617 行）

签名：

```python
async def _record_actor_requested(self, actor: CurrentActor, observation: Any, context: ActionRequestContext) -> None
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 601-605 行：给 `payload` 赋值，准备后面逻辑要用的数据。
- 第 606-617 行：等待一个异步操作完成，常见于 WebSocket、控制器或异步队列。

### `_notify_and_record_rejection`（第 619-651 行）

签名：

```python
async def _notify_and_record_rejection(self, controller: Any, actor: CurrentActor, error: ActionError, action: Any) -> None
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 626-632 行：根据条件 `_has_callable(controller, 'notify_action_rejected')` 分支处理不同情况。
- 第 634-637 行：给 `payload` 赋值，准备后面逻辑要用的数据。
- 第 638-650 行：等待一个异步操作完成，常见于 WebSocket、控制器或异步队列。
- 第 651 行：等待一个异步操作完成，常见于 WebSocket、控制器或异步队列。

### `_record_action_succeeded`（第 653-676 行）

签名：

```python
async def _record_action_succeeded(self, actor: CurrentActor, action: Any, submission: Any) -> None
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 659-663 行：给 `payload` 赋值，准备后面逻辑要用的数据。
- 第 664-676 行：等待一个异步操作完成，常见于 WebSocket、控制器或异步队列。

### `_record_settlement`（第 678-684 行）

签名：

```python
async def _record_settlement(self, hand_id: Identifier, settlement: Any) -> None
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 679-684 行：等待一个异步操作完成，常见于 WebSocket、控制器或异步队列。

### `_record_hand_ended`（第 686-695 行）

签名：

```python
async def _record_hand_ended(self, hand_id: Identifier, settlement: Any) -> None
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 687-695 行：等待一个异步操作完成，常见于 WebSocket、控制器或异步队列。

### `_broadcast_hand_started`（第 697-709 行）

签名：

```python
async def _broadcast_hand_started(self, table_id: Identifier, hand_id: Identifier, hand_context: Any) -> None
```

人话：向客户端、连接或订阅者发送消息。

关键代码块：

- 第 703 行：给 `payload` 赋值，准备后面逻辑要用的数据。
- 第 704-709 行：等待一个异步操作完成，常见于 WebSocket、控制器或异步队列。

### `_send_action_requested`（第 711-747 行）

签名：

```python
async def _send_action_requested(self, table_id: Identifier, actor: CurrentActor, observation: Any, context: ActionRequestContext) -> None
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 718-719 行：根据条件 `self.websocket_gateway is None` 分支处理不同情况。
- 第 720-728 行：给 `payload` 赋值，准备后面逻辑要用的数据。
- 第 729-741 行：根据条件 `_has_callable(self.websocket_gateway, 'send_action_requested')` 分支处理不同情况。
- 第 742-747 行：等待一个异步操作完成，常见于 WebSocket、控制器或异步队列。

### `_send_action_rejected`（第 749-771 行）

签名：

```python
async def _send_action_rejected(self, actor: CurrentActor, error: ActionError, action: Any) -> None
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 755-756 行：根据条件 `self.websocket_gateway is None` 分支处理不同情况。
- 第 757-761 行：给 `payload` 赋值，准备后面逻辑要用的数据。
- 第 762-771 行：等待一个异步操作完成，常见于 WebSocket、控制器或异步队列。

### `_broadcast_state_update`（第 773-803 行）

签名：

```python
async def _broadcast_state_update(self, table_id: Identifier, actor: CurrentActor, action: Any, submission: Any) -> None
```

人话：向客户端、连接或订阅者发送消息。

关键代码块：

- 第 780-787 行：给 `payload` 赋值，准备后面逻辑要用的数据。
- 第 788-789 行：根据条件 `self.websocket_gateway is None` 分支处理不同情况。
- 第 790-797 行：根据条件 `_has_callable(self.websocket_gateway, 'broadcast_state_update')` 分支处理不同情况。
- 第 798-803 行：等待一个异步操作完成，常见于 WebSocket、控制器或异步队列。

### `_broadcast_hand_ended`（第 805-812 行）

签名：

```python
async def _broadcast_hand_ended(self, table_id: Identifier, hand_id: Identifier, settlement: Any) -> None
```

人话：向客户端、连接或订阅者发送消息。

关键代码块：

- 第 811 行：给 `payload` 赋值，准备后面逻辑要用的数据。
- 第 812 行：等待一个异步操作完成，常见于 WebSocket、控制器或异步队列。

### `_broadcast`（第 814-842 行）

签名：

```python
async def _broadcast(self, method_names: tuple[str, ...], event_type: str, payload: Any, *, table_id: Identifier) -> None
```

人话：向客户端、连接或订阅者发送消息。

关键代码块：

- 第 822-823 行：根据条件 `self.websocket_gateway is None` 分支处理不同情况。
- 第 824-831 行：根据条件 `any((_has_callable(self.websocket_gateway, method_name) for method_name in method_names))` 分支处理不同情况。
- 第 832-842 行：根据条件 `_has_callable(self.websocket_gateway, 'broadcast_event')` 分支处理不同情况。

## 模块级函数

### `_coerce_validation_result`（第 845-870 行）

签名：

```python
def _coerce_validation_result(raw_result: Any, action: Any, context: Any) -> ValidationResult
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 846-847 行：根据条件 `isinstance(raw_result, ValidationResult)` 分支处理不同情况。
- 第 848-849 行：根据条件 `isinstance(raw_result, ActionError)` 分支处理不同情况。
- 第 850-855 行：根据条件 `isinstance(raw_result, Mapping)` 分支处理不同情况。
- 第 856-860 行：根据条件 `isinstance(raw_result, tuple) and len(raw_result) == 2` 分支处理不同情况。
- 第 862 行：给 `ok` 赋值，准备后面逻辑要用的数据。
- 第 863-864 行：根据条件 `ok is False` 分支处理不同情况。
- 第 865 行：给 `validated` 赋值，准备后面逻辑要用的数据。
- 第 866-867 行：根据条件 `validated is not None and raw_result is not None` 分支处理不同情况。
- 第 868-869 行：根据条件 `raw_result is None` 分支处理不同情况。
- 第 870 行：返回计算结果，把这个函数的最终答案交给调用者。

### `_submission_error`（第 873-883 行）

签名：

```python
def _submission_error(submission: Any, actor: CurrentActor) -> ActionError | None
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 874-877 行：根据条件 `isinstance(submission, Mapping)` 分支处理不同情况。
- 第 878-879 行：根据条件 `_field(submission, 'ok') is False` 分支处理不同情况。
- 第 880 行：给 `error` 赋值，准备后面逻辑要用的数据。
- 第 881-882 行：根据条件 `error is not None` 分支处理不同情况。
- 第 883 行：返回计算结果，把这个函数的最终答案交给调用者。

### `_control_error`（第 886-889 行）

签名：

```python
def _control_error(control: _ControlDecision, actor: CurrentActor) -> ActionError
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 887-888 行：根据条件 `control.status == 'reset'` 分支处理不同情况。
- 第 889 行：返回计算结果，把这个函数的最终答案交给调用者。

### `_error_from_exception`（第 892-893 行）

签名：

```python
def _error_from_exception(exc: Exception, context: Any) -> ActionError
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 893 行：返回计算结果，把这个函数的最终答案交给调用者。

### `_error_from_raw`（第 896-916 行）

签名：

```python
def _error_from_raw(raw_error: Any, context: Any) -> ActionError
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 897-898 行：根据条件 `isinstance(raw_error, ActionError)` 分支处理不同情况。
- 第 899-907 行：根据条件 `isinstance(raw_error, Mapping)` 分支处理不同情况。
- 第 909-916 行：返回计算结果，把这个函数的最终答案交给调用者。

### `_action_error`（第 919-927 行）

签名：

```python
def _action_error(code: str, message: str, context: Any) -> ActionError
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 920-927 行：返回计算结果，把这个函数的最终答案交给调用者。

### `_call_optional`（第 930-938 行）

签名：

```python
async def _call_optional(service: Any, method_names: tuple[str, ...], payload: Mapping[str, Any], positional_order: tuple[str, ...] = ()) -> Any
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 936-937 行：根据条件 `not any((_has_callable(service, method_name) for method_name in method_names))` 分支处理不同情况。
- 第 938 行：返回计算结果，把这个函数的最终答案交给调用者。

### `_call_service_method`（第 941-958 行）

签名：

```python
async def _call_service_method(service: Any, method_names: tuple[str, ...], payload: Mapping[str, Any], positional_order: tuple[str, ...] = ()) -> Any
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 947 行：给 `target` 赋值，准备后面逻辑要用的数据。
- 第 948-952 行：循环遍历 `method_names`，逐个处理里面的元素。
- 第 953-955 行：根据条件 `target is None` 分支处理不同情况。
- 第 957 行：给 `result` 赋值，准备后面逻辑要用的数据。
- 第 958 行：返回计算结果，把这个函数的最终答案交给调用者。

### `_call_with_supported_arguments`（第 961-1001 行）

签名：

```python
def _call_with_supported_arguments(target: Any, payload: Mapping[str, Any], positional_order: tuple[str, ...]) -> Any
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 966-970 行：尝试执行可能失败的操作，并在异常发生时转成项目自己的处理方式。
- 第 972 行：给 `parameters` 赋值，准备后面逻辑要用的数据。
- 第 973-974 行：根据条件 `any((parameter.kind == inspect.Parameter.VAR_KEYWORD for parameter in parameters))` 分支处理不同情况。
- 第 976-981 行：给 `supported_keyword_names` 赋值，准备后面逻辑要用的数据。
- 第 982-984 行：给 `supported_payload` 赋值，准备后面逻辑要用的数据。
- 第 985-986 行：根据条件 `supported_payload and set(supported_payload) == set(payload)` 分支处理不同情况。
- 第 988-993 行：给 `positional_parameters` 赋值，准备后面逻辑要用的数据。
- 第 994-996 行：根据条件 `len(positional_parameters) == 1 and len(supported_payload) == 1` 分支处理不同情况。
- 第 997-998 行：根据条件 `supported_payload and (not positional_parameters)` 分支处理不同情况。
- 第 1000 行：给 `ordered_args` 赋值，准备后面逻辑要用的数据。
- 第 1001 行：返回计算结果，把这个函数的最终答案交给调用者。

### `_maybe_await`（第 1004-1007 行）

签名：

```python
async def _maybe_await(result: Any) -> Any
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 1005-1006 行：根据条件 `inspect.isawaitable(result)` 分支处理不同情况。
- 第 1007 行：返回计算结果，把这个函数的最终答案交给调用者。

### `_field`（第 1010-1015 行）

签名：

```python
def _field(value: Any, name: str, default: Any = None) -> Any
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 1011-1012 行：根据条件 `value is None` 分支处理不同情况。
- 第 1013-1014 行：根据条件 `isinstance(value, Mapping)` 分支处理不同情况。
- 第 1015 行：返回计算结果，把这个函数的最终答案交给调用者。

### `_field_or_mapping`（第 1018-1019 行）

签名：

```python
def _field_or_mapping(value: Mapping[str, Any], name: str, default: Any = None) -> Any
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 1019 行：返回计算结果，把这个函数的最终答案交给调用者。

### `_required_identifier`（第 1022-1023 行）

签名：

```python
def _required_identifier(value: Any, name: str) -> Identifier
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 1023 行：返回计算结果，把这个函数的最终答案交给调用者。

### `_identifier_or_default`（第 1026-1028 行）

签名：

```python
def _identifier_or_default(value: Any, name: str, default: Identifier) -> Identifier
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 1027 行：给 `raw_value` 赋值，准备后面逻辑要用的数据。
- 第 1028 行：返回计算结果，把这个函数的最终答案交给调用者。

### `_normalize_identifier`（第 1031-1038 行）

签名：

```python
def _normalize_identifier(value: Any, name: str) -> Identifier
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 1032-1033 行：根据条件 `isinstance(value, bool) or value is None` 分支处理不同情况。
- 第 1034-1035 行：根据条件 `isinstance(value, int)` 分支处理不同情况。
- 第 1036-1037 行：根据条件 `isinstance(value, str) and value` 分支处理不同情况。
- 第 1038 行：主动抛出错误，表示传入数据或当前状态不符合要求。

### `_required_int`（第 1041-1045 行）

签名：

```python
def _required_int(value: Any, name: str) -> int
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 1042 行：给 `raw_value` 赋值，准备后面逻辑要用的数据。
- 第 1043-1044 行：根据条件 `isinstance(raw_value, bool) or not isinstance(raw_value, int)` 分支处理不同情况。
- 第 1045 行：返回计算结果，把这个函数的最终答案交给调用者。

### `_status_value`（第 1048-1053 行）

签名：

```python
def _status_value(status: Any) -> str
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 1049-1050 行：根据条件 `isinstance(status, Enum)` 分支处理不同情况。
- 第 1051-1052 行：根据条件 `status is None` 分支处理不同情况。
- 第 1053 行：返回计算结果，把这个函数的最终答案交给调用者。

### `_action_type_value`（第 1056-1060 行）

签名：

```python
def _action_type_value(action: Any) -> str
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 1057 行：给 `action_type` 赋值，准备后面逻辑要用的数据。
- 第 1058-1059 行：根据条件 `isinstance(action_type, Enum)` 分支处理不同情况。
- 第 1060 行：返回计算结果，把这个函数的最终答案交给调用者。

### `_has_callable`（第 1063-1064 行）

签名：

```python
def _has_callable(service: Any, method_name: str) -> bool
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 1064 行：返回计算结果，把这个函数的最终答案交给调用者。

### `_to_public_dto`（第 1067-1103 行）

签名：

```python
def _to_public_dto(value: Any) -> Any
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 1068-1069 行：根据条件 `value is None or isinstance(value, str | int | float | bool)` 分支处理不同情况。
- 第 1070-1071 行：根据条件 `isinstance(value, Enum)` 分支处理不同情况。
- 第 1073 行：给 `value_type` 赋值，准备后面逻辑要用的数据。
- 第 1074 行：给 `module_name` 赋值，准备后面逻辑要用的数据。
- 第 1075-1076 行：根据条件 `'pokerkit' in module_name` 分支处理不同情况。
- 第 1078-1090 行：根据条件 `isinstance(value, Mapping)` 分支处理不同情况。
- 第 1092-1093 行：根据条件 `isinstance(value, Sequence) and (not isinstance(value, str | bytes | bytearray))` 分支处理不同情况。
- 第 1095-1096 行：根据条件 `hasattr(value, 'to_dict') and callable(value.to_dict)` 分支处理不同情况。
- 第 1097-1098 行：根据条件 `hasattr(value, 'model_dump') and callable(value.model_dump)` 分支处理不同情况。
- 第 1099-1100 行：根据条件 `is_dataclass(value)` 分支处理不同情况。
- 第 1101-1102 行：根据条件 `hasattr(value, '__dict__')` 分支处理不同情况。
- 第 1103 行：返回计算结果，把这个函数的最终答案交给调用者。

## 对外公开接口

`__all__` 声明这个模块希望别人主要使用这些名字：

- `ActionRequestContext`
- `ActionValidatorProtocol`
- `CurrentActor`
- `GameLoop`
- `HandEventLogProtocol`
- `HandLoopResult`
- `ObservationSystemProtocol`
- `PlayerControllerProtocol`
- `PlayerControllerRegistryProtocol`
- `PokerAdapterProtocol`
- `TableManagerProtocol`
- `ValidatedAction`
- `ValidationResult`
- `WebSocketGatewayProtocol`

## 初学者阅读建议

先看“这个文件是干什么的”，再看类和函数标题。遇到以下划线开头的函数，可以先理解成内部工具；遇到 `to_dict/from_dict/to_json/from_json`，重点记住它们是在对象、字典和 JSON 之间转换。
