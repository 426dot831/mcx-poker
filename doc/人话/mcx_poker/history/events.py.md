# `mcx_poker/history/events.py` 人话讲解

源文件：`/Users/machengqi/Documents/mcx-poker/src/mcx_poker/history/events.py`

## 这个文件是干什么的

源码说明：Temporary in-memory hand event log.

The log intentionally stores only JSON-compatible payloads.  That keeps the
events easy to broadcast, inspect, and later persist without leaking PokerKit
runtime objects or private card state through public reads.

人话概括：

负责记录和查询牌局事件历史，让系统知道之前发生过什么。

## 导入区

- 第 8 行：从 `__future__` 导入 `annotations`。
- 第 10 行：从 `collections.abc` 导入 `Mapping`。
- 第 11 行：从 `dataclasses` 导入 `dataclass, field, replace`。
- 第 12 行：从 `datetime` 导入 `UTC, datetime`。
- 第 13 行：从 `enum` 导入 `StrEnum`。
- 第 14 行：从 `math` 导入 `isfinite`。
- 第 15 行：从 `typing` 导入 `TypeAlias`。

人话：导入区是在声明“这个文件需要哪些外部工具”。标准库通常提供基础能力，项目内导入则说明它依赖哪些业务模块。

## 顶层常量和类型

- 第 17 行：`JSONValue`: `TypeAlias` = `str | int | float | bool | None | list['JSONValue'] | dict[str, 'JSONValue']`。人话：声明一个带类型的模块级变量。
- 第 42 行：`_PLAYER_SCOPED_ONLY_EVENT_TYPES` = `frozenset({EventType.HOLE_CARDS_DEALT})`。人话：在模块级别准备一个后面会反复使用的值。
- 第 43-51 行：`_ALWAYS_SENSITIVE_PUBLIC_KEYS` = `frozenset({'deck', 'deck_order', 'remaining_deck', 'stub', 'undealt_cards'})`。人话：在模块级别准备一个后面会反复使用的值。
- 第 52 行：`_PRIVATE_CARD_PUBLIC_KEYS` = `frozenset({'hole_cards', 'private_cards', 'pocket_cards'})`。人话：在模块级别准备一个后面会反复使用的值。
- 第 448 行：`TemporaryHandEventLog` = `HandEventLog`。人话：在模块级别准备一个后面会反复使用的值。
- 第 450 行：`_default_log` = `HandEventLog()`。人话：在模块级别准备一个后面会反复使用的值。
- 第 607-619 行：`__all__` = `['EventType', 'EventVisibility', 'HandEvent', 'HandEventLog', 'JSONValue', 'TemporaryHandEventLog', 'append', 'clear_hand', 'get_last_sequence', 'list_player_events', 'list_public_events']`。人话：在模块级别准备一个后面会反复使用的值。

## 类 `EventType`（第 20-32 行）

继承：`StrEnum`。

源码说明：Supported temporary hand event types.

人话：把一组相关数据和行为封装到一个类型里，供其他模块按统一接口使用。

字段/类变量：

- `HAND_STARTED`：类级变量，值 `'hand_started'`。
- `SEAT_SNAPSHOT`：类级变量，值 `'seat_snapshot'`。
- `HOLE_CARDS_DEALT`：类级变量，值 `'hole_cards_dealt'`。
- `BOARD_DEALT`：类级变量，值 `'board_dealt'`。
- `ACTION_SUCCEEDED`：类级变量，值 `'action_succeeded'`。
- `ACTION_REJECTED`：类级变量，值 `'action_rejected'`。
- `POT_UPDATED`：类级变量，值 `'pot_updated'`。
- `SHOWDOWN`：类级变量，值 `'showdown'`。
- `SETTLEMENT`：类级变量，值 `'settlement'`。
- `HAND_ENDED`：类级变量，值 `'hand_ended'`。

## 类 `EventVisibility`（第 35-39 行）

继承：`StrEnum`。

源码说明：Visibility rules for an event.

人话：把一组相关数据和行为封装到一个类型里，供其他模块按统一接口使用。

字段/类变量：

- `PUBLIC`：类级变量，值 `'public'`。
- `PLAYER_SCOPED`：类级变量，值 `'player_scoped'`。

## 类 `HandEvent`（第 56-180 行）

装饰器：`@dataclass(frozen=True, slots=True)`。

源码说明：A single temporary event emitted during a hand.

``target_player_id`` is intentionally optional and additive: the MVP fields
use ``actor_player_id`` as the private recipient when no explicit target is
supplied, while future event types can target a player who is not the actor.

人话：把一组相关数据和行为封装到一个类型里，供其他模块按统一接口使用。

字段/类变量：

- `hand_id`：类型 `str`。
- `event_type`：类型 `EventType | str`。
- `sequence_number`：类型 `int`，默认值 `0`。
- `actor_player_id`：类型 `str | None`，默认值 `None`。
- `actor_seat_index`：类型 `int | None`，默认值 `None`。
- `public_payload`：类型 `JSONValue | None`，默认值 `None`。
- `private_payload`：类型 `JSONValue | None`，默认值 `None`。
- `visibility`：类型 `EventVisibility | str`，默认值 `EventVisibility.PUBLIC`。
- `created_at`：类型 `datetime`，默认值 `field(default_factory=lambda: datetime.now(UTC))`。
- `target_player_id`：类型 `str | None`，默认值 `None`。

这个类里的方法：

### `__post_init__`（第 75-131 行）

签名：

```python
def __post_init__(self) -> None
```

人话：dataclass 创建对象后自动执行，用来做校验、标准化或补充字段。

关键代码块：

- 第 76 行：给 `event_type` 赋值，准备后面逻辑要用的数据。
- 第 77 行：给 `visibility` 赋值，准备后面逻辑要用的数据。
- 第 78 行：给 `public_payload` 赋值，准备后面逻辑要用的数据。
- 第 79 行：给 `private_payload` 赋值，准备后面逻辑要用的数据。
- 第 81 行：调用 `object.__setattr__`，执行一个有副作用或校验性质的动作。
- 第 82 行：调用 `object.__setattr__`，执行一个有副作用或校验性质的动作。
- 第 83 行：调用 `object.__setattr__`，执行一个有副作用或校验性质的动作。
- 第 84 行：调用 `object.__setattr__`，执行一个有副作用或校验性质的动作。
- 第 86 行：调用 `_validate_non_empty_string`，执行一个有副作用或校验性质的动作。
- 第 87 行：调用 `_validate_optional_non_empty_string`，执行一个有副作用或校验性质的动作。
- 第 88 行：调用 `_validate_optional_non_empty_string`，执行一个有副作用或校验性质的动作。
- 第 90-91 行：根据条件 `not isinstance(self.sequence_number, int) or isinstance(self.sequence_number, bool)` 分支处理不同情况。
- 第 92-93 行：根据条件 `self.sequence_number < 0` 分支处理不同情况。
- 第 95-102 行：根据条件 `self.actor_seat_index is not None` 分支处理不同情况。
- 第 104-105 行：根据条件 `self.created_at.tzinfo is None` 分支处理不同情况。
- 第 107-111 行：根据条件 `event_type in _PLAYER_SCOPED_ONLY_EVENT_TYPES and visibility != EventVisibility.PLAYER_SCOPED` 分支处理不同情况。
- 后面还有 4 个语句块，主要继续完成这个函数的收尾、返回或异常处理。

### `to_dict`（第 133-149 行）

签名：

```python
def to_dict(self, *, include_private: bool = True) -> dict[str, JSONValue]
```

源码说明：Return a JSON-compatible representation of the event.

人话：把对象转成普通字典，方便 API、日志、测试或 JSON 序列化使用。

关键代码块：

- 第 136-146 行：声明字段或变量 `event_dict`，类型是 `dict[str, JSONValue]`。
- 第 147-148 行：根据条件 `include_private` 分支处理不同情况。
- 第 149 行：返回计算结果，把这个函数的最终答案交给调用者。

### `from_dict`（第 152-180 行）

签名：

```python
def from_dict(cls, event_dict: Mapping[str, object]) -> HandEvent
```

装饰器：`@classmethod`。

源码说明：Rebuild an event from ``to_dict`` output.

人话：从普通字典恢复成项目里的强类型对象，同时复用构造时的校验逻辑。

关键代码块：

- 第 155 行：给 `created_at` 赋值，准备后面逻辑要用的数据。
- 第 156-163 行：根据条件 `isinstance(created_at, str)` 分支处理不同情况。
- 第 165 行：给 `sequence_number` 赋值，准备后面逻辑要用的数据。
- 第 166-167 行：根据条件 `sequence_number is None` 分支处理不同情况。
- 第 169-180 行：返回计算结果，把这个函数的最终答案交给调用者。

## 类 `HandEventLog`（第 183-445 行）

源码说明：In-memory event log scoped to current process lifetime.

人话：把一组相关数据和行为封装到一个类型里，供其他模块按统一接口使用。

这个类里的方法：

### `__init__`（第 186-194 行）

签名：

```python
def __init__(self, *, max_retained_hands: int = 2) -> None
```

人话：初始化对象，接收外部传入的数据并准备对象内部状态。

关键代码块：

- 第 187-188 行：根据条件 `not isinstance(max_retained_hands, int) or isinstance(max_retained_hands, bool)` 分支处理不同情况。
- 第 189-190 行：根据条件 `max_retained_hands < 1` 分支处理不同情况。
- 第 191 行：给 `self._max_retained_hands` 赋值，准备后面逻辑要用的数据。
- 第 192 行：声明字段或变量 `self._events_by_hand`，类型是 `dict[str, list[HandEvent]]`。
- 第 193 行：声明字段或变量 `self._last_sequences`，类型是 `dict[str, int]`。
- 第 194 行：声明字段或变量 `self._hand_order`，类型是 `list[str]`。

### `append`（第 196-208 行）

签名：

```python
def append(self, event: HandEvent) -> HandEvent
```

源码说明：Append an event and assign the next sequence number for its hand.

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 199-200 行：根据条件 `not isinstance(event, HandEvent)` 分支处理不同情况。
- 第 202 行：调用 `self._ensure_hand_tracked`，执行一个有副作用或校验性质的动作。
- 第 203 行：给 `next_sequence` 赋值，准备后面逻辑要用的数据。
- 第 204 行：给 `stored_event` 赋值，准备后面逻辑要用的数据。
- 第 206 行：调用 `self._events_by_hand.setdefault(event.hand_id, []).append`，执行一个有副作用或校验性质的动作。
- 第 207 行：给 `self._last_sequences[event.hand_id]` 赋值，准备后面逻辑要用的数据。
- 第 208 行：返回计算结果，把这个函数的最终答案交给调用者。

### `list_public_events`（第 210-217 行）

签名：

```python
def list_public_events(self, hand_id: str) -> list[HandEvent]
```

源码说明：Return events visible to every observer.

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 213-217 行：返回计算结果，把这个函数的最终答案交给调用者。

### `list_player_events`（第 219-227 行）

签名：

```python
def list_player_events(self, hand_id: str, player_id: str) -> list[HandEvent]
```

源码说明：Return public events plus private events scoped to ``player_id``.

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 222 行：调用 `_validate_non_empty_string`，执行一个有副作用或校验性质的动作。
- 第 223-227 行：返回计算结果，把这个函数的最终答案交给调用者。

### `list_successful_actions`（第 229-236 行）

签名：

```python
def list_successful_actions(self, hand_id: str) -> list[HandEvent]
```

源码说明：Return only successful public action events.

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 232-236 行：返回计算结果，把这个函数的最终答案交给调用者。

### `clear_hand`（第 238-245 行）

签名：

```python
def clear_hand(self, hand_id: str) -> None
```

源码说明：Remove all retained events and sequence state for a hand.

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 241 行：调用 `self._events_by_hand.pop`，执行一个有副作用或校验性质的动作。
- 第 242 行：调用 `self._last_sequences.pop`，执行一个有副作用或校验性质的动作。
- 第 243-245 行：给 `self._hand_order` 赋值，准备后面逻辑要用的数据。

### `get_last_sequence`（第 247-250 行）

签名：

```python
def get_last_sequence(self, hand_id: str) -> int
```

源码说明：Return the last assigned sequence number for ``hand_id``.

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 250 行：返回计算结果，把这个函数的最终答案交给调用者。

### `record_hand_started`（第 252-263 行）

签名：

```python
def record_hand_started(self, hand_id: str, payload: Mapping[str, object] | None = None) -> HandEvent
```

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 257-263 行：返回计算结果，把这个函数的最终答案交给调用者。

### `record_seat_snapshot`（第 265-280 行）

签名：

```python
def record_seat_snapshot(self, hand_id: str, seats: object, *, payload: Mapping[str, object] | None = None) -> HandEvent
```

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 272 行：给 `event_payload` 赋值，准备后面逻辑要用的数据。
- 第 273 行：给 `event_payload['seats']` 赋值，准备后面逻辑要用的数据。
- 第 274-280 行：返回计算结果，把这个函数的最终答案交给调用者。

### `record_hole_cards_dealt`（第 282-302 行）

签名：

```python
def record_hole_cards_dealt(self, hand_id: str, player_id: str, cards: object, *, seat_index: int | None = None, payload: Mapping[str, object] | None = None) -> HandEvent
```

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 291 行：给 `private_payload` 赋值，准备后面逻辑要用的数据。
- 第 292 行：给 `private_payload['cards']` 赋值，准备后面逻辑要用的数据。
- 第 293-302 行：返回计算结果，把这个函数的最终答案交给调用者。

### `record_board_dealt`（第 304-325 行）

签名：

```python
def record_board_dealt(self, hand_id: str, cards: object, *, street: str | None = None, board: object | None = None, payload: Mapping[str, object] | None = None) -> HandEvent
```

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 313 行：给 `event_payload` 赋值，准备后面逻辑要用的数据。
- 第 314 行：给 `event_payload['cards']` 赋值，准备后面逻辑要用的数据。
- 第 315-316 行：根据条件 `street is not None` 分支处理不同情况。
- 第 317-318 行：根据条件 `board is not None` 分支处理不同情况。
- 第 319-325 行：返回计算结果，把这个函数的最终答案交给调用者。

### `record_action_succeeded`（第 327-349 行）

签名：

```python
def record_action_succeeded(self, hand_id: str, player_id: str, action: str, *, amount: int | float | None = None, seat_index: int | None = None, payload: Mapping[str, object] | None = None) -> HandEvent
```

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 337 行：给 `event_payload` 赋值，准备后面逻辑要用的数据。
- 第 338 行：给 `event_payload['action']` 赋值，准备后面逻辑要用的数据。
- 第 339-340 行：根据条件 `amount is not None` 分支处理不同情况。
- 第 341-349 行：返回计算结果，把这个函数的最终答案交给调用者。

### `record_action_rejected`（第 351-374 行）

签名：

```python
def record_action_rejected(self, hand_id: str, player_id: str, reason: str, *, attempted_action: str | None = None, seat_index: int | None = None, payload: Mapping[str, object] | None = None) -> HandEvent
```

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 361 行：给 `private_payload` 赋值，准备后面逻辑要用的数据。
- 第 362 行：给 `private_payload['reason']` 赋值，准备后面逻辑要用的数据。
- 第 363-364 行：根据条件 `attempted_action is not None` 分支处理不同情况。
- 第 365-374 行：返回计算结果，把这个函数的最终答案交给调用者。

### `record_pot_updated`（第 376-387 行）

签名：

```python
def record_pot_updated(self, hand_id: str, summary: Mapping[str, object] | None = None) -> HandEvent
```

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 381-387 行：返回计算结果，把这个函数的最终答案交给调用者。

### `record_betting_summary`（第 389-394 行）

签名：

```python
def record_betting_summary(self, hand_id: str, summary: Mapping[str, object] | None = None) -> HandEvent
```

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 394 行：返回计算结果，把这个函数的最终答案交给调用者。

### `record_showdown`（第 396-407 行）

签名：

```python
def record_showdown(self, hand_id: str, revealed: Mapping[str, object] | None = None) -> HandEvent
```

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 401-407 行：返回计算结果，把这个函数的最终答案交给调用者。

### `record_settlement`（第 409-420 行）

签名：

```python
def record_settlement(self, hand_id: str, settlement: Mapping[str, object] | None = None) -> HandEvent
```

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 414-420 行：返回计算结果，把这个函数的最终答案交给调用者。

### `record_hand_ended`（第 422-433 行）

签名：

```python
def record_hand_ended(self, hand_id: str, payload: Mapping[str, object] | None = None) -> HandEvent
```

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 427-433 行：返回计算结果，把这个函数的最终答案交给调用者。

### `_ensure_hand_tracked`（第 435-445 行）

签名：

```python
def _ensure_hand_tracked(self, hand_id: str) -> None
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 436 行：调用 `_validate_non_empty_string`，执行一个有副作用或校验性质的动作。
- 第 437-438 行：根据条件 `hand_id in self._events_by_hand` 分支处理不同情况。
- 第 440 行：给 `self._events_by_hand[hand_id]` 赋值，准备后面逻辑要用的数据。
- 第 441 行：调用 `self._hand_order.append`，执行一个有副作用或校验性质的动作。
- 第 442-445 行：只要 `len(self._hand_order) > self._max_retained_hands` 还成立，就持续执行循环。

## 模块级函数

### `append`（第 453-454 行）

签名：

```python
def append(event: HandEvent) -> HandEvent
```

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 454 行：返回计算结果，把这个函数的最终答案交给调用者。

### `list_public_events`（第 457-458 行）

签名：

```python
def list_public_events(hand_id: str) -> list[HandEvent]
```

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 458 行：返回计算结果，把这个函数的最终答案交给调用者。

### `list_player_events`（第 461-462 行）

签名：

```python
def list_player_events(hand_id: str, player_id: str) -> list[HandEvent]
```

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 462 行：返回计算结果，把这个函数的最终答案交给调用者。

### `clear_hand`（第 465-466 行）

签名：

```python
def clear_hand(hand_id: str) -> None
```

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 466 行：调用 `_default_log.clear_hand`，执行一个有副作用或校验性质的动作。

### `get_last_sequence`（第 469-470 行）

签名：

```python
def get_last_sequence(hand_id: str) -> int
```

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 470 行：返回计算结果，把这个函数的最终答案交给调用者。

### `_coerce_event_type`（第 473-477 行）

签名：

```python
def _coerce_event_type(event_type: EventType | str) -> EventType
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 474-477 行：尝试执行可能失败的操作，并在异常发生时转成项目自己的处理方式。

### `_coerce_visibility`（第 480-486 行）

签名：

```python
def _coerce_visibility(visibility: EventVisibility | str) -> EventVisibility
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 481-482 行：根据条件 `isinstance(visibility, str)` 分支处理不同情况。
- 第 483-486 行：尝试执行可能失败的操作，并在异常发生时转成项目自己的处理方式。

### `_normalize_payload`（第 489-513 行）

签名：

```python
def _normalize_payload(value: object, *, path: str) -> JSONValue
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 490-491 行：根据条件 `_is_pokerkit_object(value)` 分支处理不同情况。
- 第 492-493 行：根据条件 `value is None or isinstance(value, str)` 分支处理不同情况。
- 第 494-495 行：根据条件 `isinstance(value, bool)` 分支处理不同情况。
- 第 496-497 行：根据条件 `isinstance(value, int)` 分支处理不同情况。
- 第 498-501 行：根据条件 `isinstance(value, float)` 分支处理不同情况。
- 第 502-508 行：根据条件 `isinstance(value, Mapping)` 分支处理不同情况。
- 第 509-512 行：根据条件 `isinstance(value, (list, tuple))` 分支处理不同情况。
- 第 513 行：主动抛出错误，表示传入数据或当前状态不符合要求。

### `_payload_mapping`（第 516-522 行）

签名：

```python
def _payload_mapping(payload: Mapping[str, object] | None) -> dict[str, JSONValue]
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 517-518 行：根据条件 `payload is None` 分支处理不同情况。
- 第 519 行：给 `normalized` 赋值，准备后面逻辑要用的数据。
- 第 520-521 行：根据条件 `not isinstance(normalized, dict)` 分支处理不同情况。
- 第 522 行：返回计算结果，把这个函数的最终答案交给调用者。

### `_is_pokerkit_object`（第 525-527 行）

签名：

```python
def _is_pokerkit_object(value: object) -> bool
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 526 行：给 `module_name` 赋值，准备后面逻辑要用的数据。
- 第 527 行：返回计算结果，把这个函数的最终答案交给调用者。

### `_find_sensitive_public_key`（第 530-560 行）

签名：

```python
def _find_sensitive_public_key(value: JSONValue | None, path: str = 'public_payload', *, allow_private_card_keys: bool = False) -> str | None
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 536-559 行：根据条件 `isinstance(value, dict)` 分支处理不同情况。
- 第 560 行：返回计算结果，把这个函数的最终答案交给调用者。

### `_validate_non_empty_string`（第 563-565 行）

签名：

```python
def _validate_non_empty_string(value: object, name: str) -> None
```

人话：校验输入或状态是否合法，发现问题时返回错误或抛出异常。

关键代码块：

- 第 564-565 行：根据条件 `not isinstance(value, str) or not value` 分支处理不同情况。

### `_validate_optional_non_empty_string`（第 568-570 行）

签名：

```python
def _validate_optional_non_empty_string(value: object, name: str) -> None
```

人话：校验输入或状态是否合法，发现问题时返回错误或抛出异常。

关键代码块：

- 第 569-570 行：根据条件 `value is not None` 分支处理不同情况。

### `_required_string`（第 573-577 行）

签名：

```python
def _required_string(event_dict: Mapping[str, object], key: str) -> str
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 574 行：给 `value` 赋值，准备后面逻辑要用的数据。
- 第 575-576 行：根据条件 `not isinstance(value, str) or not value` 分支处理不同情况。
- 第 577 行：返回计算结果，把这个函数的最终答案交给调用者。

### `_optional_string`（第 580-586 行）

签名：

```python
def _optional_string(event_dict: Mapping[str, object], key: str) -> str | None
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 581 行：给 `value` 赋值，准备后面逻辑要用的数据。
- 第 582-583 行：根据条件 `value is None` 分支处理不同情况。
- 第 584-585 行：根据条件 `not isinstance(value, str) or not value` 分支处理不同情况。
- 第 586 行：返回计算结果，把这个函数的最终答案交给调用者。

### `_optional_int`（第 589-600 行）

签名：

```python
def _optional_int(event_dict: Mapping[str, object], key: str, *, default: int | None) -> int | None
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 595 行：给 `value` 赋值，准备后面逻辑要用的数据。
- 第 596-597 行：根据条件 `value is None` 分支处理不同情况。
- 第 598-599 行：根据条件 `not isinstance(value, int) or isinstance(value, bool)` 分支处理不同情况。
- 第 600 行：返回计算结果，把这个函数的最终答案交给调用者。

### `_optional_payload`（第 603-604 行）

签名：

```python
def _optional_payload(event_dict: Mapping[str, object], key: str) -> JSONValue | None
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 604 行：返回计算结果，把这个函数的最终答案交给调用者。

## 对外公开接口

`__all__` 声明这个模块希望别人主要使用这些名字：

- `EventType`
- `EventVisibility`
- `HandEvent`
- `HandEventLog`
- `JSONValue`
- `TemporaryHandEventLog`
- `append`
- `clear_hand`
- `get_last_sequence`
- `list_player_events`
- `list_public_events`

## 初学者阅读建议

先看“这个文件是干什么的”，再看类和函数标题。遇到以下划线开头的函数，可以先理解成内部工具；遇到 `to_dict/from_dict/to_json/from_json`，重点记住它们是在对象、字典和 JSON 之间转换。
