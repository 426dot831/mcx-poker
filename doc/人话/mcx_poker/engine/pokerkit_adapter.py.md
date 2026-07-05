# `mcx_poker/engine/pokerkit_adapter.py` 人话讲解

源文件：`/Users/machengqi/Documents/mcx-poker/src/mcx_poker/engine/pokerkit_adapter.py`

## 这个文件是干什么的

源码说明：PokerKit adapter boundary for mcx-poker.

人话概括：

属于牌局引擎层，负责动作、校验、游戏循环或 PokerKit 适配。

## 导入区

- 第 3 行：从 `__future__` 导入 `annotations`。
- 第 5 行：导入 `warnings`。
- 第 6 行：从 `collections.abc` 导入 `Mapping, Sequence`。
- 第 7 行：从 `dataclasses` 导入 `dataclass, fields, is_dataclass`。
- 第 8 行：从 `enum` 导入 `StrEnum`。
- 第 9 行：从 `typing` 导入 `Any, NoReturn, cast`。
- 第 11 行：从 `pokerkit` 导入 `Automation, Card, Mode, NoLimitTexasHoldem, State`。

人话：导入区是在声明“这个文件需要哪些外部工具”。标准库通常提供基础能力，项目内导入则说明它依赖哪些业务模块。

## 类 `ActionType`（第 14-34 行）

继承：`StrEnum`。

源码说明：Platform-level poker action types.

人话：把一组相关数据和行为封装到一个类型里，供其他模块按统一接口使用。

字段/类变量：

- `FOLD`：类级变量，值 `'Fold'`。
- `CHECK`：类级变量，值 `'Check'`。
- `CALL`：类级变量，值 `'Call'`。
- `RAISE_TO`：类级变量，值 `'RaiseTo'`。
- `ALL_IN`：类级变量，值 `'AllIn'`。

这个类里的方法：

### `normalize`（第 24-34 行）

签名：

```python
def normalize(cls, value: ActionType | str) -> ActionType
```

装饰器：`@classmethod`。

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 25-26 行：根据条件 `isinstance(value, cls)` 分支处理不同情况。
- 第 28-34 行：尝试执行可能失败的操作，并在异常发生时转成项目自己的处理方式。

## 类 `CreateHandRequest`（第 38-47 行）

装饰器：`@dataclass(frozen=True)`。

源码说明：Input required to create a PokerKit-backed cash-game hand.

人话：创建并返回一个新对象，通常会把多个输入整理到统一格式。

字段/类变量：

- `hand_id`：类型 `str`。
- `seat_to_player`：类型 `Mapping[int, str]`。
- `starting_stacks`：类型 `Mapping[int, int] | Sequence[int]`。
- `button_seat_index`：类型 `int`。
- `small_blind`：类型 `int`。
- `big_blind`：类型 `int`。
- `ante`：类型 `int`，默认值 `0`。

## 类 `PlayerAction`（第 51-60 行）

装饰器：`@dataclass(frozen=True)`。

源码说明：Platform action submitted to the adapter.

人话：把一组相关数据和行为封装到一个类型里，供其他模块按统一接口使用。

字段/类变量：

- `player_id`：类型 `str`。
- `seat_index`：类型 `int`。
- `hand_id`：类型 `str`。
- `turn_id`：类型 `str | None`。
- `action_type`：类型 `ActionType | str`。
- `amount`：类型 `int | None`，默认值 `None`。
- `source`：类型 `str | None`，默认值 `None`。

## 类 `ActorRef`（第 64-66 行）

装饰器：`@dataclass(frozen=True)`。

人话：把一组相关数据和行为封装到一个类型里，供其他模块按统一接口使用。

字段/类变量：

- `seat_index`：类型 `int`。
- `player_id`：类型 `str`。

## 类 `PokerKitIndexMapping`（第 70-74 行）

装饰器：`@dataclass(frozen=True)`。

人话：把一组相关数据和行为封装到一个类型里，供其他模块按统一接口使用。

字段/类变量：

- `seat_to_pokerkit_index`：类型 `Mapping[int, int]`。
- `pokerkit_index_to_seat`：类型 `Mapping[int, int]`。
- `player_to_pokerkit_index`：类型 `Mapping[str, int]`。
- `pokerkit_index_to_player`：类型 `Mapping[int, str]`。

## 类 `LegalActionBoundary`（第 78-84 行）

装饰器：`@dataclass(frozen=True)`。

人话：把一组相关数据和行为封装到一个类型里，供其他模块按统一接口使用。

字段/类变量：

- `action_type`：类型 `ActionType`。
- `enabled`：类型 `bool`。
- `amount_min`：类型 `int | None`，默认值 `None`。
- `amount_max`：类型 `int | None`，默认值 `None`。
- `amount_fixed`：类型 `int | None`，默认值 `None`。
- `reason_if_disabled`：类型 `str | None`，默认值 `None`。

## 类 `LegalActionBoundaries`（第 88-96 行）

装饰器：`@dataclass(frozen=True)`。

人话：把一组相关数据和行为封装到一个类型里，供其他模块按统一接口使用。

字段/类变量：

- `fold`：类型 `LegalActionBoundary`。
- `check`：类型 `LegalActionBoundary`。
- `call`：类型 `LegalActionBoundary`。
- `raise_to`：类型 `LegalActionBoundary`。
- `all_in`：类型 `LegalActionBoundary`。
- `call_amount`：类型 `int | None`。
- `min_raise_to`：类型 `int | None`。
- `max_raise_to`：类型 `int | None`。

## 类 `PotInfo`（第 100-105 行）

装饰器：`@dataclass(frozen=True)`。

人话：把一组相关数据和行为封装到一个类型里，供其他模块按统一接口使用。

字段/类变量：

- `index`：类型 `int`。
- `amount`：类型 `int`。
- `raked_amount`：类型 `int`。
- `unraked_amount`：类型 `int`。
- `eligible_seats`：类型 `tuple[int, ...]`。

## 类 `PotSummary`（第 109-111 行）

装饰器：`@dataclass(frozen=True)`。

人话：把一组相关数据和行为封装到一个类型里，供其他模块按统一接口使用。

字段/类变量：

- `total_amount`：类型 `int`。
- `pots`：类型 `tuple[PotInfo, ...]`。

## 类 `OperationSummary`（第 115-117 行）

装饰器：`@dataclass(frozen=True)`。

人话：把一组相关数据和行为封装到一个类型里，供其他模块按统一接口使用。

字段/类变量：

- `operation_type`：类型 `str`。
- `details`：类型 `Mapping[str, Any]`。

## 类 `PokerKitStateSummary`（第 121-132 行）

装饰器：`@dataclass(frozen=True)`。

人话：把一组相关数据和行为封装到一个类型里，供其他模块按统一接口使用。

字段/类变量：

- `hand_id`：类型 `str`。
- `is_active`：类型 `bool`。
- `current_actor`：类型 `ActorRef | None`。
- `board_cards`：类型 `tuple[str, ...]`。
- `stacks`：类型 `Mapping[int, int]`。
- `bets`：类型 `Mapping[int, int]`。
- `pot_summary`：类型 `PotSummary`。
- `hole_cards_by_seat`：类型 `Mapping[int, tuple[str, ...]]`。
- `shown_cards_by_seat`：类型 `Mapping[int, tuple[str, ...]]`。
- `legal_action_boundaries`：类型 `LegalActionBoundaries`。
- `operations_summary`：类型 `tuple[OperationSummary, ...]`。

## 类 `WinnerSummary`（第 136-141 行）

装饰器：`@dataclass(frozen=True)`。

人话：把一组相关数据和行为封装到一个类型里，供其他模块按统一接口使用。

字段/类变量：

- `seat_index`：类型 `int`。
- `player_id`：类型 `str`。
- `payoff`：类型 `int`。
- `amount_pulled`：类型 `int`。
- `shown_cards`：类型 `tuple[str, ...]`。

## 类 `ShowdownEntry`（第 145-148 行）

装饰器：`@dataclass(frozen=True)`。

人话：把一组相关数据和行为封装到一个类型里，供其他模块按统一接口使用。

字段/类变量：

- `seat_index`：类型 `int`。
- `player_id`：类型 `str`。
- `shown_cards`：类型 `tuple[str, ...]`。

## 类 `HandSettlement`（第 152-159 行）

装饰器：`@dataclass(frozen=True)`。

人话：把一组相关数据和行为封装到一个类型里，供其他模块按统一接口使用。

字段/类变量：

- `hand_id`：类型 `str`。
- `final_stacks`：类型 `Mapping[int, int]`。
- `payoffs`：类型 `Mapping[int, int]`。
- `winners`：类型 `tuple[WinnerSummary, ...]`。
- `final_board`：类型 `tuple[str, ...]`。
- `showdown_summary`：类型 `tuple[ShowdownEntry, ...]`。
- `operations_summary`：类型 `tuple[OperationSummary, ...]`。

## 类 `ActionSubmissionResult`（第 163-168 行）

装饰器：`@dataclass(frozen=True)`。

人话：把一组相关数据和行为封装到一个类型里，供其他模块按统一接口使用。

字段/类变量：

- `hand_id`：类型 `str`。
- `action`：类型 `PlayerAction`。
- `operation`：类型 `OperationSummary`。
- `state_summary`：类型 `PokerKitStateSummary`。
- `settlement`：类型 `HandSettlement | None`。

## 类 `PokerKitAdapterError`（第 171-207 行）

继承：`Exception`。

源码说明：Platform error raised by the PokerKit adapter.

人话：把一组相关数据和行为封装到一个类型里，供其他模块按统一接口使用。

字段/类变量：

- `code`：类型 `str`。
- `message`：类型 `str`。
- `player_id`：类型 `str | None`。
- `hand_id`：类型 `str | None`。
- `turn_id`：类型 `str | None`。
- `retry_same_player`：类型 `bool`。

这个类里的方法：

### `__init__`（第 181-197 行）

签名：

```python
def __init__(self, *, code: str, message: str, player_id: str | None = None, hand_id: str | None = None, turn_id: str | None = None, retry_same_player: bool = True) -> None
```

人话：初始化对象，接收外部传入的数据并准备对象内部状态。

关键代码块：

- 第 191 行：调用 `super().__init__`，执行一个有副作用或校验性质的动作。
- 第 192 行：给 `self.code` 赋值，准备后面逻辑要用的数据。
- 第 193 行：给 `self.message` 赋值，准备后面逻辑要用的数据。
- 第 194 行：给 `self.player_id` 赋值，准备后面逻辑要用的数据。
- 第 195 行：给 `self.hand_id` 赋值，准备后面逻辑要用的数据。
- 第 196 行：给 `self.turn_id` 赋值，准备后面逻辑要用的数据。
- 第 197 行：给 `self.retry_same_player` 赋值，准备后面逻辑要用的数据。

### `to_dict`（第 199-207 行）

签名：

```python
def to_dict(self) -> dict[str, object | None]
```

人话：把对象转成普通字典，方便 API、日志、测试或 JSON 序列化使用。

关键代码块：

- 第 200-207 行：返回计算结果，把这个函数的最终答案交给调用者。

## 类 `_HandRecord`（第 211-214 行）

装饰器：`@dataclass(frozen=True)`。

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

字段/类变量：

- `hand_id`：类型 `str`。
- `state`：类型 `State`。
- `mapping`：类型 `PokerKitIndexMapping`。

## 类 `_AllInPlan`（第 218-220 行）

装饰器：`@dataclass(frozen=True)`。

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

字段/类变量：

- `method`：类型 `str`。
- `amount`：类型 `int | None`。

## 类 `PokerKitAdapter`（第 223-907 行）

源码说明：Owns all direct PokerKit interactions.

人话：把一组相关数据和行为封装到一个类型里，供其他模块按统一接口使用。

这个类里的方法：

### `__init__`（第 239-240 行）

签名：

```python
def __init__(self) -> None
```

人话：初始化对象，接收外部传入的数据并准备对象内部状态。

关键代码块：

- 第 240 行：声明字段或变量 `self._hands`，类型是 `dict[str, _HandRecord]`。

### `create_hand`（第 242-271 行）

签名：

```python
def create_hand(self, request: CreateHandRequest) -> PokerKitStateSummary
```

人话：创建并返回一个新对象，通常会把多个输入整理到统一格式。

关键代码块：

- 第 243 行：调用 `self._validate_create_request`，执行一个有副作用或校验性质的动作。
- 第 245-248 行：给 `active_seats` 赋值，准备后面逻辑要用的数据。
- 第 249 行：给 `mapping` 赋值，准备后面逻辑要用的数据。
- 第 250 行：给 `starting_stacks` 赋值，准备后面逻辑要用的数据。
- 第 252-268 行：尝试执行可能失败的操作，并在异常发生时转成项目自己的处理方式。
- 第 270 行：给 `self._hands[request.hand_id]` 赋值，准备后面逻辑要用的数据。
- 第 271 行：返回计算结果，把这个函数的最终答案交给调用者。

### `get_hand_mapping`（第 273-281 行）

签名：

```python
def get_hand_mapping(self, hand_id: str) -> PokerKitIndexMapping
```

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 274 行：给 `record` 赋值，准备后面逻辑要用的数据。
- 第 275 行：给 `mapping` 赋值，准备后面逻辑要用的数据。
- 第 276-281 行：返回计算结果，把这个函数的最终答案交给调用者。

### `get_state_summary`（第 283-303 行）

签名：

```python
def get_state_summary(self, hand_id: str) -> PokerKitStateSummary
```

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 284 行：给 `record` 赋值，准备后面逻辑要用的数据。
- 第 285 行：给 `state` 赋值，准备后面逻辑要用的数据。
- 第 286 行：给 `mapping` 赋值，准备后面逻辑要用的数据。
- 第 287 行：给 `current_actor` 赋值，准备后面逻辑要用的数据。
- 第 289-303 行：返回计算结果，把这个函数的最终答案交给调用者。

### `legal_action_boundaries`（第 305-306 行）

签名：

```python
def legal_action_boundaries(self, hand_id: str) -> LegalActionBoundaries
```

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 306 行：返回计算结果，把这个函数的最终答案交给调用者。

### `submit_action`（第 308-339 行）

签名：

```python
def submit_action(self, action: PlayerAction) -> ActionSubmissionResult
```

人话：提交动作或请求，把外部输入交给下一层处理。

关键代码块：

- 第 309 行：给 `normalized_type` 赋值，准备后面逻辑要用的数据。
- 第 310 行：调用 `self._validate_action_shape`，执行一个有副作用或校验性质的动作。
- 第 312 行：给 `record` 赋值，准备后面逻辑要用的数据。
- 第 313 行：给 `state` 赋值，准备后面逻辑要用的数据。
- 第 315-320 行：根据条件 `not state.status` 分支处理不同情况。
- 第 322 行：调用 `self._validate_actor`，执行一个有副作用或校验性质的动作。
- 第 324-327 行：尝试执行可能失败的操作，并在异常发生时转成项目自己的处理方式。
- 第 329 行：给 `operation_summary` 赋值，准备后面逻辑要用的数据。
- 第 330 行：给 `state_summary` 赋值，准备后面逻辑要用的数据。
- 第 331 行：给 `settlement` 赋值，准备后面逻辑要用的数据。
- 第 333-339 行：返回计算结果，把这个函数的最终答案交给调用者。

### `get_hand_settlement`（第 341-364 行）

签名：

```python
def get_hand_settlement(self, hand_id: str) -> HandSettlement
```

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 342 行：给 `record` 赋值，准备后面逻辑要用的数据。
- 第 343 行：给 `state` 赋值，准备后面逻辑要用的数据。
- 第 345-350 行：根据条件 `state.status` 分支处理不同情况。
- 第 352 行：给 `mapping` 赋值，准备后面逻辑要用的数据。
- 第 353-355 行：给 `operations_summary` 赋值，准备后面逻辑要用的数据。
- 第 356-364 行：返回计算结果，把这个函数的最终答案交给调用者。

### `_validate_create_request`（第 366-396 行）

签名：

```python
def _validate_create_request(self, request: CreateHandRequest) -> None
```

人话：校验输入或状态是否合法，发现问题时返回错误或抛出异常。

关键代码块：

- 第 367-372 行：根据条件 `request.hand_id in self._hands` 分支处理不同情况。
- 第 373-378 行：根据条件 `len(request.seat_to_player) < 2` 分支处理不同情况。
- 第 379-384 行：根据条件 `len(set(request.seat_to_player.values())) != len(request.seat_to_player)` 分支处理不同情况。
- 第 385-390 行：根据条件 `request.button_seat_index not in request.seat_to_player` 分支处理不同情况。
- 第 391-396 行：根据条件 `request.small_blind <= 0 or request.big_blind <= 0 or request.ante < 0` 分支处理不同情况。

### `_submit_to_pokerkit`（第 398-453 行）

签名：

```python
def _submit_to_pokerkit(self, action: PlayerAction, action_type: ActionType, record: _HandRecord) -> Any
```

人话：提交动作或请求，把外部输入交给下一层处理。

关键代码块：

- 第 404 行：给 `state` 赋值，准备后面逻辑要用的数据。
- 第 406-453 行：用 `match` 按 `action_type` 的不同形状分别处理。

### `_validate_action_shape`（第 455-476 行）

签名：

```python
def _validate_action_shape(self, action: PlayerAction, action_type: ActionType) -> None
```

人话：校验输入或状态是否合法，发现问题时返回错误或抛出异常。

关键代码块：

- 第 456-469 行：根据条件 `action_type == ActionType.RAISE_TO` 分支处理不同情况。
- 第 471-476 行：根据条件 `action.amount is not None` 分支处理不同情况。

### `_validate_actor`（第 478-506 行）

签名：

```python
def _validate_actor(self, action: PlayerAction, record: _HandRecord) -> None
```

人话：校验输入或状态是否合法，发现问题时返回错误或抛出异常。

关键代码块：

- 第 479 行：给 `mapping` 赋值，准备后面逻辑要用的数据。
- 第 480 行：给 `pokerkit_index` 赋值，准备后面逻辑要用的数据。
- 第 481-486 行：根据条件 `pokerkit_index is None` 分支处理不同情况。
- 第 487-492 行：根据条件 `mapping.pokerkit_index_to_player[pokerkit_index] != action.player_id` 分支处理不同情况。
- 第 494 行：给 `turn_index` 赋值，准备后面逻辑要用的数据。
- 第 495-500 行：根据条件 `turn_index is None` 分支处理不同情况。
- 第 501-506 行：根据条件 `turn_index != pokerkit_index` 分支处理不同情况。

### `_legal_action_boundaries`（第 508-579 行）

签名：

```python
def _legal_action_boundaries(self, record: _HandRecord) -> LegalActionBoundaries
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 509 行：给 `state` 赋值，准备后面逻辑要用的数据。
- 第 510 行：给 `disabled_reason` 赋值，准备后面逻辑要用的数据。
- 第 512 行：给 `call_amount` 赋值，准备后面逻辑要用的数据。
- 第 513 行：给 `min_raise_to` 赋值，准备后面逻辑要用的数据。
- 第 514 行：给 `max_raise_to` 赋值，准备后面逻辑要用的数据。
- 第 515 行：给 `can_check_or_call` 赋值，准备后面逻辑要用的数据。
- 第 516-521 行：给 `can_raise_min` 赋值，准备后面逻辑要用的数据。
- 第 523-528 行：给 `fold_enabled` 赋值，准备后面逻辑要用的数据。
- 第 529 行：给 `check_enabled` 赋值，准备后面逻辑要用的数据。
- 第 530-535 行：给 `call_enabled` 赋值，准备后面逻辑要用的数据。
- 第 536 行：给 `raise_enabled` 赋值，准备后面逻辑要用的数据。
- 第 538 行：给 `all_in_plan` 赋值，准备后面逻辑要用的数据。
- 第 539 行：给 `all_in_amount` 赋值，准备后面逻辑要用的数据。
- 第 541-579 行：返回计算结果，把这个函数的最终答案交给调用者。

### `_all_in_plan`（第 581-603 行）

签名：

```python
def _all_in_plan(self, state: State) -> _AllInPlan | None
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 582 行：给 `actor_index` 赋值，准备后面逻辑要用的数据。
- 第 583-584 行：根据条件 `not state.status or actor_index is None` 分支处理不同情况。
- 第 586 行：给 `max_raise_to` 赋值，准备后面逻辑要用的数据。
- 第 587-592 行：根据条件 `max_raise_to is not None and state.can_complete_bet_or_raise_to(max_raise_to) and (max_raise_to == state.stacks[actor_index] + state.bets[actor_index])` 分支处理不同情况。
- 第 594 行：给 `call_amount` 赋值，准备后面逻辑要用的数据。
- 第 595-601 行：根据条件 `call_amount is not None and call_amount > 0 and state.can_check_or_call() and (call_amount == state.stacks[actor_index])` 分支处理不同情况。
- 第 603 行：返回计算结果，把这个函数的最终答案交给调用者。

### `_map_pokerkit_exception`（第 605-627 行）

签名：

```python
def _map_pokerkit_exception(self, action: PlayerAction, record: _HandRecord, exc: ValueError) -> PokerKitAdapterError
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 611-619 行：根据条件 `not record.state.status` 分支处理不同情况。
- 第 621-627 行：返回计算结果，把这个函数的最终答案交给调用者。

### `_raise_action_error`（第 629-642 行）

签名：

```python
def _raise_action_error(self, action: PlayerAction, *, code: str, message: str) -> NoReturn
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 636-642 行：主动抛出错误，表示传入数据或当前状态不符合要求。

### `_get_record`（第 644-652 行）

签名：

```python
def _get_record(self, hand_id: str) -> _HandRecord
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 645-652 行：尝试执行可能失败的操作，并在异常发生时转成项目自己的处理方式。

### `_active_seats_after_button`（第 654-671 行）

签名：

```python
def _active_seats_after_button(self, active_seats: tuple[int, ...], button_seat_index: int) -> tuple[int, ...]
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 659 行：给 `sorted_seats` 赋值，准备后面逻辑要用的数据。
- 第 660 行：给 `button_position` 赋值，准备后面逻辑要用的数据。
- 第 661 行：给 `ordered` 赋值，准备后面逻辑要用的数据。
- 第 665-669 行：根据条件 `ordered[-1] != button_seat_index` 分支处理不同情况。
- 第 671 行：返回计算结果，把这个函数的最终答案交给调用者。

### `_build_mapping`（第 673-699 行）

签名：

```python
def _build_mapping(self, active_seats: tuple[int, ...], seat_to_player: Mapping[int, str]) -> PokerKitIndexMapping
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 678-680 行：给 `seat_to_pokerkit_index` 赋值，准备后面逻辑要用的数据。
- 第 681-684 行：给 `pokerkit_index_to_seat` 赋值，准备后面逻辑要用的数据。
- 第 685-688 行：给 `player_to_pokerkit_index` 赋值，准备后面逻辑要用的数据。
- 第 689-692 行：给 `pokerkit_index_to_player` 赋值，准备后面逻辑要用的数据。
- 第 694-699 行：返回计算结果，把这个函数的最终答案交给调用者。

### `_normalize_starting_stacks`（第 701-732 行）

签名：

```python
def _normalize_starting_stacks(self, starting_stacks: Mapping[int, int] | Sequence[int], active_seats: tuple[int, ...]) -> tuple[int, ...]
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 706-719 行：根据条件 `isinstance(starting_stacks, Mapping)` 分支处理不同情况。
- 第 721-725 行：根据条件 `len(stacks) != len(active_seats)` 分支处理不同情况。
- 第 726-730 行：根据条件 `any((stack <= 0 for stack in stacks))` 分支处理不同情况。
- 第 732 行：返回计算结果，把这个函数的最终答案交给调用者。

### `_actor_ref`（第 734-748 行）

签名：

```python
def _actor_ref(self, record: _HandRecord, pokerkit_index: int | None) -> ActorRef | None
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 735-736 行：根据条件 `pokerkit_index is None` 分支处理不同情况。
- 第 738-746 行：尝试执行可能失败的操作，并在异常发生时转成项目自己的处理方式。
- 第 748 行：返回计算结果，把这个函数的最终答案交给调用者。

### `_seat_amounts`（第 750-758 行）

签名：

```python
def _seat_amounts(self, amounts: Sequence[int], mapping: PokerKitIndexMapping) -> dict[int, int]
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 755-758 行：返回计算结果，把这个函数的最终答案交给调用者。

### `_board_cards`（第 760-764 行）

签名：

```python
def _board_cards(self, state: State) -> tuple[str, ...]
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 761-764 行：尝试执行可能失败的操作，并在异常发生时转成项目自己的处理方式。

### `_pot_summary`（第 766-783 行）

签名：

```python
def _pot_summary(self, state: State, mapping: PokerKitIndexMapping) -> PotSummary
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 767 行：给 `pots` 赋值，准备后面逻辑要用的数据。
- 第 768-783 行：返回计算结果，把这个函数的最终答案交给调用者。

### `_hole_cards_by_seat`（第 785-793 行）

签名：

```python
def _hole_cards_by_seat(self, state: State, mapping: PokerKitIndexMapping) -> dict[int, tuple[str, ...]]
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 790-793 行：返回计算结果，把这个函数的最终答案交给调用者。

### `_shown_cards_by_seat`（第 795-805 行）

签名：

```python
def _shown_cards_by_seat(self, state: State, mapping: PokerKitIndexMapping) -> dict[int, tuple[str, ...]]
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 800-805 行：返回计算结果，把这个函数的最终答案交给调用者。

### `_can_fold_without_warning`（第 807-810 行）

签名：

```python
def _can_fold_without_warning(self, state: State) -> bool
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 808-810 行：在上下文管理器里执行代码，通常用于资源的进入和退出管理。

### `_operation_summary`（第 812-838 行）

签名：

```python
def _operation_summary(self, operation: Any, mapping: PokerKitIndexMapping) -> OperationSummary
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 817 行：声明字段或变量 `details`，类型是 `dict[str, Any]`。
- 第 819-833 行：根据条件 `is_dataclass(operation)` 分支处理不同情况。
- 第 835-838 行：返回计算结果，把这个函数的最终答案交给调用者。

### `_serialize_value`（第 840-852 行）

签名：

```python
def _serialize_value(self, value: Any, mapping: PokerKitIndexMapping) -> Any
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 841-842 行：根据条件 `isinstance(value, Card)` 分支处理不同情况。
- 第 843-844 行：根据条件 `isinstance(value, tuple)` 分支处理不同情况。
- 第 845-846 行：根据条件 `isinstance(value, list)` 分支处理不同情况。
- 第 847-851 行：根据条件 `isinstance(value, dict)` 分支处理不同情况。
- 第 852 行：返回计算结果，把这个函数的最终答案交给调用者。

### `_winners`（第 854-889 行）

签名：

```python
def _winners(self, record: _HandRecord) -> tuple[WinnerSummary, ...]
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 855 行：给 `state` 赋值，准备后面逻辑要用的数据。
- 第 856 行：给 `mapping` 赋值，准备后面逻辑要用的数据。
- 第 857 行：声明字段或变量 `pulled_amounts`，类型是 `dict[int, int]`。
- 第 859-865 行：循环遍历 `state.operations`，逐个处理里面的元素。
- 第 867 行：给 `max_payoff` 赋值，准备后面逻辑要用的数据。
- 第 868-872 行：给 `winner_indices` 赋值，准备后面逻辑要用的数据。
- 第 873-878 行：根据条件 `max_payoff <= 0` 分支处理不同情况。
- 第 880-889 行：返回计算结果，把这个函数的最终答案交给调用者。

### `_showdown_summary`（第 891-907 行）

签名：

```python
def _showdown_summary(self, record: _HandRecord) -> tuple[ShowdownEntry, ...]
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 892 行：声明字段或变量 `entries`，类型是 `list[ShowdownEntry]`。
- 第 894-905 行：循环遍历 `record.state.operations`，逐个处理里面的元素。
- 第 907 行：返回计算结果，把这个函数的最终答案交给调用者。

## 初学者阅读建议

先看“这个文件是干什么的”，再看类和函数标题。遇到以下划线开头的函数，可以先理解成内部工具；遇到 `to_dict/from_dict/to_json/from_json`，重点记住它们是在对象、字典和 JSON 之间转换。
