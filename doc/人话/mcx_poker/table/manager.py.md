# `mcx_poker/table/manager.py` 人话讲解

源文件：`/Users/machengqi/Documents/mcx-poker/src/mcx_poker/table/manager.py`

## 这个文件是干什么的

源码说明：Long-lived local table state and hand lifecycle management.

人话概括：

负责牌桌生命周期、座位、筹码、手牌推进和广播。

## 导入区

- 第 3 行：从 `__future__` 导入 `annotations`。
- 第 5 行：导入 `json`。
- 第 6 行：从 `collections.abc` 导入 `Mapping, Sequence`。
- 第 7 行：从 `dataclasses` 导入 `dataclass, field`。
- 第 8 行：从 `enum` 导入 `StrEnum`。
- 第 9 行：从 `typing` 导入 `Any, Protocol, Self, runtime_checkable`。

人话：导入区是在声明“这个文件需要哪些外部工具”。标准库通常提供基础能力，项目内导入则说明它依赖哪些业务模块。

## 顶层常量和类型

- 第 11 行：`SEAT_COUNT` = `6`。人话：在模块级别准备一个后面会反复使用的值。
- 第 12 行：`DEFAULT_TABLE_ID` = `'local-table'`。人话：在模块级别准备一个后面会反复使用的值。
- 第 13 行：`DEFAULT_SMALL_BLIND` = `1`。人话：在模块级别准备一个后面会反复使用的值。
- 第 14 行：`DEFAULT_BIG_BLIND` = `2`。人话：在模块级别准备一个后面会反复使用的值。
- 第 15 行：`DEFAULT_ANTE` = `0`。人话：在模块级别准备一个后面会反复使用的值。
- 第 16 行：`DEFAULT_STARTING_STACK` = `200`。人话：在模块级别准备一个后面会反复使用的值。
- 第 17 行：`DEFAULT_MIN_ACTIVE_PLAYERS` = `2`。人话：在模块级别准备一个后面会反复使用的值。
- 第 906-936 行：`__all__` = `['AdapterUnavailableError', 'ControllerType', 'CreateHandRequest', 'DEFAULT_ANTE', 'DEFAULT_BIG_BLIND', 'DEFAULT_MIN_ACTIVE_PLAYERS', 'DEFAULT_SMALL_BLIND', 'DEFAULT_STARTING_STACK', 'HandAdapter', 'HandContext', 'HandSettlement', 'HandSettlementMismatchError', 'HandSnapshot', 'InvalidStackError', 'NoCurrentHandError', 'PlayerAlreadySeatedError', 'SEAT_COUNT', 'SeatNotFoundError', 'SeatOccupiedError', 'SeatSnapshot', 'SeatState', 'SeatStatus', 'TableManager', 'TableManagerError', 'TableNotInitializedError', 'TableSnapshot', 'TableState', 'TableStateConflictError', 'TableStatus']`。人话：在模块级别准备一个后面会反复使用的值。

## 类 `TableStatus`（第 20-26 行）

继承：`StrEnum`。

源码说明：Lifecycle state for the local table.

人话：把一组相关数据和行为封装到一个类型里，供其他模块按统一接口使用。

字段/类变量：

- `IDLE`：类级变量，值 `'idle'`。
- `RUNNING`：类级变量，值 `'running'`。
- `PAUSED`：类级变量，值 `'paused'`。
- `RESETTING`：类级变量，值 `'resetting'`。

## 类 `SeatStatus`（第 29-35 行）

继承：`StrEnum`。

源码说明：Public occupancy state for a fixed table seat.

人话：把一组相关数据和行为封装到一个类型里，供其他模块按统一接口使用。

字段/类变量：

- `EMPTY`：类级变量，值 `'empty'`。
- `SEATED`：类级变量，值 `'seated'`。
- `SITTING_OUT`：类级变量，值 `'sitting_out'`。
- `IN_HAND`：类级变量，值 `'in_hand'`。

## 类 `ControllerType`（第 38-43 行）

继承：`StrEnum`。

源码说明：Supported controller ownership types for seated players.

人话：把一组相关数据和行为封装到一个类型里，供其他模块按统一接口使用。

字段/类变量：

- `HUMAN`：类级变量，值 `'human'`。
- `BOT`：类级变量，值 `'bot'`。
- `FUTURE_AGENT`：类级变量，值 `'future_agent'`。

## 类 `TableManagerError`（第 46-66 行）

继承：`ValueError`。

源码说明：Base platform error raised by table-manager commands.

人话：把一组相关数据和行为封装到一个类型里，供其他模块按统一接口使用。

字段/类变量：

- `code`：类级变量，值 `'table_manager_error'`。

这个类里的方法：

### `__init__`（第 51-59 行）

签名：

```python
def __init__(self, message: str | None = None, *, details: Mapping[str, object] | None = None) -> None
```

人话：初始化对象，接收外部传入的数据并准备对象内部状态。

关键代码块：

- 第 57 行：调用 `super().__init__`，执行一个有副作用或校验性质的动作。
- 第 58 行：给 `self.message` 赋值，准备后面逻辑要用的数据。
- 第 59 行：给 `self.details` 赋值，准备后面逻辑要用的数据。

### `error_code`（第 62-63 行）

签名：

```python
def error_code(self) -> str
```

装饰器：`@property`。

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 63 行：返回计算结果，把这个函数的最终答案交给调用者。

### `to_dict`（第 65-66 行）

签名：

```python
def to_dict(self) -> dict[str, object]
```

人话：把对象转成普通字典，方便 API、日志、测试或 JSON 序列化使用。

关键代码块：

- 第 66 行：返回计算结果，把这个函数的最终答案交给调用者。

## 类 `TableNotInitializedError`（第 69-70 行）

继承：`TableManagerError`。

人话：把一组相关数据和行为封装到一个类型里，供其他模块按统一接口使用。

字段/类变量：

- `code`：类级变量，值 `'table_not_initialized'`。

## 类 `TableStateConflictError`（第 73-74 行）

继承：`TableManagerError`。

人话：把一组相关数据和行为封装到一个类型里，供其他模块按统一接口使用。

字段/类变量：

- `code`：类级变量，值 `'table_state_conflict'`。

## 类 `SeatNotFoundError`（第 77-78 行）

继承：`TableManagerError`。

人话：把一组相关数据和行为封装到一个类型里，供其他模块按统一接口使用。

字段/类变量：

- `code`：类级变量，值 `'seat_not_found'`。

## 类 `SeatOccupiedError`（第 81-82 行）

继承：`TableManagerError`。

人话：把一组相关数据和行为封装到一个类型里，供其他模块按统一接口使用。

字段/类变量：

- `code`：类级变量，值 `'seat_occupied'`。

## 类 `PlayerAlreadySeatedError`（第 85-86 行）

继承：`TableManagerError`。

人话：把一组相关数据和行为封装到一个类型里，供其他模块按统一接口使用。

字段/类变量：

- `code`：类级变量，值 `'player_already_seated'`。

## 类 `InvalidStackError`（第 89-90 行）

继承：`TableManagerError`。

人话：把一组相关数据和行为封装到一个类型里，供其他模块按统一接口使用。

字段/类变量：

- `code`：类级变量，值 `'invalid_stack'`。

## 类 `NoCurrentHandError`（第 93-94 行）

继承：`TableManagerError`。

人话：把一组相关数据和行为封装到一个类型里，供其他模块按统一接口使用。

字段/类变量：

- `code`：类级变量，值 `'no_current_hand'`。

## 类 `HandSettlementMismatchError`（第 97-98 行）

继承：`TableManagerError`。

人话：把一组相关数据和行为封装到一个类型里，供其他模块按统一接口使用。

字段/类变量：

- `code`：类级变量，值 `'hand_settlement_mismatch'`。

## 类 `AdapterUnavailableError`（第 101-102 行）

继承：`TableManagerError`。

人话：把一组相关数据和行为封装到一个类型里，供其他模块按统一接口使用。

字段/类变量：

- `code`：类级变量，值 `'adapter_unavailable'`。

## 类 `SeatState`（第 106-124 行）

装饰器：`@dataclass(slots=True)`。

源码说明：Mutable long-lived state for one fixed seat.

人话：把一组相关数据和行为封装到一个类型里，供其他模块按统一接口使用。

字段/类变量：

- `seat_index`：类型 `int`。
- `player_id`：类型 `str | None`，默认值 `None`。
- `player_name`：类型 `str | None`，默认值 `None`。
- `controller_type`：类型 `ControllerType`，默认值 `ControllerType.HUMAN`。
- `stack`：类型 `int`，默认值 `0`。
- `status`：类型 `SeatStatus`，默认值 `SeatStatus.EMPTY`。

这个类里的方法：

### `to_snapshot`（第 116-124 行）

签名：

```python
def to_snapshot(self) -> SeatSnapshot
```

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 117-124 行：返回计算结果，把这个函数的最终答案交给调用者。

## 类 `HandContext`（第 128-143 行）

装饰器：`@dataclass(slots=True)`。

源码说明：Mutable context for the currently active hand.

人话：把一组相关数据和行为封装到一个类型里，供其他模块按统一接口使用。

字段/类变量：

- `hand_id`：类型 `str`。
- `button_seat_index`：类型 `int`。
- `active_seat_indexes`：类型 `tuple[int, ...]`。
- `starting_stacks`：类型 `dict[int, int]`。
- `adapter_hand_ref`：类型 `Any`，默认值 `None`。

这个类里的方法：

### `to_snapshot`（第 137-143 行）

签名：

```python
def to_snapshot(self) -> HandSnapshot
```

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 138-143 行：返回计算结果，把这个函数的最终答案交给调用者。

## 类 `TableState`（第 147-156 行）

装饰器：`@dataclass(slots=True)`。

源码说明：Mutable long-lived state for the single local table.

人话：把一组相关数据和行为封装到一个类型里，供其他模块按统一接口使用。

字段/类变量：

- `table_id`：类型 `str`。
- `seat_count`：类型 `int`。
- `status`：类型 `TableStatus`。
- `seats`：类型 `list[SeatState]`。
- `button_seat_index`：类型 `int`。
- `current_hand_id`：类型 `str | None`，默认值 `None`。
- `hand_context`：类型 `HandContext | None`，默认值 `None`。

## 类 `SeatSnapshot`（第 160-178 行）

装饰器：`@dataclass(frozen=True, slots=True)`。

源码说明：Public seat state included in table snapshots.

人话：把一组相关数据和行为封装到一个类型里，供其他模块按统一接口使用。

字段/类变量：

- `seat_index`：类型 `int`。
- `player_id`：类型 `str | None`，默认值 `None`。
- `player_name`：类型 `str | None`，默认值 `None`。
- `controller_type`：类型 `ControllerType`，默认值 `ControllerType.HUMAN`。
- `stack`：类型 `int`，默认值 `0`。
- `status`：类型 `SeatStatus`，默认值 `SeatStatus.EMPTY`。

这个类里的方法：

### `to_dict`（第 170-178 行）

签名：

```python
def to_dict(self) -> dict[str, object]
```

人话：把对象转成普通字典，方便 API、日志、测试或 JSON 序列化使用。

关键代码块：

- 第 171-178 行：返回计算结果，把这个函数的最终答案交给调用者。

## 类 `HandSnapshot`（第 182-200 行）

装饰器：`@dataclass(frozen=True, slots=True)`。

源码说明：Public summary for the current hand.

人话：把一组相关数据和行为封装到一个类型里，供其他模块按统一接口使用。

字段/类变量：

- `hand_id`：类型 `str`。
- `button_seat_index`：类型 `int`。
- `active_seat_indexes`：类型 `tuple[int, ...]`。
- `starting_stacks`：类型 `dict[int, int]`。

这个类里的方法：

### `__post_init__`（第 190-192 行）

签名：

```python
def __post_init__(self) -> None
```

人话：dataclass 创建对象后自动执行，用来做校验、标准化或补充字段。

关键代码块：

- 第 191 行：调用 `object.__setattr__`，执行一个有副作用或校验性质的动作。
- 第 192 行：调用 `object.__setattr__`，执行一个有副作用或校验性质的动作。

### `to_dict`（第 194-200 行）

签名：

```python
def to_dict(self) -> dict[str, object]
```

人话：把对象转成普通字典，方便 API、日志、测试或 JSON 序列化使用。

关键代码块：

- 第 195-200 行：返回计算结果，把这个函数的最终答案交给调用者。

## 类 `TableSnapshot`（第 204-232 行）

装饰器：`@dataclass(frozen=True, slots=True)`。

源码说明：Public table state safe for API, events, observations, and UI.

人话：把一组相关数据和行为封装到一个类型里，供其他模块按统一接口使用。

字段/类变量：

- `table_id`：类型 `str`。
- `status`：类型 `TableStatus`。
- `seat_count`：类型 `int`。
- `seats`：类型 `tuple[SeatSnapshot, ...]`。
- `button_seat_index`：类型 `int`。
- `current_hand_id`：类型 `str | None`，默认值 `None`。
- `current_hand`：类型 `HandSnapshot | None`，默认值 `None`。

这个类里的方法：

### `hand_id`（第 216-217 行）

签名：

```python
def hand_id(self) -> str | None
```

装饰器：`@property`。

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 217 行：返回计算结果，把这个函数的最终答案交给调用者。

### `to_dict`（第 219-229 行）

签名：

```python
def to_dict(self) -> dict[str, object]
```

人话：把对象转成普通字典，方便 API、日志、测试或 JSON 序列化使用。

关键代码块：

- 第 220-229 行：返回计算结果，把这个函数的最终答案交给调用者。

### `to_json`（第 231-232 行）

签名：

```python
def to_json(self) -> str
```

人话：把对象转成 JSON 字符串，方便跨进程或前后端传输。

关键代码块：

- 第 232 行：返回计算结果，把这个函数的最终答案交给调用者。

## 类 `CreateHandRequest`（第 236-260 行）

装饰器：`@dataclass(frozen=True, slots=True)`。

源码说明：Platform-level input passed to the injected hand adapter.

人话：创建并返回一个新对象，通常会把多个输入整理到统一格式。

字段/类变量：

- `hand_id`：类型 `str`。
- `seat_to_player`：类型 `dict[int, str]`。
- `starting_stacks`：类型 `dict[int, int]`。
- `button_seat_index`：类型 `int`。
- `small_blind`：类型 `int`，默认值 `DEFAULT_SMALL_BLIND`。
- `big_blind`：类型 `int`，默认值 `DEFAULT_BIG_BLIND`。
- `ante`：类型 `int`，默认值 `DEFAULT_ANTE`。

这个类里的方法：

### `__post_init__`（第 247-249 行）

签名：

```python
def __post_init__(self) -> None
```

人话：dataclass 创建对象后自动执行，用来做校验、标准化或补充字段。

关键代码块：

- 第 248 行：调用 `object.__setattr__`，执行一个有副作用或校验性质的动作。
- 第 249 行：调用 `object.__setattr__`，执行一个有副作用或校验性质的动作。

### `to_dict`（第 251-260 行）

签名：

```python
def to_dict(self) -> dict[str, object]
```

人话：把对象转成普通字典，方便 API、日志、测试或 JSON 序列化使用。

关键代码块：

- 第 252-260 行：返回计算结果，把这个函数的最终答案交给调用者。

## 类 `HandSettlement`（第 264-295 行）

装饰器：`@dataclass(frozen=True, slots=True)`。

源码说明：Final hand result consumed by the table manager.

人话：把一组相关数据和行为封装到一个类型里，供其他模块按统一接口使用。

字段/类变量：

- `hand_id`：类型 `str`。
- `final_stacks`：类型 `dict[int, int]`。
- `payoffs`：类型 `dict[int, int]`，默认值 `field(default_factory=dict)`。
- `winners`：类型 `tuple[Mapping[str, object], ...]`，默认值 `()`。
- `final_board`：类型 `tuple[str, ...]`，默认值 `()`。
- `showdown_summary`：类型 `Mapping[str, object] | None`，默认值 `None`。
- `operations_summary`：类型 `tuple[Mapping[str, object], ...]`，默认值 `()`。

这个类里的方法：

### `__post_init__`（第 275-280 行）

签名：

```python
def __post_init__(self) -> None
```

人话：dataclass 创建对象后自动执行，用来做校验、标准化或补充字段。

关键代码块：

- 第 276 行：调用 `object.__setattr__`，执行一个有副作用或校验性质的动作。
- 第 277 行：调用 `object.__setattr__`，执行一个有副作用或校验性质的动作。
- 第 278 行：调用 `object.__setattr__`，执行一个有副作用或校验性质的动作。
- 第 279 行：调用 `object.__setattr__`，执行一个有副作用或校验性质的动作。
- 第 280 行：调用 `object.__setattr__`，执行一个有副作用或校验性质的动作。

### `from_mapping`（第 283-295 行）

签名：

```python
def from_mapping(cls, data: Mapping[str, object]) -> Self
```

装饰器：`@classmethod`。

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 284-295 行：返回计算结果，把这个函数的最终答案交给调用者。

## 类 `HandAdapter`（第 299-302 行）

装饰器：`@runtime_checkable`。

继承：`Protocol`。

源码说明：Adapter boundary used to create one hand from platform state.

人话：把一组相关数据和行为封装到一个类型里，供其他模块按统一接口使用。

这个类里的方法：

### `create_hand`（第 302 行）

签名：

```python
def create_hand(self, request: CreateHandRequest) -> Any
```

人话：创建并返回一个新对象，通常会把多个输入整理到统一格式。

关键代码块：

- 第 302 行：执行一个表达式，通常是调用函数或触发某个对象行为。

## 类 `TableManager`（第 305-629 行）

源码说明：Command surface for the unique local table.

人话：把一组相关数据和行为封装到一个类型里，供其他模块按统一接口使用。

这个类里的方法：

### `__init__`（第 308-339 行）

签名：

```python
def __init__(self, *, adapter: HandAdapter | None = None, table_id: str = DEFAULT_TABLE_ID, seat_count: int = SEAT_COUNT, default_starting_stack: int = DEFAULT_STARTING_STACK, minimum_active_players: int = DEFAULT_MIN_ACTIVE_PLAYERS, small_blind: int = DEFAULT_SMALL_BLIND, big_blind: int = DEFAULT_BIG_BLIND, ante: int = DEFAULT_ANTE) -> None
```

人话：初始化对象，接收外部传入的数据并准备对象内部状态。

关键代码块：

- 第 320-321 行：根据条件 `seat_count != SEAT_COUNT` 分支处理不同情况。
- 第 322 行：给 `self.adapter` 赋值，准备后面逻辑要用的数据。
- 第 323 行：给 `self.table_id` 赋值，准备后面逻辑要用的数据。
- 第 324 行：给 `self.seat_count` 赋值，准备后面逻辑要用的数据。
- 第 325-328 行：给 `self.default_starting_stack` 赋值，准备后面逻辑要用的数据。
- 第 329-332 行：给 `self.minimum_active_players` 赋值，准备后面逻辑要用的数据。
- 第 333-334 行：根据条件 `self.minimum_active_players > self.seat_count` 分支处理不同情况。
- 第 335 行：给 `self.small_blind` 赋值，准备后面逻辑要用的数据。
- 第 336 行：给 `self.big_blind` 赋值，准备后面逻辑要用的数据。
- 第 337 行：给 `self.ante` 赋值，准备后面逻辑要用的数据。
- 第 338 行：声明字段或变量 `self._state`，类型是 `TableState | None`。
- 第 339 行：给 `self._next_hand_number` 赋值，准备后面逻辑要用的数据。

### `state`（第 342-343 行）

签名：

```python
def state(self) -> TableState
```

装饰器：`@property`。

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 343 行：返回计算结果，把这个函数的最终答案交给调用者。

### `initialize_table`（第 345-380 行）

签名：

```python
def initialize_table(self, config: Mapping[str, object] | None = None) -> TableSnapshot
```

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 346 行：给 `config` 赋值，准备后面逻辑要用的数据。
- 第 347 行：给 `table_id` 赋值，准备后面逻辑要用的数据。
- 第 348-351 行：给 `default_stack` 赋值，准备后面逻辑要用的数据。
- 第 352-355 行：给 `minimum_players` 赋值，准备后面逻辑要用的数据。
- 第 356-357 行：根据条件 `minimum_players > SEAT_COUNT` 分支处理不同情况。
- 第 359 行：给 `self.table_id` 赋值，准备后面逻辑要用的数据。
- 第 360 行：给 `self.default_starting_stack` 赋值，准备后面逻辑要用的数据。
- 第 361 行：给 `self.minimum_active_players` 赋值，准备后面逻辑要用的数据。
- 第 362-365 行：给 `self.small_blind` 赋值，准备后面逻辑要用的数据。
- 第 366-368 行：给 `self.big_blind` 赋值，准备后面逻辑要用的数据。
- 第 369 行：给 `self.ante` 赋值，准备后面逻辑要用的数据。
- 第 370 行：给 `self._next_hand_number` 赋值，准备后面逻辑要用的数据。
- 第 371-379 行：给 `self._state` 赋值，准备后面逻辑要用的数据。
- 第 380 行：返回计算结果，把这个函数的最终答案交给调用者。

### `seat_player`（第 382-426 行）

签名：

```python
def seat_player(self, seat_index: int, *args: object, player_id: str | None = None, player_name: str | None = None, controller_type: ControllerType | str = ControllerType.HUMAN, starting_stack: int | None = None, stack: int | None = None) -> TableSnapshot
```

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 392 行：给 `state` 赋值，准备后面逻辑要用的数据。
- 第 393-397 行：根据条件 `state.status is not TableStatus.IDLE` 分支处理不同情况。
- 第 399-407 行：给 `parsed` 赋值，准备后面逻辑要用的数据。
- 第 408 行：给 `seat` 赋值，准备后面逻辑要用的数据。
- 第 409-413 行：根据条件 `seat.player_id is not None` 分支处理不同情况。
- 第 414 行：给 `existing_seat` 赋值，准备后面逻辑要用的数据。
- 第 415-419 行：根据条件 `existing_seat is not None` 分支处理不同情况。
- 第 421 行：给 `seat.player_id` 赋值，准备后面逻辑要用的数据。
- 第 422 行：给 `seat.player_name` 赋值，准备后面逻辑要用的数据。
- 第 423 行：给 `seat.controller_type` 赋值，准备后面逻辑要用的数据。
- 第 424 行：给 `seat.stack` 赋值，准备后面逻辑要用的数据。
- 第 425 行：给 `seat.status` 赋值，准备后面逻辑要用的数据。
- 第 426 行：返回计算结果，把这个函数的最终答案交给调用者。

### `start_table`（第 428-445 行）

签名：

```python
def start_table(self, table_id: str | None = None) -> TableSnapshot
```

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 429 行：给 `state` 赋值，准备后面逻辑要用的数据。
- 第 430-434 行：根据条件 `state.status is not TableStatus.IDLE` 分支处理不同情况。
- 第 435 行：给 `active_count` 赋值，准备后面逻辑要用的数据。
- 第 436-443 行：根据条件 `active_count < self.minimum_active_players` 分支处理不同情况。
- 第 444 行：给 `state.status` 赋值，准备后面逻辑要用的数据。
- 第 445 行：返回计算结果，把这个函数的最终答案交给调用者。

### `pause_table`（第 447-455 行）

签名：

```python
def pause_table(self, table_id: str | None = None) -> TableSnapshot
```

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 448 行：给 `state` 赋值，准备后面逻辑要用的数据。
- 第 449-453 行：根据条件 `state.status is not TableStatus.RUNNING` 分支处理不同情况。
- 第 454 行：给 `state.status` 赋值，准备后面逻辑要用的数据。
- 第 455 行：返回计算结果，把这个函数的最终答案交给调用者。

### `resume_table`（第 457-465 行）

签名：

```python
def resume_table(self, table_id: str | None = None) -> TableSnapshot
```

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 458 行：给 `state` 赋值，准备后面逻辑要用的数据。
- 第 459-463 行：根据条件 `state.status is not TableStatus.PAUSED` 分支处理不同情况。
- 第 464 行：给 `state.status` 赋值，准备后面逻辑要用的数据。
- 第 465 行：返回计算结果，把这个函数的最终答案交给调用者。

### `reset_table`（第 467-476 行）

签名：

```python
def reset_table(self, table_id: str | None = None) -> TableSnapshot
```

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 468 行：给 `state` 赋值，准备后面逻辑要用的数据。
- 第 469 行：给 `state.status` 赋值，准备后面逻辑要用的数据。
- 第 470 行：给 `state.seats` 赋值，准备后面逻辑要用的数据。
- 第 471 行：给 `state.button_seat_index` 赋值，准备后面逻辑要用的数据。
- 第 472 行：给 `state.current_hand_id` 赋值，准备后面逻辑要用的数据。
- 第 473 行：给 `state.hand_context` 赋值，准备后面逻辑要用的数据。
- 第 474 行：给 `state.status` 赋值，准备后面逻辑要用的数据。
- 第 475 行：给 `self._next_hand_number` 赋值，准备后面逻辑要用的数据。
- 第 476 行：返回计算结果，把这个函数的最终答案交给调用者。

### `create_next_hand`（第 478-533 行）

签名：

```python
def create_next_hand(self, table_id: str | None = None) -> HandContext
```

人话：创建并返回一个新对象，通常会把多个输入整理到统一格式。

关键代码块：

- 第 479 行：给 `state` 赋值，准备后面逻辑要用的数据。
- 第 480-484 行：根据条件 `state.status is not TableStatus.RUNNING` 分支处理不同情况。
- 第 485-489 行：根据条件 `state.hand_context is not None or state.current_hand_id is not None` 分支处理不同情况。
- 第 491 行：给 `active_seats` 赋值，准备后面逻辑要用的数据。
- 第 492-499 行：根据条件 `len(active_seats) < self.minimum_active_players` 分支处理不同情况。
- 第 500 行：给 `button_seat_index` 赋值，准备后面逻辑要用的数据。
- 第 501 行：给 `hand_id` 赋值，准备后面逻辑要用的数据。
- 第 502 行：给 `starting_stacks` 赋值，准备后面逻辑要用的数据。
- 第 503-506 行：给 `seat_to_player` 赋值，准备后面逻辑要用的数据。
- 第 507-515 行：给 `request` 赋值，准备后面逻辑要用的数据。
- 第 516-517 行：根据条件 `self.adapter is None` 分支处理不同情况。
- 第 518 行：给 `adapter_hand_ref` 赋值，准备后面逻辑要用的数据。
- 第 520-526 行：给 `context` 赋值，准备后面逻辑要用的数据。
- 第 527 行：给 `state.button_seat_index` 赋值，准备后面逻辑要用的数据。
- 第 528 行：给 `state.current_hand_id` 赋值，准备后面逻辑要用的数据。
- 第 529 行：给 `state.hand_context` 赋值，准备后面逻辑要用的数据。
- 后面还有 3 个语句块，主要继续完成这个函数的收尾、返回或异常处理。

### `apply_hand_settlement`（第 535-582 行）

签名：

```python
def apply_hand_settlement(self, settlement: HandSettlement | Mapping[str, object] | object, table_id: str | None = None) -> TableSnapshot
```

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 540 行：给 `state` 赋值，准备后面逻辑要用的数据。
- 第 541 行：给 `context` 赋值，准备后面逻辑要用的数据。
- 第 542-543 行：根据条件 `context is None or state.current_hand_id is None` 分支处理不同情况。
- 第 545 行：给 `parsed` 赋值，准备后面逻辑要用的数据。
- 第 546-553 行：根据条件 `parsed.hand_id != context.hand_id` 分支处理不同情况。
- 第 555 行：给 `expected_seats` 赋值，准备后面逻辑要用的数据。
- 第 556 行：给 `actual_seats` 赋值，准备后面逻辑要用的数据。
- 第 557-564 行：根据条件 `actual_seats != expected_seats` 分支处理不同情况。
- 第 566-569 行：给 `final_stacks` 赋值，准备后面逻辑要用的数据。
- 第 571-574 行：循环遍历 `final_stacks.items()`，逐个处理里面的元素。
- 第 576 行：给 `state.current_hand_id` 赋值，准备后面逻辑要用的数据。
- 第 577 行：给 `state.hand_context` 赋值，准备后面逻辑要用的数据。
- 第 578-581 行：给 `state.button_seat_index` 赋值，准备后面逻辑要用的数据。
- 第 582 行：返回计算结果，把这个函数的最终答案交给调用者。

### `get_table_snapshot`（第 584-595 行）

签名：

```python
def get_table_snapshot(self, table_id: str | None = None) -> TableSnapshot
```

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 585 行：给 `state` 赋值，准备后面逻辑要用的数据。
- 第 586 行：给 `current_hand` 赋值，准备后面逻辑要用的数据。
- 第 587-595 行：返回计算结果，把这个函数的最终答案交给调用者。

### `get_table`（第 597-598 行）

签名：

```python
def get_table(self, table_id: str | None = None) -> TableSnapshot
```

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 598 行：返回计算结果，把这个函数的最终答案交给调用者。

### `_seat`（第 600-603 行）

签名：

```python
def _seat(self, seat_index: int) -> SeatState
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 601 行：给 `state` 赋值，准备后面逻辑要用的数据。
- 第 602 行：给 `validated_index` 赋值，准备后面逻辑要用的数据。
- 第 603 行：返回计算结果，把这个函数的最终答案交给调用者。

### `_find_player_seat`（第 605-610 行）

签名：

```python
def _find_player_seat(self, player_id: str) -> SeatState | None
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 606 行：给 `state` 赋值，准备后面逻辑要用的数据。
- 第 607-609 行：循环遍历 `state.seats`，逐个处理里面的元素。
- 第 610 行：返回计算结果，把这个函数的最终答案交给调用者。

### `_eligible_seat_indexes`（第 612-616 行）

签名：

```python
def _eligible_seat_indexes(self) -> list[int]
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 613 行：给 `state` 赋值，准备后面逻辑要用的数据。
- 第 614-616 行：返回计算结果，把这个函数的最终答案交给调用者。

### `_new_hand_id`（第 618-619 行）

签名：

```python
def _new_hand_id(self) -> str
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 619 行：返回计算结果，把这个函数的最终答案交给调用者。

### `_require_state`（第 621-629 行）

签名：

```python
def _require_state(self, table_id: str | None = None) -> TableState
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 622-623 行：根据条件 `self._state is None` 分支处理不同情况。
- 第 624-628 行：根据条件 `table_id is not None and table_id != self._state.table_id` 分支处理不同情况。
- 第 629 行：返回计算结果，把这个函数的最终答案交给调用者。

## 类 `_ParsedSeatPlayer`（第 633-637 行）

装饰器：`@dataclass(frozen=True, slots=True)`。

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

字段/类变量：

- `player_id`：类型 `str`。
- `player_name`：类型 `str`。
- `controller_type`：类型 `ControllerType`。
- `starting_stack`：类型 `int`。

## 模块级函数

### `_parse_seat_player_arguments`（第 640-702 行）

签名：

```python
def _parse_seat_player_arguments(args: tuple[object, ...], *, player_id: str | None, player_name: str | None, controller_type: ControllerType | str, starting_stack: int | None, stack: int | None, default_stack: int) -> _ParsedSeatPlayer
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 650 行：声明字段或变量 `positional_player_id`，类型是 `object | None`。
- 第 651 行：声明字段或变量 `positional_player_name`，类型是 `object | None`。
- 第 652 行：声明字段或变量 `positional_controller_type`，类型是 `object | None`。
- 第 653 行：声明字段或变量 `positional_stack`，类型是 `object | None`。
- 第 655-679 行：根据条件 `len(args) == 1` 分支处理不同情况。
- 第 681-684 行：给 `resolved_player_name` 赋值，准备后面逻辑要用的数据。
- 第 685-688 行：给 `resolved_player_id` 赋值，准备后面逻辑要用的数据。
- 第 689-690 行：根据条件 `resolved_player_id is None` 分支处理不同情况。
- 第 692-694 行：给 `controller_value` 赋值，准备后面逻辑要用的数据。
- 第 695 行：给 `resolved_controller` 赋值，准备后面逻辑要用的数据。
- 第 696 行：给 `stack_value` 赋值，准备后面逻辑要用的数据。
- 第 697-702 行：返回计算结果，把这个函数的最终答案交给调用者。

### `_resolve_argument`（第 705-714 行）

签名：

```python
def _resolve_argument(name: str, keyword_value: object | None, positional_value: object | None) -> object
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 708-709 行：根据条件 `positional_value is None` 分支处理不同情况。
- 第 710-711 行：根据条件 `keyword_value is None` 分支处理不同情况。
- 第 712-713 行：根据条件 `keyword_value == positional_value` 分支处理不同情况。
- 第 714 行：主动抛出错误，表示传入数据或当前状态不符合要求。

### `_resolve_stack_argument`（第 717-729 行）

签名：

```python
def _resolve_stack_argument(starting_stack: object | None, stack: object | None, positional_stack: object | None, default_stack: int) -> object
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 723 行：给 `values` 赋值，准备后面逻辑要用的数据。
- 第 724-725 行：根据条件 `not values` 分支处理不同情况。
- 第 726 行：给 `first` 赋值，准备后面逻辑要用的数据。
- 第 727-728 行：根据条件 `any((value != first for value in values[1:]))` 分支处理不同情况。
- 第 729 行：返回计算结果，把这个函数的最终答案交给调用者。

### `_looks_like_controller_type`（第 732-738 行）

签名：

```python
def _looks_like_controller_type(value: object) -> bool
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 733-734 行：根据条件 `isinstance(value, ControllerType)` 分支处理不同情况。
- 第 735-736 行：根据条件 `not isinstance(value, str)` 分支处理不同情况。
- 第 737 行：给 `normalized` 赋值，准备后面逻辑要用的数据。
- 第 738 行：返回计算结果，把这个函数的最终答案交给调用者。

### `_normalize_controller_type`（第 741-750 行）

签名：

```python
def _normalize_controller_type(value: object) -> ControllerType
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 742-743 行：根据条件 `isinstance(value, ControllerType)` 分支处理不同情况。
- 第 744-745 行：根据条件 `not isinstance(value, str)` 分支处理不同情况。
- 第 746 行：给 `normalized` 赋值，准备后面逻辑要用的数据。
- 第 747-750 行：尝试执行可能失败的操作，并在异常发生时转成项目自己的处理方式。

### `_coerce_settlement`（第 753-774 行）

签名：

```python
def _coerce_settlement(settlement: HandSettlement | Mapping[str, object] | object) -> HandSettlement
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 756-757 行：根据条件 `isinstance(settlement, HandSettlement)` 分支处理不同情况。
- 第 758-759 行：根据条件 `isinstance(settlement, Mapping)` 分支处理不同情况。
- 第 760 行：声明字段或变量 `attrs`，类型是 `dict[str, object]`。
- 第 761-771 行：循环遍历 `('hand_id', 'final_stacks', 'payoffs', 'winners', 'final_board', 'showdown_summary', 'operations_summary')`，逐个处理里面的元素。
- 第 772-773 行：根据条件 `not attrs` 分支处理不同情况。
- 第 774 行：返回计算结果，把这个函数的最终答案交给调用者。

### `_normalize_stack_mapping`（第 777-781 行）

签名：

```python
def _normalize_stack_mapping(value: object, name: str) -> dict[int, int]
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 778 行：给 `normalized` 赋值，准备后面逻辑要用的数据。
- 第 779-780 行：循环遍历 `normalized.items()`，逐个处理里面的元素。
- 第 781 行：返回计算结果，把这个函数的最终答案交给调用者。

### `_normalize_int_mapping`（第 784-793 行）

签名：

```python
def _normalize_int_mapping(value: object, name: str) -> dict[int, int]
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 785-786 行：根据条件 `not isinstance(value, Mapping)` 分支处理不同情况。
- 第 787 行：声明字段或变量 `normalized`，类型是 `dict[int, int]`。
- 第 788-792 行：循环遍历 `value.items()`，逐个处理里面的元素。
- 第 793 行：返回计算结果，把这个函数的最终答案交给调用者。

### `_normalize_mapping_sequence`（第 796-806 行）

签名：

```python
def _normalize_mapping_sequence(value: object, name: str) -> tuple[Mapping[str, object], ...]
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 797-798 行：根据条件 `value is None` 分支处理不同情况。
- 第 799-800 行：根据条件 `isinstance(value, Mapping | str | bytes) or not isinstance(value, Sequence)` 分支处理不同情况。
- 第 801 行：声明字段或变量 `items`，类型是 `list[Mapping[str, object]]`。
- 第 802-805 行：循环遍历 `value`，逐个处理里面的元素。
- 第 806 行：返回计算结果，把这个函数的最终答案交给调用者。

### `_normalize_string_sequence`（第 809-817 行）

签名：

```python
def _normalize_string_sequence(value: object, name: str) -> tuple[str, ...]
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 810-811 行：根据条件 `value is None` 分支处理不同情况。
- 第 812-813 行：根据条件 `isinstance(value, str | bytes) or not isinstance(value, Sequence)` 分支处理不同情况。
- 第 814 行：声明字段或变量 `items`，类型是 `list[str]`。
- 第 815-816 行：循环遍历 `value`，逐个处理里面的元素。
- 第 817 行：返回计算结果，把这个函数的最终答案交给调用者。

### `_optional_mapping`（第 820-825 行）

签名：

```python
def _optional_mapping(value: object, name: str) -> Mapping[str, object] | None
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 821-822 行：根据条件 `value is None` 分支处理不同情况。
- 第 823-824 行：根据条件 `not isinstance(value, Mapping)` 分支处理不同情况。
- 第 825 行：返回计算结果，把这个函数的最终答案交给调用者。

### `_derive_player_id`（第 828-829 行）

签名：

```python
def _derive_player_id(player_name: str) -> str
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 829 行：返回计算结果，把这个函数的最终答案交给调用者。

### `_known_player_id`（第 832-835 行）

签名：

```python
def _known_player_id(player_id: str | None) -> str
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 833-834 行：根据条件 `player_id is None` 分支处理不同情况。
- 第 835 行：返回计算结果，把这个函数的最终答案交给调用者。

### `_button_for_new_hand`（第 838-841 行）

签名：

```python
def _button_for_new_hand(current_button: int, active_seat_indexes: Sequence[int]) -> int
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 839-840 行：根据条件 `current_button in active_seat_indexes` 分支处理不同情况。
- 第 841 行：返回计算结果，把这个函数的最终答案交给调用者。

### `_next_button_after_settlement`（第 844-852 行）

签名：

```python
def _next_button_after_settlement(current_button: int, eligible_seat_indexes: Sequence[int]) -> int
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 845-846 行：根据条件 `not eligible_seat_indexes` 分支处理不同情况。
- 第 847 行：给 `eligible` 赋值，准备后面逻辑要用的数据。
- 第 848-851 行：循环遍历 `range(1, SEAT_COUNT + 1)`，逐个处理里面的元素。
- 第 852 行：返回计算结果，把这个函数的最终答案交给调用者。

### `_validate_seat_index`（第 855-863 行）

签名：

```python
def _validate_seat_index(value: object) -> int
```

人话：校验输入或状态是否合法，发现问题时返回错误或抛出异常。

关键代码块：

- 第 856-857 行：根据条件 `not isinstance(value, int) or isinstance(value, bool)` 分支处理不同情况。
- 第 858-862 行：根据条件 `value < 0 or value >= SEAT_COUNT` 分支处理不同情况。
- 第 863 行：返回计算结果，把这个函数的最终答案交给调用者。

### `_coerce_seat_index_key`（第 866-872 行）

签名：

```python
def _coerce_seat_index_key(value: object, name: str) -> int
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 867-871 行：根据条件 `isinstance(value, str)` 分支处理不同情况。
- 第 872 行：返回计算结果，把这个函数的最终答案交给调用者。

### `_validate_positive_int`（第 875-880 行）

签名：

```python
def _validate_positive_int(value: object, name: str) -> int
```

人话：校验输入或状态是否合法，发现问题时返回错误或抛出异常。

关键代码块：

- 第 876-877 行：根据条件 `not isinstance(value, int) or isinstance(value, bool)` 分支处理不同情况。
- 第 878-879 行：根据条件 `value <= 0` 分支处理不同情况。
- 第 880 行：返回计算结果，把这个函数的最终答案交给调用者。

### `_validate_non_negative_int`（第 883-888 行）

签名：

```python
def _validate_non_negative_int(value: object, name: str) -> int
```

人话：校验输入或状态是否合法，发现问题时返回错误或抛出异常。

关键代码块：

- 第 884-885 行：根据条件 `not isinstance(value, int) or isinstance(value, bool)` 分支处理不同情况。
- 第 886-887 行：根据条件 `value < 0` 分支处理不同情况。
- 第 888 行：返回计算结果，把这个函数的最终答案交给调用者。

### `_required_string`（第 891-897 行）

签名：

```python
def _required_string(value: object, name: str) -> str
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 892-893 行：根据条件 `not isinstance(value, str)` 分支处理不同情况。
- 第 894 行：给 `stripped` 赋值，准备后面逻辑要用的数据。
- 第 895-896 行：根据条件 `not stripped` 分支处理不同情况。
- 第 897 行：返回计算结果，把这个函数的最终答案交给调用者。

### `_optional_string`（第 900-903 行）

签名：

```python
def _optional_string(value: object, name: str) -> str | None
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 901-902 行：根据条件 `value is None` 分支处理不同情况。
- 第 903 行：返回计算结果，把这个函数的最终答案交给调用者。

## 对外公开接口

`__all__` 声明这个模块希望别人主要使用这些名字：

- `AdapterUnavailableError`
- `ControllerType`
- `CreateHandRequest`
- `DEFAULT_ANTE`
- `DEFAULT_BIG_BLIND`
- `DEFAULT_MIN_ACTIVE_PLAYERS`
- `DEFAULT_SMALL_BLIND`
- `DEFAULT_STARTING_STACK`
- `HandAdapter`
- `HandContext`
- `HandSettlement`
- `HandSettlementMismatchError`
- `HandSnapshot`
- `InvalidStackError`
- `NoCurrentHandError`
- `PlayerAlreadySeatedError`
- `SEAT_COUNT`
- `SeatNotFoundError`
- `SeatOccupiedError`
- `SeatSnapshot`
- `SeatState`
- `SeatStatus`
- `TableManager`
- `TableManagerError`
- `TableNotInitializedError`
- `TableSnapshot`
- `TableState`
- `TableStateConflictError`
- `TableStatus`

## 初学者阅读建议

先看“这个文件是干什么的”，再看类和函数标题。遇到以下划线开头的函数，可以先理解成内部工具；遇到 `to_dict/from_dict/to_json/from_json`，重点记住它们是在对象、字典和 JSON 之间转换。
