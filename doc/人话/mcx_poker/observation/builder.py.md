# `mcx_poker/observation/builder.py` 人话讲解

源文件：`/Users/machengqi/Documents/mcx-poker/src/mcx_poker/observation/builder.py`

## 这个文件是干什么的

源码说明：Player-facing observation DTOs and builders.

The builder accepts duck-typed table snapshots, state summaries, and public hand
events.  It intentionally does not import PokerKit or adapter internals.

人话概括：

负责把内部牌局状态整理成玩家能看到的观察信息。

## 导入区

- 第 7 行：从 `__future__` 导入 `annotations`。
- 第 9 行：导入 `json`。
- 第 10 行：从 `collections.abc` 导入 `Iterable, Mapping, Sequence`。
- 第 11 行：从 `dataclasses` 导入 `dataclass, field`。
- 第 12 行：从 `enum` 导入 `Enum`。
- 第 13 行：从 `math` 导入 `isfinite`。
- 第 14 行：从 `typing` 导入 `Any, TypeAlias`。
- 第 16 行：从 `mcx_poker.engine.actions` 导入 `ActionType, LegalAction`。

人话：导入区是在声明“这个文件需要哪些外部工具”。标准库通常提供基础能力，项目内导入则说明它依赖哪些业务模块。

## 顶层常量和类型

- 第 18 行：`Identifier`: `TypeAlias` = `str | int`。人话：声明一个带类型的模块级变量。
- 第 19 行：`JSONValue`: `TypeAlias` = `str | int | float | bool | None | list['JSONValue'] | dict[str, 'JSONValue']`。人话：声明一个带类型的模块级变量。
- 第 21 行：`SEAT_COUNT` = `6`。人话：在模块级别准备一个后面会反复使用的值。
- 第 22 行：`_MISSING` = `object()`。人话：在模块级别准备一个后面会反复使用的值。
- 第 23-38 行：`_ALWAYS_HIDDEN_KEYS` = `frozenset({'adapter_hand_ref', 'controller_private_state', 'deck', 'deck_order', 'future_cards', 'pokerkit_state', 'private_controller_state', 'raw_pokerkit_state', 'raw_state', 'remaining_deck', 'stub', 'undealt_cards'})`。人话：在模块级别准备一个后面会反复使用的值。
- 第 39-49 行：`_PRIVATE_CARD_KEYS` = `frozenset({'all_hole_cards', 'hidden_hole_cards', 'hole_cards_by_player', 'opponent_hole_cards', 'private_cards', 'private_hole_cards', 'unshown_hole_cards'})`。人话：在模块级别准备一个后面会反复使用的值。
- 第 50 行：`_SHOWDOWN_EVENT_TYPES` = `frozenset({'showdown', 'cards_shown', 'hole_cards_shown'})`。人话：在模块级别准备一个后面会反复使用的值。
- 第 408 行：`build_observation` = `build_player_observation`。人话：在模块级别准备一个后面会反复使用的值。

## 类 `VisibleSeat`（第 54-103 行）

装饰器：`@dataclass(frozen=True, slots=True)`。

源码说明：Seat state visible to one observer.

人话：把一组相关数据和行为封装到一个类型里，供其他模块按统一接口使用。

字段/类变量：

- `seat_index`：类型 `int`。
- `player_id`：类型 `Identifier | None`，默认值 `None`。
- `player_name`：类型 `str | None`，默认值 `None`。
- `stack`：类型 `int`，默认值 `0`。
- `current_bet`：类型 `int`，默认值 `0`。
- `status`：类型 `str`，默认值 `'empty'`。
- `hole_card_count`：类型 `int`，默认值 `0`。
- `shown_cards`：类型 `tuple[str, ...]`，默认值 `()`。

这个类里的方法：

### `__post_init__`（第 66-78 行）

签名：

```python
def __post_init__(self) -> None
```

人话：dataclass 创建对象后自动执行，用来做校验、标准化或补充字段。

关键代码块：

- 第 67 行：调用 `object.__setattr__`，执行一个有副作用或校验性质的动作。
- 第 68 行：调用 `object.__setattr__`，执行一个有副作用或校验性质的动作。
- 第 69 行：调用 `object.__setattr__`，执行一个有副作用或校验性质的动作。
- 第 70 行：调用 `object.__setattr__`，执行一个有副作用或校验性质的动作。
- 第 71 行：调用 `object.__setattr__`，执行一个有副作用或校验性质的动作。
- 第 72 行：调用 `object.__setattr__`，执行一个有副作用或校验性质的动作。
- 第 73-77 行：调用 `object.__setattr__`，执行一个有副作用或校验性质的动作。
- 第 78 行：调用 `object.__setattr__`，执行一个有副作用或校验性质的动作。

### `to_dict`（第 80-90 行）

签名：

```python
def to_dict(self) -> dict[str, JSONValue]
```

人话：把对象转成普通字典，方便 API、日志、测试或 JSON 序列化使用。

关键代码块：

- 第 81-90 行：返回计算结果，把这个函数的最终答案交给调用者。

### `from_dict`（第 93-103 行）

签名：

```python
def from_dict(cls, data: Mapping[str, Any]) -> VisibleSeat
```

装饰器：`@classmethod`。

人话：从普通字典恢复成项目里的强类型对象，同时复用构造时的校验逻辑。

关键代码块：

- 第 94-103 行：返回计算结果，把这个函数的最终答案交给调用者。

## 类 `PotSummary`（第 107-142 行）

装饰器：`@dataclass(frozen=True, slots=True)`。

源码说明：Visible pot summary with JSON-safe side-pot details.

人话：把一组相关数据和行为封装到一个类型里，供其他模块按统一接口使用。

字段/类变量：

- `total_amount`：类型 `int`，默认值 `0`。
- `pots`：类型 `tuple[Mapping[str, JSONValue], ...]`，默认值 `()`。

这个类里的方法：

### `__post_init__`（第 113-119 行）

签名：

```python
def __post_init__(self) -> None
```

人话：dataclass 创建对象后自动执行，用来做校验、标准化或补充字段。

关键代码块：

- 第 114 行：调用 `object.__setattr__`，执行一个有副作用或校验性质的动作。
- 第 115-119 行：调用 `object.__setattr__`，执行一个有副作用或校验性质的动作。

### `to_dict`（第 121-125 行）

签名：

```python
def to_dict(self) -> dict[str, JSONValue]
```

人话：把对象转成普通字典，方便 API、日志、测试或 JSON 序列化使用。

关键代码块：

- 第 122-125 行：返回计算结果，把这个函数的最终答案交给调用者。

### `from_any`（第 128-142 行）

签名：

```python
def from_any(cls, value: Any) -> PotSummary
```

装饰器：`@classmethod`。

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 129-130 行：根据条件 `value is None` 分支处理不同情况。
- 第 131-132 行：根据条件 `isinstance(value, PotSummary)` 分支处理不同情况。
- 第 134 行：给 `total` 赋值，准备后面逻辑要用的数据。
- 第 135 行：给 `raw_pots` 赋值，准备后面逻辑要用的数据。
- 第 136 行：声明字段或变量 `pots`，类型是 `list[Mapping[str, JSONValue]]`。
- 第 137-141 行：循环遍历 `enumerate(_as_iterable(raw_pots))`，逐个处理里面的元素。
- 第 142 行：返回计算结果，把这个函数的最终答案交给调用者。

## 类 `BetSummary`（第 146-195 行）

装饰器：`@dataclass(frozen=True, slots=True)`。

源码说明：Visible current-betting summary for the hand state.

人话：把一组相关数据和行为封装到一个类型里，供其他模块按统一接口使用。

字段/类变量：

- `current_bet`：类型 `int`，默认值 `0`。
- `to_call`：类型 `int | None`，默认值 `None`。
- `min_raise_to`：类型 `int | None`，默认值 `None`。
- `max_raise_to`：类型 `int | None`，默认值 `None`。
- `bets_by_seat`：类型 `Mapping[int, int]`，默认值 `field(default_factory=dict)`。

这个类里的方法：

### `__post_init__`（第 155-172 行）

签名：

```python
def __post_init__(self) -> None
```

人话：dataclass 创建对象后自动执行，用来做校验、标准化或补充字段。

关键代码块：

- 第 156 行：调用 `object.__setattr__`，执行一个有副作用或校验性质的动作。
- 第 157 行：调用 `object.__setattr__`，执行一个有副作用或校验性质的动作。
- 第 158-162 行：调用 `object.__setattr__`，执行一个有副作用或校验性质的动作。
- 第 163-167 行：调用 `object.__setattr__`，执行一个有副作用或校验性质的动作。
- 第 168-172 行：调用 `object.__setattr__`，执行一个有副作用或校验性质的动作。

### `to_dict`（第 174-181 行）

签名：

```python
def to_dict(self) -> dict[str, JSONValue]
```

人话：把对象转成普通字典，方便 API、日志、测试或 JSON 序列化使用。

关键代码块：

- 第 175-181 行：返回计算结果，把这个函数的最终答案交给调用者。

### `from_any`（第 184-195 行）

签名：

```python
def from_any(cls, value: Any) -> BetSummary
```

装饰器：`@classmethod`。

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 185-186 行：根据条件 `value is None` 分支处理不同情况。
- 第 187-188 行：根据条件 `isinstance(value, BetSummary)` 分支处理不同情况。
- 第 189-195 行：返回计算结果，把这个函数的最终答案交给调用者。

## 类 `PlayerObservation`（第 199-314 行）

装饰器：`@dataclass(frozen=True, slots=True)`。

源码说明：Per-player observation with hidden information redacted.

人话：把一组相关数据和行为封装到一个类型里，供其他模块按统一接口使用。

字段/类变量：

- `observer_player_id`：类型 `Identifier`。
- `observer_seat_index`：类型 `int`。
- `table_id`：类型 `Identifier`。
- `hand_id`：类型 `Identifier`。
- `turn_id`：类型 `Identifier`。
- `is_actor`：类型 `bool`。
- `button_seat_index`：类型 `int`。
- `own_hole_cards`：类型 `tuple[str, ...]`，默认值 `()`。
- `board_cards`：类型 `tuple[str, ...]`，默认值 `()`。
- `visible_seats`：类型 `tuple[VisibleSeat, ...]`，默认值 `()`。
- `pot_summary`：类型 `PotSummary`，默认值 `field(default_factory=PotSummary)`。
- `bet_summary`：类型 `BetSummary`，默认值 `field(default_factory=BetSummary)`。
- `visible_action_history`：类型 `tuple[Mapping[str, JSONValue], ...]`，默认值 `()`。
- `legal_actions`：类型 `tuple[LegalAction, ...]`，默认值 `()`。

这个类里的方法：

### `__post_init__`（第 217-250 行）

签名：

```python
def __post_init__(self) -> None
```

人话：dataclass 创建对象后自动执行，用来做校验、标准化或补充字段。

关键代码块：

- 第 218 行：调用 `object.__setattr__`，执行一个有副作用或校验性质的动作。
- 第 219-221 行：调用 `object.__setattr__`，执行一个有副作用或校验性质的动作。
- 第 222 行：调用 `object.__setattr__`，执行一个有副作用或校验性质的动作。
- 第 223 行：调用 `object.__setattr__`，执行一个有副作用或校验性质的动作。
- 第 224 行：调用 `object.__setattr__`，执行一个有副作用或校验性质的动作。
- 第 225-226 行：根据条件 `not isinstance(self.is_actor, bool)` 分支处理不同情况。
- 第 227 行：调用 `object.__setattr__`，执行一个有副作用或校验性质的动作。
- 第 228-232 行：调用 `object.__setattr__`，执行一个有副作用或校验性质的动作。
- 第 233 行：调用 `object.__setattr__`，执行一个有副作用或校验性质的动作。
- 第 234-238 行：调用 `object.__setattr__`，执行一个有副作用或校验性质的动作。
- 第 239 行：调用 `object.__setattr__`，执行一个有副作用或校验性质的动作。
- 第 240 行：调用 `object.__setattr__`，执行一个有副作用或校验性质的动作。
- 第 241-245 行：调用 `object.__setattr__`，执行一个有副作用或校验性质的动作。
- 第 246-250 行：调用 `object.__setattr__`，执行一个有副作用或校验性质的动作。

### `to_dict`（第 252-271 行）

签名：

```python
def to_dict(self) -> dict[str, JSONValue]
```

人话：把对象转成普通字典，方便 API、日志、测试或 JSON 序列化使用。

关键代码块：

- 第 253-271 行：返回计算结果，把这个函数的最终答案交给调用者。

### `from_dict`（第 274-290 行）

签名：

```python
def from_dict(cls, data: Mapping[str, Any]) -> PlayerObservation
```

装饰器：`@classmethod`。

人话：从普通字典恢复成项目里的强类型对象，同时复用构造时的校验逻辑。

关键代码块：

- 第 275-290 行：返回计算结果，把这个函数的最终答案交给调用者。

### `to_json`（第 292-293 行）

签名：

```python
def to_json(self) -> str
```

人话：把对象转成 JSON 字符串，方便跨进程或前后端传输。

关键代码块：

- 第 293 行：返回计算结果，把这个函数的最终答案交给调用者。

### `from_json`（第 296-300 行）

签名：

```python
def from_json(cls, payload: str) -> PlayerObservation
```

装饰器：`@classmethod`。

人话：从 JSON 字符串恢复成对象。

关键代码块：

- 第 297 行：给 `loaded` 赋值，准备后面逻辑要用的数据。
- 第 298-299 行：根据条件 `not isinstance(loaded, Mapping)` 分支处理不同情况。
- 第 300 行：返回计算结果，把这个函数的最终答案交给调用者。

### `to_websocket_payload`（第 302-314 行）

签名：

```python
def to_websocket_payload(self) -> dict[str, JSONValue]
```

源码说明：Return a private ``action_requested`` payload shape.

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 305 行：给 `observation` 赋值，准备后面逻辑要用的数据。
- 第 306-314 行：返回计算结果，把这个函数的最终答案交给调用者。

## 模块级函数

### `build_player_observation`（第 317-405 行）

签名：

```python
def build_player_observation(table_snapshot: Any, state_summary: Any, public_events: Iterable[Any] | None = None, *, observer_player_id: Identifier | None = None, observer_seat_index: int | None = None, turn_id: Identifier | None = None) -> PlayerObservation
```

源码说明：Build one player's redacted observation from platform summaries.

人话：根据已有状态组装更高层的数据对象。

关键代码块：

- 第 328 行：给 `events` 赋值，准备后面逻辑要用的数据。
- 第 329 行：给 `seats_by_index` 赋值，准备后面逻辑要用的数据。
- 第 330 行：给 `player_to_seat` 赋值，准备后面逻辑要用的数据。
- 第 332-336 行：给 `observer_seat` 赋值，准备后面逻辑要用的数据。
- 第 337-341 行：给 `observer_player` 赋值，准备后面逻辑要用的数据。
- 第 343 行：给 `actor` 赋值，准备后面逻辑要用的数据。
- 第 344 行：给 `actor_seat` 赋值，准备后面逻辑要用的数据。
- 第 345 行：给 `actor_player` 赋值，准备后面逻辑要用的数据。
- 第 346-348 行：给 `is_actor` 赋值，准备后面逻辑要用的数据。
- 第 350 行：给 `hole_cards_by_seat` 赋值，准备后面逻辑要用的数据。
- 第 351 行：给 `shown_cards` 赋值，准备后面逻辑要用的数据。
- 第 352 行：给 `folded_seats` 赋值，准备后面逻辑要用的数据。
- 第 353 行：给 `bets_by_seat` 赋值，准备后面逻辑要用的数据。
- 第 354 行：给 `stacks_by_seat` 赋值，准备后面逻辑要用的数据。
- 第 356 行：给 `own_hole_cards` 赋值，准备后面逻辑要用的数据。
- 第 357 行：给 `board_cards` 赋值，准备后面逻辑要用的数据。
- 后面还有 5 个语句块，主要继续完成这个函数的收尾、返回或异常处理。

### `_build_visible_seat`（第 411-461 行）

签名：

```python
def _build_visible_seat(*, seat_index: int, raw_seat: Any, observer_seat_index: int, hole_cards_by_seat: Mapping[int, tuple[str, ...]], shown_cards_by_seat: Mapping[int, tuple[str, ...]], folded_seats: set[int], bets_by_seat: Mapping[int, int], stacks_by_seat: Mapping[int, int]) -> VisibleSeat
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 422 行：给 `player_id` 赋值，准备后面逻辑要用的数据。
- 第 423 行：给 `shown_cards` 赋值，准备后面逻辑要用的数据。
- 第 424 行：给 `hidden_cards` 赋值，准备后面逻辑要用的数据。
- 第 425 行：给 `raw_hole_count` 赋值，准备后面逻辑要用的数据。
- 第 426-429 行：根据条件 `raw_hole_count is None and _read(raw_seat, ('has_hole_cards', 'in_hand', 'is_in_hand'), False)` 分支处理不同情况。
- 第 431-438 行：根据条件 `seat_index == observer_seat_index` 分支处理不同情况。
- 第 440-442 行：给 `stack` 赋值，准备后面逻辑要用的数据。
- 第 443 行：给 `current_bet` 赋值，准备后面逻辑要用的数据。
- 第 444-451 行：给 `status` 赋值，准备后面逻辑要用的数据。
- 第 452-461 行：返回计算结果，把这个函数的最终答案交给调用者。

### `_build_bet_summary`（第 464-476 行）

签名：

```python
def _build_bet_summary(state_summary: Any, bets_by_seat: Mapping[int, int]) -> BetSummary
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 465 行：给 `explicit` 赋值，准备后面逻辑要用的数据。
- 第 466-467 行：根据条件 `explicit is not None` 分支处理不同情况。
- 第 469 行：给 `boundaries` 赋值，准备后面逻辑要用的数据。
- 第 470-476 行：返回计算结果，把这个函数的最终答案交给调用者。

### `_legal_actions`（第 479-500 行）

签名：

```python
def _legal_actions(state_summary: Any) -> tuple[LegalAction, ...]
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 480 行：给 `explicit` 赋值，准备后面逻辑要用的数据。
- 第 481-482 行：根据条件 `explicit is not None` 分支处理不同情况。
- 第 484 行：给 `boundaries` 赋值，准备后面逻辑要用的数据。
- 第 485-486 行：根据条件 `boundaries is None` 分支处理不同情况。
- 第 488 行：声明字段或变量 `actions`，类型是 `list[LegalAction]`。
- 第 489-499 行：循环遍历 `(('fold', ActionType.FOLD), ('check', ActionType.CHECK), ('call', ActionType.CALL), ('raise_to', ActionType.RAISE_TO), ('all_in', ActionType.ALL_IN))`，逐个处理里面的元素。
- 第 500 行：返回计算结果，把这个函数的最终答案交给调用者。

### `_legal_action_items`（第 503-507 行）

签名：

```python
def _legal_action_items(value: Any) -> tuple[Any, ...]
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 504 行：给 `actions` 赋值，准备后面逻辑要用的数据。
- 第 505-506 行：根据条件 `actions is not _MISSING` 分支处理不同情况。
- 第 507 行：返回计算结果，把这个函数的最终答案交给调用者。

### `_normalize_legal_action`（第 510-553 行）

签名：

```python
def _normalize_legal_action(value: Any, *, default_action_type: ActionType | None = None) -> LegalAction
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 515-516 行：根据条件 `isinstance(value, LegalAction)` 分支处理不同情况。
- 第 517-518 行：根据条件 `isinstance(value, str | Enum)` 分支处理不同情况。
- 第 520 行：给 `payload` 赋值，准备后面逻辑要用的数据。
- 第 521-528 行：给 `action_type` 赋值，准备后面逻辑要用的数据。
- 第 529-530 行：根据条件 `action_type is None` 分支处理不同情况。
- 第 532-553 行：返回计算结果，把这个函数的最终答案交给调用者。

### `_normalize_visible_seat`（第 556-559 行）

签名：

```python
def _normalize_visible_seat(value: Any) -> VisibleSeat
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 557-558 行：根据条件 `isinstance(value, VisibleSeat)` 分支处理不同情况。
- 第 559 行：返回计算结果，把这个函数的最终答案交给调用者。

### `_normalize_visible_event`（第 562-570 行）

签名：

```python
def _normalize_visible_event(value: Any) -> Mapping[str, JSONValue]
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 563 行：给 `event` 赋值，准备后面逻辑要用的数据。
- 第 564 行：给 `visibility` 赋值，准备后面逻辑要用的数据。
- 第 565-566 行：根据条件 `visibility is not None and visibility != 'public'` 分支处理不同情况。
- 第 567-568 行：根据条件 `event.get('public') is False` 分支处理不同情况。
- 第 569 行：调用 `event.pop`，执行一个有副作用或校验性质的动作。
- 第 570 行：返回计算结果，把这个函数的最终答案交给调用者。

### `_event_to_visible_dict`（第 573-590 行）

签名：

```python
def _event_to_visible_dict(event: Any) -> Mapping[str, JSONValue]
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 574 行：给 `event_type` 赋值，准备后面逻辑要用的数据。
- 第 575-578 行：给 `payload` 赋值，准备后面逻辑要用的数据。
- 第 579-586 行：声明字段或变量 `visible`，类型是 `dict[str, JSONValue]`。
- 第 587 行：给 `created_at` 赋值，准备后面逻辑要用的数据。
- 第 588-589 行：根据条件 `created_at is not None` 分支处理不同情况。
- 第 590 行：返回计算结果，把这个函数的最终答案交给调用者。

### `_is_public_event`（第 593-598 行）

签名：

```python
def _is_public_event(event: Any) -> bool
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 594 行：给 `visibility` 赋值，准备后面逻辑要用的数据。
- 第 595-596 行：根据条件 `visibility is not None and visibility != 'public'` 分支处理不同情况。
- 第 597 行：给 `public_flag` 赋值，准备后面逻辑要用的数据。
- 第 598 行：返回计算结果，把这个函数的最终答案交给调用者。

### `_event_type`（第 601-602 行）

签名：

```python
def _event_type(event: Any) -> str
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 602 行：返回计算结果，把这个函数的最终答案交给调用者。

### `_event_payload`（第 605-611 行）

签名：

```python
def _event_payload(event: Any) -> Mapping[str, Any]
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 606 行：给 `payload` 赋值，准备后面逻辑要用的数据。
- 第 607-608 行：根据条件 `payload is None` 分支处理不同情况。
- 第 609-610 行：根据条件 `not isinstance(payload, Mapping)` 分支处理不同情况。
- 第 611 行：返回计算结果，把这个函数的最终答案交给调用者。

### `_shown_cards_by_seat`（第 614-624 行）

签名：

```python
def _shown_cards_by_seat(state_summary: Any, public_events: Iterable[Any], player_to_seat: Mapping[Identifier, int]) -> dict[int, tuple[str, ...]]
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 619 行：给 `shown` 赋值，准备后面逻辑要用的数据。
- 第 620-623 行：循环遍历 `public_events`，逐个处理里面的元素。
- 第 624 行：返回计算结果，把这个函数的最终答案交给调用者。

### `_merge_shown_cards_from_payload`（第 627-647 行）

签名：

```python
def _merge_shown_cards_from_payload(shown: dict[int, tuple[str, ...]], payload: Mapping[str, Any], player_to_seat: Mapping[Identifier, int]) -> None
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 632-635 行：循环遍历 `('shown_cards_by_seat', 'revealed_cards_by_seat', 'hole_cards_by_seat')`，逐个处理里面的元素。
- 第 637-647 行：循环遍历 `_showdown_entries(payload)`，逐个处理里面的元素。

### `_showdown_entries`（第 650-660 行）

签名：

```python
def _showdown_entries(payload: Mapping[str, Any]) -> tuple[Any, ...]
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 651 行：声明字段或变量 `entries`，类型是 `list[Any]`。
- 第 652-655 行：循环遍历 `('players', 'revealed', 'showdown', 'showdown_summary', 'entries')`，逐个处理里面的元素。
- 第 656-659 行：根据条件 `any((key in payload for key in ('seat_index', 'player_id', 'shown_cards', 'hole_cards', 'cards')))` 分支处理不同情况。
- 第 660 行：返回计算结果，把这个函数的最终答案交给调用者。

### `_seat_from_entry`（第 663-668 行）

签名：

```python
def _seat_from_entry(entry: Any, player_to_seat: Mapping[Identifier, int]) -> int | None
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 664 行：给 `seat_index` 赋值，准备后面逻辑要用的数据。
- 第 665-666 行：根据条件 `seat_index is not None` 分支处理不同情况。
- 第 667 行：给 `player_id` 赋值，准备后面逻辑要用的数据。
- 第 668 行：返回计算结果，把这个函数的最终答案交给调用者。

### `_folded_seats`（第 671-687 行）

签名：

```python
def _folded_seats(public_events: Iterable[Any]) -> set[int]
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 672 行：声明字段或变量 `folded`，类型是 `set[int]`。
- 第 673-686 行：循环遍历 `public_events`，逐个处理里面的元素。
- 第 687 行：返回计算结果，把这个函数的最终答案交给调用者。

### `_board_cards`（第 690-709 行）

签名：

```python
def _board_cards(state_summary: Any, table_snapshot: Any, public_events: Iterable[Any]) -> tuple[str, ...]
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 693-696 行：给 `cards` 赋值，准备后面逻辑要用的数据。
- 第 697-698 行：根据条件 `cards is not None` 分支处理不同情况。
- 第 700 行：声明字段或变量 `board`，类型是 `tuple[str, ...]`。
- 第 701-708 行：循环遍历 `public_events`，逐个处理里面的元素。
- 第 709 行：返回计算结果，把这个函数的最终答案交给调用者。

### `_seats_by_index`（第 712-720 行）

签名：

```python
def _seats_by_index(table_snapshot: Any) -> dict[int, Any]
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 713 行：给 `raw_seats` 赋值，准备后面逻辑要用的数据。
- 第 714 行：声明字段或变量 `seats`，类型是 `dict[int, Any]`。
- 第 715-719 行：循环遍历 `enumerate(_as_iterable(raw_seats))`，逐个处理里面的元素。
- 第 720 行：返回计算结果，把这个函数的最终答案交给调用者。

### `_player_to_seat`（第 723-728 行）

签名：

```python
def _player_to_seat(seats_by_index: Mapping[int, Any]) -> dict[Identifier, int]
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 724-728 行：返回计算结果，把这个函数的最终答案交给调用者。

### `_resolve_observer_seat`（第 731-741 行）

签名：

```python
def _resolve_observer_seat(*, observer_player_id: Identifier | None, observer_seat_index: int | None, player_to_seat: Mapping[Identifier, int]) -> int
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 737-738 行：根据条件 `observer_seat_index is not None` 分支处理不同情况。
- 第 739-740 行：根据条件 `observer_player_id is not None and observer_player_id in player_to_seat` 分支处理不同情况。
- 第 741 行：主动抛出错误，表示传入数据或当前状态不符合要求。

### `_resolve_observer_player`（第 744-753 行）

签名：

```python
def _resolve_observer_player(*, observer_player_id: Identifier | None, observer_seat_index: int, seats_by_index: Mapping[int, Any]) -> Identifier
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 750-751 行：根据条件 `observer_player_id is not None` 分支处理不同情况。
- 第 752 行：给 `player_id` 赋值，准备后面逻辑要用的数据。
- 第 753 行：返回计算结果，把这个函数的最终答案交给调用者。

### `_actor_ref`（第 756-771 行）

签名：

```python
def _actor_ref(state_summary: Any) -> Any
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 757-771 行：返回计算结果，把这个函数的最终答案交给调用者。

### `_actor_seat_index`（第 774-783 行）

签名：

```python
def _actor_seat_index(actor: Any, player_to_seat: Mapping[Identifier, int]) -> int | None
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 775-776 行：根据条件 `isinstance(actor, int) and (not isinstance(actor, bool))` 分支处理不同情况。
- 第 777 行：给 `seat_index` 赋值，准备后面逻辑要用的数据。
- 第 778-779 行：根据条件 `seat_index is not None` 分支处理不同情况。
- 第 780 行：给 `player_id` 赋值，准备后面逻辑要用的数据。
- 第 781-782 行：根据条件 `player_id is not None` 分支处理不同情况。
- 第 783 行：返回计算结果，把这个函数的最终答案交给调用者。

### `_actor_player_id`（第 786-789 行）

签名：

```python
def _actor_player_id(actor: Any) -> Identifier | None
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 787-788 行：根据条件 `isinstance(actor, str)` 分支处理不同情况。
- 第 789 行：返回计算结果，把这个函数的最终答案交给调用者。

### `_button_seat_index`（第 792-799 行）

签名：

```python
def _button_seat_index(table_snapshot: Any, state_summary: Any) -> int
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 793-798 行：给 `value` 赋值，准备后面逻辑要用的数据。
- 第 799 行：返回计算结果，把这个函数的最终答案交给调用者。

### `_visible_status`（第 802-822 行）

签名：

```python
def _visible_status(*, raw_status: Any, player_id: Any, seat_index: int, folded_seats: set[int], stack: int, hole_card_count: int) -> str
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 811-812 行：根据条件 `player_id is None` 分支处理不同情况。
- 第 813-814 行：根据条件 `seat_index in folded_seats` 分支处理不同情况。
- 第 815 行：给 `normalized` 赋值，准备后面逻辑要用的数据。
- 第 816-817 行：根据条件 `normalized in {'folded', 'all_in', 'sitting_out'}` 分支处理不同情况。
- 第 818-819 行：根据条件 `hole_card_count > 0 and stack == 0` 分支处理不同情况。
- 第 820-821 行：根据条件 `normalized in {'in_hand', 'seated'}` 分支处理不同情况。
- 第 822 行：返回计算结果，把这个函数的最终答案交给调用者。

### `_status_string`（第 825-829 行）

签名：

```python
def _status_string(status: Any, player_id: Any) -> str
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 826 行：给 `normalized` 赋值，准备后面逻辑要用的数据。
- 第 827-828 行：根据条件 `normalized` 分支处理不同情况。
- 第 829 行：返回计算结果，把这个函数的最终答案交给调用者。

### `_indexed_amounts`（第 832-843 行）

签名：

```python
def _indexed_amounts(value: Any) -> dict[int, int]
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 833-834 行：根据条件 `value is None` 分支处理不同情况。
- 第 835-840 行：根据条件 `isinstance(value, Mapping)` 分支处理不同情况。
- 第 841-843 行：返回计算结果，把这个函数的最终答案交给调用者。

### `_indexed_card_mapping`（第 846-855 行）

签名：

```python
def _indexed_card_mapping(value: Any) -> dict[int, tuple[str, ...]]
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 847-848 行：根据条件 `value is None` 分支处理不同情况。
- 第 849-854 行：根据条件 `isinstance(value, Mapping)` 分支处理不同情况。
- 第 855 行：返回计算结果，把这个函数的最终答案交给调用者。

### `_indexed_or_raw`（第 858-866 行）

签名：

```python
def _indexed_or_raw(indexed: Mapping[int, int], seat_index: int, raw_seat: Any, names: tuple[str, ...]) -> int
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 864-865 行：根据条件 `seat_index in indexed` 分支处理不同情况。
- 第 866 行：返回计算结果，把这个函数的最终答案交给调用者。

### `_can_parse_index`（第 869-874 行）

签名：

```python
def _can_parse_index(value: Any) -> bool
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 870-873 行：尝试执行可能失败的操作，并在异常发生时转成项目自己的处理方式。
- 第 874 行：返回计算结果，把这个函数的最终答案交给调用者。

### `_read`（第 877-889 行）

签名：

```python
def _read(value: Any, names: tuple[str, ...], default: Any = _MISSING) -> Any
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 878-881 行：根据条件 `value is None` 分支处理不同情况。
- 第 882-886 行：循环遍历 `names`，逐个处理里面的元素。
- 第 887-888 行：根据条件 `default is _MISSING` 分支处理不同情况。
- 第 889 行：返回计算结果，把这个函数的最终答案交给调用者。

### `_first_defined`（第 892-896 行）

签名：

```python
def _first_defined(*values: Any) -> Any
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 893-895 行：循环遍历 `values`，逐个处理里面的元素。
- 第 896 行：返回计算结果，把这个函数的最终答案交给调用者。

### `_first_identifier`（第 899-903 行）

签名：

```python
def _first_identifier(*values: Any) -> Identifier
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 900-902 行：循环遍历 `values`，逐个处理里面的元素。
- 第 903 行：主动抛出错误，表示传入数据或当前状态不符合要求。

### `_require_identifier`（第 906-909 行）

签名：

```python
def _require_identifier(value: Any) -> Identifier
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 907-908 行：根据条件 `isinstance(value, bool) or not isinstance(value, str | int) or value == ''` 分支处理不同情况。
- 第 909 行：返回计算结果，把这个函数的最终答案交给调用者。

### `_optional_identifier`（第 912-915 行）

签名：

```python
def _optional_identifier(value: Any) -> Identifier | None
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 913-914 行：根据条件 `value is None` 分支处理不同情况。
- 第 915 行：返回计算结果，把这个函数的最终答案交给调用者。

### `_optional_string`（第 918-923 行）

签名：

```python
def _optional_string(value: Any) -> str | None
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 919-920 行：根据条件 `value is None` 分支处理不同情况。
- 第 921-922 行：根据条件 `not isinstance(value, str)` 分支处理不同情况。
- 第 923 行：返回计算结果，把这个函数的最终答案交给调用者。

### `_string_or_none`（第 926-932 行）

签名：

```python
def _string_or_none(value: Any) -> str | None
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 927-928 行：根据条件 `value is None` 分支处理不同情况。
- 第 929 行：给 `normalized` 赋值，准备后面逻辑要用的数据。
- 第 930-931 行：根据条件 `normalized is None` 分支处理不同情况。
- 第 932 行：返回计算结果，把这个函数的最终答案交给调用者。

### `_require_seat_index`（第 935-938 行）

签名：

```python
def _require_seat_index(value: Any) -> int
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 936-937 行：根据条件 `isinstance(value, bool) or not isinstance(value, int) or value < 0 or (value >= SEAT_COUNT)` 分支处理不同情况。
- 第 938 行：返回计算结果，把这个函数的最终答案交给调用者。

### `_int_or_none`（第 941-951 行）

签名：

```python
def _int_or_none(value: Any) -> int | None
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 942-943 行：根据条件 `value is None or isinstance(value, bool)` 分支处理不同情况。
- 第 944-945 行：根据条件 `isinstance(value, int)` 分支处理不同情况。
- 第 946-950 行：根据条件 `isinstance(value, str)` 分支处理不同情况。
- 第 951 行：返回计算结果，把这个函数的最终答案交给调用者。

### `_optional_int`（第 954-956 行）

签名：

```python
def _optional_int(value: Any, default: int) -> int
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 955 行：给 `parsed` 赋值，准备后面逻辑要用的数据。
- 第 956 行：返回计算结果，把这个函数的最终答案交给调用者。

### `_chip_amount`（第 959-962 行）

签名：

```python
def _chip_amount(value: Any, name: str) -> int
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 960-961 行：根据条件 `isinstance(value, bool) or not isinstance(value, int) or value < 0` 分支处理不同情况。
- 第 962 行：返回计算结果，把这个函数的最终答案交给调用者。

### `_optional_chip_amount`（第 965-968 行）

签名：

```python
def _optional_chip_amount(value: Any, name: str) -> int | None
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 966-967 行：根据条件 `value is None` 分支处理不同情况。
- 第 968 行：返回计算结果，把这个函数的最终答案交给调用者。

### `_string_tuple`（第 971-976 行）

签名：

```python
def _string_tuple(value: Any, name: str) -> tuple[str, ...]
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 972-973 行：根据条件 `value is None` 分支处理不同情况。
- 第 974-975 行：根据条件 `isinstance(value, str | bytes) or not isinstance(value, Iterable)` 分支处理不同情况。
- 第 976 行：返回计算结果，把这个函数的最终答案交给调用者。

### `_card_string`（第 979-985 行）

签名：

```python
def _card_string(value: Any, name: str) -> str
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 980 行：调用 `_reject_runtime_object`，执行一个有副作用或校验性质的动作。
- 第 981-982 行：根据条件 `not isinstance(value, str)` 分支处理不同情况。
- 第 983-984 行：根据条件 `not value` 分支处理不同情况。
- 第 985 行：返回计算结果，把这个函数的最终答案交给调用者。

### `_as_iterable`（第 988-995 行）

签名：

```python
def _as_iterable(value: Any) -> tuple[Any, ...]
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 989-990 行：根据条件 `value is None` 分支处理不同情况。
- 第 991-992 行：根据条件 `isinstance(value, Mapping)` 分支处理不同情况。
- 第 993-994 行：根据条件 `isinstance(value, str | bytes) or not isinstance(value, Iterable)` 分支处理不同情况。
- 第 995 行：返回计算结果，把这个函数的最终答案交给调用者。

### `_object_to_public_mapping`（第 998-1010 行）

签名：

```python
def _object_to_public_mapping(value: Any, *, allow_private_cards: bool) -> dict[str, JSONValue]
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 999-1000 行：根据条件 `isinstance(value, Mapping)` 分支处理不同情况。
- 第 1001-1002 行：根据条件 `hasattr(value, 'to_dict') and callable(value.to_dict)` 分支处理不同情况。
- 第 1003-1007 行：根据条件 `hasattr(value, '__dataclass_fields__')` 分支处理不同情况。
- 第 1008-1009 行：根据条件 `hasattr(value, '__dict__')` 分支处理不同情况。
- 第 1010 行：主动抛出错误，表示传入数据或当前状态不符合要求。

### `_sanitize_public_mapping`（第 1013-1027 行）

签名：

```python
def _sanitize_public_mapping(value: Mapping[str, Any], *, allow_private_cards: bool) -> dict[str, JSONValue]
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 1016 行：声明字段或变量 `sanitized`，类型是 `dict[str, JSONValue]`。
- 第 1017-1026 行：循环遍历 `value.items()`，逐个处理里面的元素。
- 第 1027 行：返回计算结果，把这个函数的最终答案交给调用者。

### `_to_json_value`（第 1030-1050 行）

签名：

```python
def _to_json_value(value: Any, *, allow_private_cards: bool = False) -> JSONValue
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 1031 行：调用 `_reject_runtime_object`，执行一个有副作用或校验性质的动作。
- 第 1032-1033 行：根据条件 `value is None or isinstance(value, str)` 分支处理不同情况。
- 第 1034-1035 行：根据条件 `isinstance(value, bool)` 分支处理不同情况。
- 第 1036-1037 行：根据条件 `isinstance(value, int)` 分支处理不同情况。
- 第 1038-1041 行：根据条件 `isinstance(value, float)` 分支处理不同情况。
- 第 1042-1043 行：根据条件 `isinstance(value, Enum)` 分支处理不同情况。
- 第 1044-1045 行：根据条件 `isinstance(value, Mapping)` 分支处理不同情况。
- 第 1046-1047 行：根据条件 `isinstance(value, Sequence) and (not isinstance(value, str | bytes))` 分支处理不同情况。
- 第 1048-1049 行：根据条件 `hasattr(value, 'isoformat') and callable(value.isoformat)` 分支处理不同情况。
- 第 1050 行：返回计算结果，把这个函数的最终答案交给调用者。

### `_enum_value`（第 1053-1056 行）

签名：

```python
def _enum_value(value: Any) -> Any
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 1054-1055 行：根据条件 `isinstance(value, Enum)` 分支处理不同情况。
- 第 1056 行：返回计算结果，把这个函数的最终答案交给调用者。

### `_reject_runtime_object`（第 1059-1062 行）

签名：

```python
def _reject_runtime_object(value: Any, name: str) -> None
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 1060 行：给 `module_name` 赋值，准备后面逻辑要用的数据。
- 第 1061-1062 行：根据条件 `module_name == 'pokerkit' or module_name.startswith('pokerkit.')` 分支处理不同情况。

## 初学者阅读建议

先看“这个文件是干什么的”，再看类和函数标题。遇到以下划线开头的函数，可以先理解成内部工具；遇到 `to_dict/from_dict/to_json/from_json`，重点记住它们是在对象、字典和 JSON 之间转换。
