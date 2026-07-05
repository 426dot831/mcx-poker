# `mcx_poker/players/controllers.py` 人话讲解

源文件：`/Users/machengqi/Documents/mcx-poker/src/mcx_poker/players/controllers.py`

## 这个文件是干什么的

源码说明：Player controller boundary implementations.

Controllers consume platform observations and return platform-native
``PlayerAction`` objects. This module intentionally has no dependency on
PokerKit or table-manager internals.

人话概括：

负责玩家控制器，包括真人等待动作、机器人自动选择动作等。

## 导入区

- 第 8 行：从 `__future__` 导入 `annotations`。
- 第 10 行：导入 `asyncio`。
- 第 11 行：从 `collections.abc` 导入 `Iterable, Mapping, Sequence`。
- 第 12 行：从 `dataclasses` 导入 `dataclass, replace`。
- 第 13 行：从 `enum` 导入 `StrEnum`。
- 第 14 行：从 `typing` 导入 `Any, Protocol, runtime_checkable`。
- 第 16-24 行：从 `mcx_poker.engine.actions` 导入 `ActionError, ActionSource, ActionType, Identifier, LegalAction, LegalActionSet, PlayerAction`。

人话：导入区是在声明“这个文件需要哪些外部工具”。标准库通常提供基础能力，项目内导入则说明它依赖哪些业务模块。

## 顶层常量和类型

- 第 502 行：`DeterministicBotPlayerController` = `BotPlayerController`。人话：在模块级别准备一个后面会反复使用的值。
- 第 705-724 行：`__all__` = `['ActionRequestContext', 'ActionSubmissionRejected', 'BotPlayerController', 'BotStrategy', 'BotStrategyError', 'ControllerError', 'ControllerRegistration', 'ControllerRegistry', 'ControllerType', 'DeterministicBotPlayerController', 'FirstLegalActionStrategy', 'FutureAgentPlayerController', 'HumanPlayerController', 'NoLegalActionAvailable', 'PendingActionError', 'PendingHumanAction', 'PlayerController', 'PlayerObservation']`。人话：在模块级别准备一个后面会反复使用的值。

## 类 `ControllerType`（第 27-32 行）

继承：`StrEnum`。

源码说明：Controller source types known by the player-controller registry.

人话：把一组相关数据和行为封装到一个类型里，供其他模块按统一接口使用。

字段/类变量：

- `HUMAN`：类级变量，值 `'human'`。
- `BOT`：类级变量，值 `'bot'`。
- `FUTURE_AGENT`：类级变量，值 `'future_agent'`。

## 类 `ControllerError`（第 35-36 行）

继承：`ValueError`。

源码说明：Base error for controller boundary failures.

人话：把一组相关数据和行为封装到一个类型里，供其他模块按统一接口使用。

## 类 `NoLegalActionAvailable`（第 39-40 行）

继承：`ControllerError`。

源码说明：Raised when an observation exposes no enabled legal action.

人话：把一组相关数据和行为封装到一个类型里，供其他模块按统一接口使用。

## 类 `BotStrategyError`（第 43-44 行）

继承：`ControllerError`。

源码说明：Raised when a bot strategy returns an unusable decision.

人话：把一组相关数据和行为封装到一个类型里，供其他模块按统一接口使用。

## 类 `PendingActionError`（第 47-48 行）

继承：`ControllerError`。

源码说明：Raised when a human controller receives conflicting pending requests.

人话：把一组相关数据和行为封装到一个类型里，供其他模块按统一接口使用。

## 类 `ActionSubmissionRejected`（第 51-58 行）

继承：`ControllerError`。

源码说明：Raised when a submitted human action does not match the active turn.

人话：把一组相关数据和行为封装到一个类型里，供其他模块按统一接口使用。

字段/类变量：

- `action_error`：类型 `ActionError`。

这个类里的方法：

### `__init__`（第 56-58 行）

签名：

```python
def __init__(self, action_error: ActionError) -> None
```

人话：初始化对象，接收外部传入的数据并准备对象内部状态。

关键代码块：

- 第 57 行：给 `self.action_error` 赋值，准备后面逻辑要用的数据。
- 第 58 行：调用 `super().__init__`，执行一个有副作用或校验性质的动作。

## 类 `ActionRequestContext`（第 62-101 行）

装饰器：`@dataclass(frozen=True, slots=True)`。

源码说明：Metadata attached to one controller action request.

人话：把一组相关数据和行为封装到一个类型里，供其他模块按统一接口使用。

字段/类变量：

- `table_id`：类型 `Identifier`。
- `hand_id`：类型 `Identifier`。
- `turn_id`：类型 `Identifier`。
- `player_id`：类型 `Identifier`。
- `seat_index`：类型 `int`。

这个类里的方法：

### `__post_init__`（第 71-76 行）

签名：

```python
def __post_init__(self) -> None
```

人话：dataclass 创建对象后自动执行，用来做校验、标准化或补充字段。

关键代码块：

- 第 72 行：调用 `object.__setattr__`，执行一个有副作用或校验性质的动作。
- 第 73 行：调用 `object.__setattr__`，执行一个有副作用或校验性质的动作。
- 第 74 行：调用 `object.__setattr__`，执行一个有副作用或校验性质的动作。
- 第 75 行：调用 `object.__setattr__`，执行一个有副作用或校验性质的动作。
- 第 76 行：调用 `object.__setattr__`，执行一个有副作用或校验性质的动作。

### `to_dict`（第 78-85 行）

签名：

```python
def to_dict(self) -> dict[str, object]
```

人话：把对象转成普通字典，方便 API、日志、测试或 JSON 序列化使用。

关键代码块：

- 第 79-85 行：返回计算结果，把这个函数的最终答案交给调用者。

### `from_dict`（第 88-101 行）

签名：

```python
def from_dict(cls, data: Mapping[str, Any]) -> ActionRequestContext
```

装饰器：`@classmethod`。

人话：从普通字典恢复成项目里的强类型对象，同时复用构造时的校验逻辑。

关键代码块：

- 第 89 行：调用 `_require_mapping`，执行一个有副作用或校验性质的动作。
- 第 90-94 行：调用 `_require_keys`，执行一个有副作用或校验性质的动作。
- 第 95-101 行：返回计算结果，把这个函数的最终答案交给调用者。

## 类 `PlayerObservation`（第 105-136 行）

装饰器：`@runtime_checkable`。

继承：`Protocol`。

源码说明：Minimal observation shape consumed by controllers.

人话：把一组相关数据和行为封装到一个类型里，供其他模块按统一接口使用。

这个类里的方法：

### `observer_player_id`（第 109-111 行）

签名：

```python
def observer_player_id(self) -> Identifier
```

装饰器：`@property`。

源码说明：Player id of the observing actor.

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 111 行：执行一个表达式，通常是调用函数或触发某个对象行为。

### `observer_seat_index`（第 114-116 行）

签名：

```python
def observer_seat_index(self) -> int
```

装饰器：`@property`。

源码说明：Seat index of the observing actor.

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 116 行：执行一个表达式，通常是调用函数或触发某个对象行为。

### `table_id`（第 119-121 行）

签名：

```python
def table_id(self) -> Identifier
```

装饰器：`@property`。

源码说明：Current table id.

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 121 行：执行一个表达式，通常是调用函数或触发某个对象行为。

### `hand_id`（第 124-126 行）

签名：

```python
def hand_id(self) -> Identifier
```

装饰器：`@property`。

源码说明：Current hand id.

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 126 行：执行一个表达式，通常是调用函数或触发某个对象行为。

### `turn_id`（第 129-131 行）

签名：

```python
def turn_id(self) -> Identifier
```

装饰器：`@property`。

源码说明：Current turn id.

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 131 行：执行一个表达式，通常是调用函数或触发某个对象行为。

### `legal_actions`（第 134-136 行）

签名：

```python
def legal_actions(self) -> Iterable[LegalAction | Mapping[str, Any] | str]
```

装饰器：`@property`。

源码说明：Currently visible legal action descriptions.

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 136 行：执行一个表达式，通常是调用函数或触发某个对象行为。

## 类 `PlayerController`（第 140-161 行）

装饰器：`@runtime_checkable`。

继承：`Protocol`。

源码说明：Async controller boundary consumed by the game loop.

人话：把一组相关数据和行为封装到一个类型里，供其他模块按统一接口使用。

这个类里的方法：

### `request_action`（第 143-149 行）

签名：

```python
async def request_action(self, observation: PlayerObservation, action_request_context: ActionRequestContext | None = None) -> PlayerAction
```

源码说明：Return one platform action for the supplied observation.

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 149 行：执行一个表达式，通常是调用函数或触发某个对象行为。

### `notify_action_rejected`（第 151-153 行）

签名：

```python
async def notify_action_rejected(self, action_error: ActionError | object) -> None
```

源码说明：Receive an action rejection notification from the platform.

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 153 行：执行一个表达式，通常是调用函数或触发某个对象行为。

### `notify_hand_started`（第 155-157 行）

签名：

```python
async def notify_hand_started(self, hand_context: object) -> None
```

源码说明：Receive a hand-started notification.

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 157 行：执行一个表达式，通常是调用函数或触发某个对象行为。

### `notify_hand_ended`（第 159-161 行）

签名：

```python
async def notify_hand_ended(self, result_summary: object) -> None
```

源码说明：Receive a hand-ended notification.

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 161 行：执行一个表达式，通常是调用函数或触发某个对象行为。

## 类 `BotStrategy`（第 164-174 行）

继承：`Protocol`。

源码说明：Replaceable strategy hook for bot controllers.

人话：把一组相关数据和行为封装到一个类型里，供其他模块按统一接口使用。

这个类里的方法：

### `select_action`（第 167-174 行）

签名：

```python
def select_action(self, observation: PlayerObservation, context: ActionRequestContext, legal_actions: Sequence[LegalAction]) -> LegalAction | PlayerAction
```

源码说明：Select a legal action description or return a full action.

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 174 行：执行一个表达式，通常是调用函数或触发某个对象行为。

## 类 `PendingHumanAction`（第 178-185 行）

装饰器：`@dataclass(slots=True)`。

源码说明：The currently open human decision point.

人话：把一组相关数据和行为封装到一个类型里，供其他模块按统一接口使用。

字段/类变量：

- `observation`：类型 `PlayerObservation`。
- `context`：类型 `ActionRequestContext`。
- `future`：类型 `asyncio.Future[PlayerAction]`。
- `waiter_active`：类型 `bool`，默认值 `False`。
- `last_error`：类型 `ActionError | object | None`，默认值 `None`。

## 类 `ControllerRegistration`（第 189-195 行）

装饰器：`@dataclass(frozen=True, slots=True)`。

源码说明：Registry entry for one player controller.

人话：把一组相关数据和行为封装到一个类型里，供其他模块按统一接口使用。

字段/类变量：

- `player_id`：类型 `Identifier`。
- `controller`：类型 `PlayerController`。
- `seat_index`：类型 `int | None`，默认值 `None`。
- `controller_type`：类型 `ControllerType`，默认值 `ControllerType.HUMAN`。

## 类 `ControllerRegistry`（第 198-277 行）

源码说明：Lookup registry for controllers by player id or seat index.

人话：把一组相关数据和行为封装到一个类型里，供其他模块按统一接口使用。

这个类里的方法：

### `__init__`（第 201-203 行）

签名：

```python
def __init__(self) -> None
```

人话：初始化对象，接收外部传入的数据并准备对象内部状态。

关键代码块：

- 第 202 行：声明字段或变量 `self._by_player_id`，类型是 `dict[Identifier, ControllerRegistration]`。
- 第 203 行：声明字段或变量 `self._by_seat_index`，类型是 `dict[int, Identifier]`。

### `register`（第 205-231 行）

签名：

```python
def register(self, player_id: Identifier, controller: PlayerController, *, seat_index: int | None = None, controller_type: ControllerType | str = ControllerType.HUMAN) -> None
```

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 213 行：给 `normalized_player_id` 赋值，准备后面逻辑要用的数据。
- 第 214 行：给 `normalized_seat_index` 赋值，准备后面逻辑要用的数据。
- 第 215 行：给 `normalized_type` 赋值，准备后面逻辑要用的数据。
- 第 216 行：调用 `_require_request_action`，执行一个有副作用或校验性质的动作。
- 第 218-224 行：根据条件 `normalized_seat_index is not None` 分支处理不同情况。
- 第 226-231 行：给 `self._by_player_id[normalized_player_id]` 赋值，准备后面逻辑要用的数据。

### `get`（第 233-234 行）

签名：

```python
def get(self, player_id: Identifier) -> PlayerController
```

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 234 行：返回计算结果，把这个函数的最终答案交给调用者。

### `get_by_player_id`（第 236-237 行）

签名：

```python
def get_by_player_id(self, player_id: Identifier) -> PlayerController
```

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 237 行：返回计算结果，把这个函数的最终答案交给调用者。

### `get_by_seat_index`（第 239-240 行）

签名：

```python
def get_by_seat_index(self, seat_index: int) -> PlayerController
```

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 240 行：返回计算结果，把这个函数的最终答案交给调用者。

### `get_registration_by_player_id`（第 242-247 行）

签名：

```python
def get_registration_by_player_id(self, player_id: Identifier) -> ControllerRegistration
```

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 243 行：给 `normalized_player_id` 赋值，准备后面逻辑要用的数据。
- 第 244-247 行：尝试执行可能失败的操作，并在异常发生时转成项目自己的处理方式。

### `get_registration_by_seat_index`（第 249-255 行）

签名：

```python
def get_registration_by_seat_index(self, seat_index: int) -> ControllerRegistration
```

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 250 行：给 `normalized_seat_index` 赋值，准备后面逻辑要用的数据。
- 第 251-254 行：尝试执行可能失败的操作，并在异常发生时转成项目自己的处理方式。
- 第 255 行：返回计算结果，把这个函数的最终答案交给调用者。

### `request_action`（第 257-266 行）

签名：

```python
async def request_action(self, player_id: Identifier, observation: PlayerObservation, action_request_context: ActionRequestContext | None = None) -> PlayerAction
```

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 263-266 行：返回计算结果，把这个函数的最终答案交给调用者。

### `request_action_by_seat_index`（第 268-277 行）

签名：

```python
async def request_action_by_seat_index(self, seat_index: int, observation: PlayerObservation, action_request_context: ActionRequestContext | None = None) -> PlayerAction
```

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 274-277 行：返回计算结果，把这个函数的最终答案交给调用者。

## 类 `NoopLifecycleController`（第 280-290 行）

源码说明：Shared no-op lifecycle hooks for simple controllers.

人话：把一组相关数据和行为封装到一个类型里，供其他模块按统一接口使用。

这个类里的方法：

### `notify_action_rejected`（第 283-284 行）

签名：

```python
async def notify_action_rejected(self, action_error: ActionError | object) -> None
```

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 284 行：返回计算结果，把这个函数的最终答案交给调用者。

### `notify_hand_started`（第 286-287 行）

签名：

```python
async def notify_hand_started(self, hand_context: object) -> None
```

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 287 行：返回计算结果，把这个函数的最终答案交给调用者。

### `notify_hand_ended`（第 289-290 行）

签名：

```python
async def notify_hand_ended(self, result_summary: object) -> None
```

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 290 行：返回计算结果，把这个函数的最终答案交给调用者。

## 类 `FirstLegalActionStrategy`（第 293-306 行）

源码说明：Deterministic strategy that selects the first enabled legal action.

人话：把一组相关数据和行为封装到一个类型里，供其他模块按统一接口使用。

这个类里的方法：

### `select_action`（第 296-306 行）

签名：

```python
def select_action(self, observation: PlayerObservation, context: ActionRequestContext, legal_actions: Sequence[LegalAction]) -> LegalAction
```

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 302 行：处理 `Delete` 语句。
- 第 303-305 行：循环遍历 `legal_actions`，逐个处理里面的元素。
- 第 306 行：主动抛出错误，表示传入数据或当前状态不符合要求。

## 类 `BotPlayerController`（第 309-340 行）

继承：`NoopLifecycleController`。

源码说明：Minimal deterministic bot controller.

The default strategy chooses only from ``observation.legal_actions``. If a
custom strategy returns a full ``PlayerAction``, this controller returns it
unchanged instead of replacing it with a fallback.

人话：把一组相关数据和行为封装到一个类型里，供其他模块按统一接口使用。

字段/类变量：

- `controller_type`：类级变量，值 `ControllerType.BOT`。

这个类里的方法：

### `__init__`（第 319-320 行）

签名：

```python
def __init__(self, strategy: BotStrategy | None = None) -> None
```

人话：初始化对象，接收外部传入的数据并准备对象内部状态。

关键代码块：

- 第 320 行：给 `self.strategy` 赋值，准备后面逻辑要用的数据。

### `request_action`（第 322-340 行）

签名：

```python
async def request_action(self, observation: PlayerObservation, action_request_context: ActionRequestContext | None = None) -> PlayerAction
```

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 327 行：给 `context` 赋值，准备后面逻辑要用的数据。
- 第 328 行：给 `legal_actions` 赋值，准备后面逻辑要用的数据。
- 第 329 行：给 `decision` 赋值，准备后面逻辑要用的数据。
- 第 331-332 行：根据条件 `isinstance(decision, PlayerAction)` 分支处理不同情况。
- 第 333-334 行：根据条件 `not isinstance(decision, LegalAction)` 分支处理不同情况。
- 第 335-336 行：根据条件 `not decision.enabled` 分支处理不同情况。
- 第 337-338 行：根据条件 `decision not in legal_actions` 分支处理不同情况。
- 第 340 行：返回计算结果，把这个函数的最终答案交给调用者。

## 类 `HumanPlayerController`（第 343-485 行）

继承：`NoopLifecycleController`。

源码说明：Human controller that waits for one submitted action per pending turn.

人话：把一组相关数据和行为封装到一个类型里，供其他模块按统一接口使用。

字段/类变量：

- `controller_type`：类级变量，值 `ControllerType.HUMAN`。

这个类里的方法：

### `__init__`（第 348-350 行）

签名：

```python
def __init__(self) -> None
```

人话：初始化对象，接收外部传入的数据并准备对象内部状态。

关键代码块：

- 第 349 行：声明字段或变量 `self._pending`，类型是 `PendingHumanAction | None`。
- 第 350 行：声明字段或变量 `self._action_errors`，类型是 `list[ActionError | object]`。

### `pending_action`（第 353-354 行）

签名：

```python
def pending_action(self) -> PendingHumanAction | None
```

装饰器：`@property`。

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 354 行：返回计算结果，把这个函数的最终答案交给调用者。

### `pending_context`（第 357-358 行）

签名：

```python
def pending_context(self) -> ActionRequestContext | None
```

装饰器：`@property`。

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 358 行：返回计算结果，把这个函数的最终答案交给调用者。

### `pending_turn_id`（第 361-362 行）

签名：

```python
def pending_turn_id(self) -> Identifier | None
```

装饰器：`@property`。

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 362 行：返回计算结果，把这个函数的最终答案交给调用者。

### `last_action_error`（第 365-368 行）

签名：

```python
def last_action_error(self) -> ActionError | object | None
```

装饰器：`@property`。

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 366-367 行：根据条件 `not self._action_errors` 分支处理不同情况。
- 第 368 行：返回计算结果，把这个函数的最终答案交给调用者。

### `action_errors`（第 371-372 行）

签名：

```python
def action_errors(self) -> tuple[ActionError | object, ...]
```

装饰器：`@property`。

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 372 行：返回计算结果，把这个函数的最终答案交给调用者。

### `request_action`（第 374-389 行）

签名：

```python
async def request_action(self, observation: PlayerObservation, action_request_context: ActionRequestContext | None = None) -> PlayerAction
```

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 379 行：给 `context` 赋值，准备后面逻辑要用的数据。
- 第 380 行：给 `pending` 赋值，准备后面逻辑要用的数据。
- 第 381-389 行：尝试执行可能失败的操作，并在异常发生时转成项目自己的处理方式。

### `submit_action`（第 391-410 行）

签名：

```python
async def submit_action(self, action: PlayerAction | Mapping[str, Any]) -> PlayerAction
```

人话：提交动作或请求，把外部输入交给下一层处理。

关键代码块：

- 第 392 行：给 `pending` 赋值，准备后面逻辑要用的数据。
- 第 393 行：给 `submitted_action` 赋值，准备后面逻辑要用的数据。
- 第 394-399 行：根据条件 `pending is None` 分支处理不同情况。
- 第 400-405 行：根据条件 `pending.future.done()` 分支处理不同情况。
- 第 407 行：调用 `_validate_submitted_action_matches_context`，执行一个有副作用或校验性质的动作。
- 第 408 行：给 `human_action` 赋值，准备后面逻辑要用的数据。
- 第 409 行：调用 `pending.future.set_result`，执行一个有副作用或校验性质的动作。
- 第 410 行：返回计算结果，把这个函数的最终答案交给调用者。

### `notify_action_rejected`（第 412-427 行）

签名：

```python
async def notify_action_rejected(self, action_error: ActionError | object) -> None
```

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 413 行：调用 `self._action_errors.append`，执行一个有副作用或校验性质的动作。
- 第 414 行：给 `pending` 赋值，准备后面逻辑要用的数据。
- 第 415-416 行：根据条件 `pending is None` 分支处理不同情况。
- 第 418 行：给 `pending.last_error` 赋值，准备后面逻辑要用的数据。
- 第 419-423 行：根据条件 `isinstance(action_error, ActionError) and (not action_error.retry_same_player)` 分支处理不同情况。
- 第 425-426 行：根据条件 `_action_error_matches_context(action_error, pending.context) and pending.future.done()` 分支处理不同情况。
- 第 427 行：返回计算结果，把这个函数的最终答案交给调用者。

### `notify_hand_started`（第 429-431 行）

签名：

```python
async def notify_hand_started(self, hand_context: object) -> None
```

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 430 行：给 `self._pending` 赋值，准备后面逻辑要用的数据。
- 第 431 行：调用 `self._action_errors.clear`，执行一个有副作用或校验性质的动作。

### `notify_hand_ended`（第 433-437 行）

签名：

```python
async def notify_hand_ended(self, result_summary: object) -> None
```

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 434 行：给 `pending` 赋值，准备后面逻辑要用的数据。
- 第 435-436 行：根据条件 `pending is not None and (not pending.future.done())` 分支处理不同情况。
- 第 437 行：给 `self._pending` 赋值，准备后面逻辑要用的数据。

### `_ensure_pending_action`（第 439-485 行）

签名：

```python
def _ensure_pending_action(self, observation: PlayerObservation, context: ActionRequestContext) -> PendingHumanAction
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 444 行：给 `pending` 赋值，准备后面逻辑要用的数据。
- 第 445-452 行：根据条件 `pending is None` 分支处理不同情况。
- 第 454-464 行：根据条件 `_same_action_context(pending.context, context)` 分支处理不同情况。
- 第 466-474 行：根据条件 `pending.last_error is not None` 分支处理不同情况。
- 第 476-477 行：根据条件 `not pending.future.done()` 分支处理不同情况。
- 第 479-484 行：给 `self._pending` 赋值，准备后面逻辑要用的数据。
- 第 485 行：返回计算结果，把这个函数的最终答案交给调用者。

## 类 `FutureAgentPlayerController`（第 488-499 行）

继承：`NoopLifecycleController`。

源码说明：Reserved future-agent controller type without real LLM/GTO behavior.

人话：把一组相关数据和行为封装到一个类型里，供其他模块按统一接口使用。

字段/类变量：

- `controller_type`：类级变量，值 `ControllerType.FUTURE_AGENT`。

这个类里的方法：

### `request_action`（第 493-499 行）

签名：

```python
async def request_action(self, observation: PlayerObservation, action_request_context: ActionRequestContext | None = None) -> PlayerAction
```

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 498 行：处理 `Delete` 语句。
- 第 499 行：主动抛出错误，表示传入数据或当前状态不符合要求。

## 模块级函数

### `_player_action_from_legal_action`（第 505-518 行）

签名：

```python
def _player_action_from_legal_action(legal_action: LegalAction, context: ActionRequestContext, source: ActionSource) -> PlayerAction
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 510-518 行：返回计算结果，把这个函数的最终答案交给调用者。

### `_amount_for_legal_action`（第 521-530 行）

签名：

```python
def _amount_for_legal_action(legal_action: LegalAction) -> int | None
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 522-523 行：根据条件 `legal_action.action_type is not ActionType.RAISE_TO` 分支处理不同情况。
- 第 524-525 行：根据条件 `legal_action.amount_fixed is not None` 分支处理不同情况。
- 第 526-527 行：根据条件 `legal_action.amount_min is not None` 分支处理不同情况。
- 第 528-529 行：根据条件 `legal_action.amount_max is not None` 分支处理不同情况。
- 第 530 行：主动抛出错误，表示传入数据或当前状态不符合要求。

### `_context_from_observation`（第 533-545 行）

签名：

```python
def _context_from_observation(observation: PlayerObservation) -> ActionRequestContext
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 534-545 行：返回计算结果，把这个函数的最终答案交给调用者。

### `_read_observation_field`（第 548-553 行）

签名：

```python
def _read_observation_field(observation: object, *names: str) -> object
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 549-551 行：循环遍历 `names`，逐个处理里面的元素。
- 第 552 行：给 `joined_names` 赋值，准备后面逻辑要用的数据。
- 第 553 行：主动抛出错误，表示传入数据或当前状态不符合要求。

### `_legal_actions_from_observation`（第 556-572 行）

签名：

```python
def _legal_actions_from_observation(observation: PlayerObservation) -> tuple[LegalAction, ...]
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 557 行：给 `raw_legal_actions` 赋值，准备后面逻辑要用的数据。
- 第 558 行：声明字段或变量 `iterable`，类型是 `Iterable[object]`。
- 第 559-567 行：根据条件 `isinstance(raw_legal_actions, LegalActionSet)` 分支处理不同情况。
- 第 569 行：给 `legal_actions` 赋值，准备后面逻辑要用的数据。
- 第 570-571 行：根据条件 `not legal_actions` 分支处理不同情况。
- 第 572 行：返回计算结果，把这个函数的最终答案交给调用者。

### `_coerce_legal_action`（第 575-582 行）

签名：

```python
def _coerce_legal_action(value: object) -> LegalAction
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 576-577 行：根据条件 `isinstance(value, LegalAction)` 分支处理不同情况。
- 第 578-579 行：根据条件 `isinstance(value, Mapping)` 分支处理不同情况。
- 第 580-581 行：根据条件 `isinstance(value, str)` 分支处理不同情况。
- 第 582 行：主动抛出错误，表示传入数据或当前状态不符合要求。

### `_coerce_player_action`（第 585-595 行）

签名：

```python
def _coerce_player_action(action: PlayerAction | Mapping[str, Any]) -> PlayerAction
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 586-587 行：根据条件 `isinstance(action, PlayerAction)` 分支处理不同情况。
- 第 588-589 行：根据条件 `isinstance(action, Mapping)` 分支处理不同情况。
- 第 590-595 行：主动抛出错误，表示传入数据或当前状态不符合要求。

### `_validate_submitted_action_matches_context`（第 598-619 行）

签名：

```python
def _validate_submitted_action_matches_context(action: PlayerAction, context: ActionRequestContext) -> None
```

人话：校验输入或状态是否合法，发现问题时返回错误或抛出异常。

关键代码块：

- 第 602-607 行：根据条件 `action.player_id != context.player_id` 分支处理不同情况。
- 第 608-613 行：根据条件 `action.seat_index != context.seat_index` 分支处理不同情况。
- 第 614-619 行：根据条件 `action.hand_id != context.hand_id or action.turn_id != context.turn_id` 分支处理不同情况。

### `_submission_rejected`（第 622-636 行）

签名：

```python
def _submission_rejected(code: str, message: str, action: PlayerAction) -> ActionSubmissionRejected
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 627-636 行：返回计算结果，把这个函数的最终答案交给调用者。

### `_action_error_matches_context`（第 639-649 行）

签名：

```python
def _action_error_matches_context(action_error: ActionError | object, context: ActionRequestContext) -> bool
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 643-644 行：根据条件 `not isinstance(action_error, ActionError)` 分支处理不同情况。
- 第 645-649 行：返回计算结果，把这个函数的最终答案交给调用者。

### `_same_action_context`（第 652-659 行）

签名：

```python
def _same_action_context(left: ActionRequestContext, right: ActionRequestContext) -> bool
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 653-659 行：返回计算结果，把这个函数的最终答案交给调用者。

### `_parse_controller_type`（第 662-669 行）

签名：

```python
def _parse_controller_type(controller_type: ControllerType | str) -> ControllerType
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 663-664 行：根据条件 `isinstance(controller_type, ControllerType)` 分支处理不同情况。
- 第 665-669 行：尝试执行可能失败的操作，并在异常发生时转成项目自己的处理方式。

### `_require_request_action`（第 672-674 行）

签名：

```python
def _require_request_action(controller: PlayerController) -> None
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 673-674 行：根据条件 `not callable(getattr(controller, 'request_action', None))` 分支处理不同情况。

### `_validate_identifier`（第 677-684 行）

签名：

```python
def _validate_identifier(value: object, field_name: str) -> Identifier
```

人话：校验输入或状态是否合法，发现问题时返回错误或抛出异常。

关键代码块：

- 第 678-679 行：根据条件 `isinstance(value, bool) or value is None` 分支处理不同情况。
- 第 680-681 行：根据条件 `isinstance(value, int)` 分支处理不同情况。
- 第 682-683 行：根据条件 `isinstance(value, str) and value` 分支处理不同情况。
- 第 684 行：主动抛出错误，表示传入数据或当前状态不符合要求。

### `_validate_seat_index`（第 687-690 行）

签名：

```python
def _validate_seat_index(value: object) -> int
```

人话：校验输入或状态是否合法，发现问题时返回错误或抛出异常。

关键代码块：

- 第 688-689 行：根据条件 `isinstance(value, bool) or not isinstance(value, int) or value < 0` 分支处理不同情况。
- 第 690 行：返回计算结果，把这个函数的最终答案交给调用者。

### `_require_mapping`（第 693-695 行）

签名：

```python
def _require_mapping(data: object, model_name: str) -> None
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 694-695 行：根据条件 `not isinstance(data, Mapping)` 分支处理不同情况。

### `_require_keys`（第 698-702 行）

签名：

```python
def _require_keys(data: Mapping[str, Any], model_name: str, keys: tuple[str, ...]) -> None
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 699 行：给 `missing` 赋值，准备后面逻辑要用的数据。
- 第 700-702 行：根据条件 `missing` 分支处理不同情况。

## 对外公开接口

`__all__` 声明这个模块希望别人主要使用这些名字：

- `ActionRequestContext`
- `ActionSubmissionRejected`
- `BotPlayerController`
- `BotStrategy`
- `BotStrategyError`
- `ControllerError`
- `ControllerRegistration`
- `ControllerRegistry`
- `ControllerType`
- `DeterministicBotPlayerController`
- `FirstLegalActionStrategy`
- `FutureAgentPlayerController`
- `HumanPlayerController`
- `NoLegalActionAvailable`
- `PendingActionError`
- `PendingHumanAction`
- `PlayerController`
- `PlayerObservation`

## 初学者阅读建议

先看“这个文件是干什么的”，再看类和函数标题。遇到以下划线开头的函数，可以先理解成内部工具；遇到 `to_dict/from_dict/to_json/from_json`，重点记住它们是在对象、字典和 JSON 之间转换。
