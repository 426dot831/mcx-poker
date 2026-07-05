# `mcx_poker/engine/validator.py` 人话讲解

源文件：`/Users/machengqi/Documents/mcx-poker/src/mcx_poker/engine/validator.py`

## 这个文件是干什么的

源码说明：Platform action validation before adapter submission.

人话概括：

属于牌局引擎层，负责动作、校验、游戏循环或 PokerKit 适配。

## 导入区

- 第 3 行：从 `__future__` 导入 `annotations`。
- 第 5 行：从 `collections.abc` 导入 `Iterable, Mapping`。
- 第 6 行：从 `dataclasses` 导入 `dataclass`。
- 第 7 行：从 `typing` 导入 `Any, Literal, Protocol, TypeAlias`。
- 第 9-14 行：从 `mcx_poker.engine.actions` 导入 `ActionError, ActionType, LegalActionSet, PlayerAction`。

人话：导入区是在声明“这个文件需要哪些外部工具”。标准库通常提供基础能力，项目内导入则说明它依赖哪些业务模块。

## 顶层常量和类型

- 第 16 行：`Identifier`: `TypeAlias` = `str | int`。人话：声明一个带类型的模块级变量。
- 第 17 行：`ValidationSource`: `TypeAlias` = `Literal['platform']`。人话：声明一个带类型的模块级变量。
- 第 19-28 行：`ERROR_MESSAGES` = `{'hand_mismatch': 'Action hand does not match the current hand.', 'turn_mismatch': 'Action turn does not match the current turn.', 'player_not_seated': 'Player is not seated at the submitted seat.', 'not_current_actor': 'Action was not submitted by the current actor.', 'action_not_available': 'Action is not available for the current actor.', 'amount_required': 'RaiseTo requires a positive integer amount.', 'amount_not_allowed': 'Only RaiseTo may include an amount.', 'amount_out_of_range': 'RaiseTo amount is outside the legal range.'}`。人话：在模块级别准备一个后面会反复使用的值。
- 第 84 行：`ActionValidationResult`: `TypeAlias` = `ValidatedAction | ActionError`。人话：声明一个带类型的模块级变量。
- 第 177 行：`action_error_from_adapter_error` = `adapter_error_to_action_error`。人话：在模块级别准备一个后面会反复使用的值。
- 第 377-386 行：`__all__` = `['ActionContext', 'ActionValidationResult', 'PlayerActionLike', 'TableSnapshot', 'ValidatedAction', 'action_error_from_adapter_error', 'adapter_error_to_action_error', 'validate_action']`。人话：在模块级别准备一个后面会反复使用的值。

## 类 `PlayerActionLike`（第 31-39 行）

继承：`Protocol`。

源码说明：Duck-typed player action accepted by the validator.

人话：把一组相关数据和行为封装到一个类型里，供其他模块按统一接口使用。

字段/类变量：

- `player_id`：类型 `Identifier`。
- `seat_index`：类型 `int`。
- `hand_id`：类型 `Identifier`。
- `turn_id`：类型 `Identifier`。
- `action_type`：类型 `ActionType | str`。
- `amount`：类型 `int | None`。

## 类 `TableSnapshot`（第 42-45 行）

继承：`Protocol`。

源码说明：Minimal table snapshot surface used to resolve seats.

人话：把一组相关数据和行为封装到一个类型里，供其他模块按统一接口使用。

字段/类变量：

- `seat_to_player`：类型 `Mapping[int, Identifier]`。

## 类 `ActionContext`（第 49-71 行）

装饰器：`@dataclass(frozen=True, slots=True)`。

源码说明：Current server-owned action opportunity.

人话：把一组相关数据和行为封装到一个类型里，供其他模块按统一接口使用。

字段/类变量：

- `table_id`：类型 `Identifier`。
- `hand_id`：类型 `Identifier`。
- `turn_id`：类型 `Identifier`。
- `actor_player_id`：类型 `Identifier`。
- `actor_seat_index`：类型 `int`。

这个类里的方法：

### `__post_init__`（第 58-71 行）

签名：

```python
def __post_init__(self) -> None
```

人话：dataclass 创建对象后自动执行，用来做校验、标准化或补充字段。

关键代码块：

- 第 59 行：调用 `object.__setattr__`，执行一个有副作用或校验性质的动作。
- 第 60 行：调用 `object.__setattr__`，执行一个有副作用或校验性质的动作。
- 第 61 行：调用 `object.__setattr__`，执行一个有副作用或校验性质的动作。
- 第 62-66 行：调用 `object.__setattr__`，执行一个有副作用或校验性质的动作。
- 第 67-71 行：调用 `object.__setattr__`，执行一个有副作用或校验性质的动作。

## 类 `ValidatedAction`（第 75-81 行）

装饰器：`@dataclass(frozen=True, slots=True)`。

源码说明：Action accepted by the platform validator.

人话：校验输入或状态是否合法，发现问题时返回错误或抛出异常。

字段/类变量：

- `action`：类型 `PlayerAction | PlayerActionLike | Mapping[str, Any]`。
- `normalized_type`：类型 `ActionType`。
- `normalized_amount`：类型 `int | None`。
- `validation_source`：类型 `ValidationSource`，默认值 `'platform'`。

## 模块级函数

### `validate_action`（第 87-149 行）

签名：

```python
def validate_action(action: PlayerAction | PlayerActionLike | Mapping[str, Any], context: ActionContext, legal_actions: LegalActionSet | Iterable[Any] | Mapping[str, Any] | Any, table_snapshot: TableSnapshot | Mapping[str, Any] | Any) -> ActionValidationResult
```

源码说明：Validate a submitted action without mutating state or calling the adapter.

人话：校验输入或状态是否合法，发现问题时返回错误或抛出异常。

关键代码块：

- 第 95 行：给 `player_id` 赋值，准备后面逻辑要用的数据。
- 第 96 行：给 `seat_index` 赋值，准备后面逻辑要用的数据。
- 第 97 行：给 `hand_id` 赋值，准备后面逻辑要用的数据。
- 第 98 行：给 `turn_id` 赋值，准备后面逻辑要用的数据。
- 第 99 行：给 `raw_action_type` 赋值，准备后面逻辑要用的数据。
- 第 100 行：给 `amount` 赋值，准备后面逻辑要用的数据。
- 第 102-103 行：根据条件 `hand_id != context.hand_id` 分支处理不同情况。
- 第 105-106 行：根据条件 `turn_id != context.turn_id` 分支处理不同情况。
- 第 108-109 行：根据条件 `not _is_non_bool_int(seat_index) or _seated_player(table_snapshot, seat_index) != player_id` 分支处理不同情况。
- 第 111-112 行：根据条件 `seat_index != context.actor_seat_index or player_id != context.actor_player_id` 分支处理不同情况。
- 第 114 行：给 `action_type` 赋值，准备后面逻辑要用的数据。
- 第 115-116 行：根据条件 `action_type is None` 分支处理不同情况。
- 第 118 行：给 `legal_action` 赋值，准备后面逻辑要用的数据。
- 第 119-120 行：根据条件 `legal_action is None or not _legal_action_enabled(legal_action)` 分支处理不同情况。
- 第 122-137 行：根据条件 `action_type is ActionType.RAISE_TO` 分支处理不同情况。
- 第 139-140 行：根据条件 `amount is not None` 分支处理不同情况。
- 后面还有 2 个语句块，主要继续完成这个函数的收尾、返回或异常处理。

### `adapter_error_to_action_error`（第 152-174 行）

签名：

```python
def adapter_error_to_action_error(adapter_error: BaseException | Mapping[str, Any] | Any, action: PlayerAction | PlayerActionLike | Mapping[str, Any] | None = None) -> ActionError
```

源码说明：Convert an adapter action rejection into the same ActionError shape.

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 158 行：给 `error_payload` 赋值，准备后面逻辑要用的数据。
- 第 159 行：给 `code` 赋值，准备后面逻辑要用的数据。
- 第 160 行：给 `message` 赋值，准备后面逻辑要用的数据。
- 第 162-163 行：根据条件 `not isinstance(code, str) or not code` 分支处理不同情况。
- 第 164-165 行：根据条件 `not isinstance(message, str) or not message` 分支处理不同情况。
- 第 167-174 行：返回计算结果，把这个函数的最终答案交给调用者。

### `_action_error`（第 180-191 行）

签名：

```python
def _action_error(code: str, action: PlayerAction | PlayerActionLike | Mapping[str, Any]) -> ActionError
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 184-191 行：返回计算结果，把这个函数的最终答案交给调用者。

### `_find_legal_action`（第 194-206 行）

签名：

```python
def _find_legal_action(legal_actions: Any, action_type: ActionType) -> Any | None
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 195-196 行：根据条件 `isinstance(legal_actions, LegalActionSet)` 分支处理不同情况。
- 第 198 行：给 `boundary` 赋值，准备后面逻辑要用的数据。
- 第 199-200 行：根据条件 `boundary is not None` 分支处理不同情况。
- 第 202-205 行：循环遍历 `_iter_legal_actions(legal_actions)`，逐个处理里面的元素。
- 第 206 行：返回计算结果，把这个函数的最终答案交给调用者。

### `_boundary_action`（第 209-228 行）

签名：

```python
def _boundary_action(legal_actions: Any, action_type: ActionType) -> Any | None
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 210-216 行：给 `attr_by_type` 赋值，准备后面逻辑要用的数据。
- 第 217 行：给 `attr` 赋值，准备后面逻辑要用的数据。
- 第 219-226 行：根据条件 `isinstance(legal_actions, Mapping)` 分支处理不同情况。
- 第 228 行：返回计算结果，把这个函数的最终答案交给调用者。

### `_iter_legal_actions`（第 231-248 行）

签名：

```python
def _iter_legal_actions(legal_actions: Any) -> Iterable[Any]
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 232-236 行：根据条件 `isinstance(legal_actions, Mapping)` 分支处理不同情况。
- 第 238 行：给 `actions_attr` 赋值，准备后面逻辑要用的数据。
- 第 239-240 行：根据条件 `actions_attr is not None and (not isinstance(actions_attr, str | bytes))` 分支处理不同情况。
- 第 242-243 行：根据条件 `isinstance(legal_actions, str | bytes)` 分支处理不同情况。
- 第 245-248 行：尝试执行可能失败的操作，并在异常发生时转成项目自己的处理方式。

### `_legal_action_enabled`（第 251-253 行）

签名：

```python
def _legal_action_enabled(legal_action: Any) -> bool
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 252 行：给 `enabled` 赋值，准备后面逻辑要用的数据。
- 第 253 行：返回计算结果，把这个函数的最终答案交给调用者。

### `_check_call_amount_semantics`（第 256-266 行）

签名：

```python
def _check_call_amount_semantics(action_type: ActionType, legal_action: Any) -> bool
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 257 行：给 `fixed` 赋值，准备后面逻辑要用的数据。
- 第 258-259 行：根据条件 `fixed is None` 分支处理不同情况。
- 第 260-261 行：根据条件 `not _is_non_bool_int(fixed)` 分支处理不同情况。
- 第 262-263 行：根据条件 `action_type is ActionType.CHECK` 分支处理不同情况。
- 第 264-265 行：根据条件 `action_type is ActionType.CALL` 分支处理不同情况。
- 第 266 行：返回计算结果，把这个函数的最终答案交给调用者。

### `_seated_player`（第 269-286 行）

签名：

```python
def _seated_player(table_snapshot: Any, seat_index: int) -> Identifier | None
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 270 行：给 `seat_to_player` 赋值，准备后面逻辑要用的数据。
- 第 271-272 行：根据条件 `isinstance(seat_to_player, Mapping)` 分支处理不同情况。
- 第 274-277 行：循环遍历 `('players_by_seat', 'seat_players', 'player_by_seat')`，逐个处理里面的元素。
- 第 279 行：给 `seats` 赋值，准备后面逻辑要用的数据。
- 第 280-281 行：根据条件 `seats is None or isinstance(seats, Mapping | str | bytes)` 分支处理不同情况。
- 第 283-285 行：循环遍历 `seats`，逐个处理里面的元素。
- 第 286 行：返回计算结果，把这个函数的最终答案交给调用者。

### `_lookup_seat_mapping`（第 289-295 行）

签名：

```python
def _lookup_seat_mapping(seat_to_player: Mapping[Any, Any], seat_index: int) -> Identifier | None
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 290-291 行：根据条件 `seat_index in seat_to_player` 分支处理不同情况。
- 第 292 行：给 `string_key` 赋值，准备后面逻辑要用的数据。
- 第 293-294 行：根据条件 `string_key in seat_to_player` 分支处理不同情况。
- 第 295 行：返回计算结果，把这个函数的最终答案交给调用者。

### `_normalize_action_type`（第 298-308 行）

签名：

```python
def _normalize_action_type(value: Any) -> ActionType | None
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 299-300 行：根据条件 `isinstance(value, ActionType)` 分支处理不同情况。
- 第 301-302 行：根据条件 `hasattr(value, 'value')` 分支处理不同情况。
- 第 303-307 行：根据条件 `isinstance(value, str)` 分支处理不同情况。
- 第 308 行：返回计算结果，把这个函数的最终答案交给调用者。

### `_error_payload`（第 311-321 行）

签名：

```python
def _error_payload(adapter_error: BaseException | Mapping[str, Any] | Any) -> Any
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 312-313 行：根据条件 `isinstance(adapter_error, Mapping)` 分支处理不同情况。
- 第 315 行：给 `to_dict` 赋值，准备后面逻辑要用的数据。
- 第 316-319 行：根据条件 `callable(to_dict)` 分支处理不同情况。
- 第 321 行：返回计算结果，把这个函数的最终答案交给调用者。

### `_error_identifier`（第 324-332 行）

签名：

```python
def _error_identifier(adapter_error: Any, action: PlayerAction | PlayerActionLike | Mapping[str, Any] | None, field_name: str) -> Identifier | None
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 329 行：给 `value` 赋值，准备后面逻辑要用的数据。
- 第 330-331 行：根据条件 `value is not None or action is None` 分支处理不同情况。
- 第 332 行：返回计算结果，把这个函数的最终答案交给调用者。

### `_read_field`（第 335-338 行）

签名：

```python
def _read_field(source: Any, field_name: str, default: Any = None) -> Any
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 336-337 行：根据条件 `isinstance(source, Mapping)` 分支处理不同情况。
- 第 338 行：返回计算结果，把这个函数的最终答案交给调用者。

### `_validate_identifier`（第 341-348 行）

签名：

```python
def _validate_identifier(value: Any, field_name: str) -> Identifier
```

人话：校验输入或状态是否合法，发现问题时返回错误或抛出异常。

关键代码块：

- 第 342-343 行：根据条件 `isinstance(value, bool) or value is None` 分支处理不同情况。
- 第 344-345 行：根据条件 `isinstance(value, int)` 分支处理不同情况。
- 第 346-347 行：根据条件 `isinstance(value, str) and value` 分支处理不同情况。
- 第 348 行：主动抛出错误，表示传入数据或当前状态不符合要求。

### `_optional_identifier`（第 351-358 行）

签名：

```python
def _optional_identifier(value: Any) -> Identifier | None
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 352-353 行：根据条件 `isinstance(value, bool) or value is None` 分支处理不同情况。
- 第 354-355 行：根据条件 `isinstance(value, int)` 分支处理不同情况。
- 第 356-357 行：根据条件 `isinstance(value, str) and value` 分支处理不同情况。
- 第 358 行：返回计算结果，把这个函数的最终答案交给调用者。

### `_validate_seat_index`（第 361-364 行）

签名：

```python
def _validate_seat_index(value: Any) -> int
```

人话：校验输入或状态是否合法，发现问题时返回错误或抛出异常。

关键代码块：

- 第 362-363 行：根据条件 `not _is_non_bool_int(value) or value < 0` 分支处理不同情况。
- 第 364 行：返回计算结果，把这个函数的最终答案交给调用者。

### `_is_non_bool_int`（第 367-368 行）

签名：

```python
def _is_non_bool_int(value: Any) -> bool
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 368 行：返回计算结果，把这个函数的最终答案交给调用者。

### `_optional_int`（第 371-374 行）

签名：

```python
def _optional_int(value: Any) -> int | None
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 372-373 行：根据条件 `_is_non_bool_int(value)` 分支处理不同情况。
- 第 374 行：返回计算结果，把这个函数的最终答案交给调用者。

## 对外公开接口

`__all__` 声明这个模块希望别人主要使用这些名字：

- `ActionContext`
- `ActionValidationResult`
- `PlayerActionLike`
- `TableSnapshot`
- `ValidatedAction`
- `action_error_from_adapter_error`
- `adapter_error_to_action_error`
- `validate_action`

## 初学者阅读建议

先看“这个文件是干什么的”，再看类和函数标题。遇到以下划线开头的函数，可以先理解成内部工具；遇到 `to_dict/from_dict/to_json/from_json`，重点记住它们是在对象、字典和 JSON 之间转换。
