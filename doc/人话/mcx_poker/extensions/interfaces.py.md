# `mcx_poker/extensions/interfaces.py` 人话讲解

源文件：`/Users/machengqi/Documents/mcx-poker/src/mcx_poker/extensions/interfaces.py`

## 这个文件是干什么的

源码说明：Future extension interface boundaries for mcx-poker.

The MVP intentionally keeps LLM players, solver integration, coach pages,
statistics databases, network calls, and PokerKit objects out of this module.
Future extensions consume only platform DTOs such as observations, table
snapshots, public hand events, and persisted hand-review inputs.

人话概括：

定义扩展接口，让外部策略、LLM 或未来插件能按统一格式接入。

## 导入区

- 第 9 行：从 `__future__` 导入 `annotations`。
- 第 11 行：从 `collections.abc` 导入 `Mapping, Sequence`。
- 第 12 行：从 `dataclasses` 导入 `dataclass, field, fields, is_dataclass, replace`。
- 第 13 行：从 `enum` 导入 `Enum, StrEnum`。
- 第 14 行：从 `typing` 导入 `Any, Protocol, runtime_checkable`。

人话：导入区是在声明“这个文件需要哪些外部工具”。标准库通常提供基础能力，项目内导入则说明它依赖哪些业务模块。

## 顶层常量和类型

- 第 16-22 行：`MVP_EXCLUSIONS`: `tuple[str, ...]` = `('real_llm_player', 'real_solver', 'coach_page', 'statistics_database', 'network_dependency')`。人话：声明一个带类型的模块级变量。
- 第 25-30 行：`ALLOWED_EXTENSION_INPUT_TYPES`: `tuple[str, ...]` = `('PlayerObservation', 'TableSnapshot', 'HandEvent', 'HandReviewInput')`。人话：声明一个带类型的模块级变量。
- 第 33-36 行：`REPLAY_HAND_HISTORY_REQUIREMENT` = `'Replay depends on persisted Hand History; the temporary hand event log is not a cross-restart replay source.'`。人话：在模块级别准备一个后面会反复使用的值。
- 第 38-54 行：`_FORBIDDEN_INPUT_KEYS` = `frozenset({'all_hole_cards', 'controller_private_state', 'deck', 'deck_order', 'future_cards', 'hole_cards_by_player', 'opponent_hole_cards', 'pokerkit_state', 'private_controller_state', 'raw_pokerkit_state', 'raw_state', 'undealt_cards', 'unshown_hole_cards'})`。人话：在模块级别准备一个后面会反复使用的值。
- 第 739-782 行：`__all__` = `['ALLOWED_EXTENSION_INPUT_TYPES', 'MVP_EXCLUSIONS', 'REPLAY_HAND_HISTORY_REQUIREMENT', 'ActionRequestContext', 'ActionType', 'BaseFutureController', 'CoachFeedback', 'ControllerRegistry', 'DecisionAnalyzer', 'DecisionAssessment', 'DeterministicLLMClient', 'ExtensionInputRejected', 'ExtensionInterfaceError', 'GTOPlayerController', 'HandEvent', 'HandReviewInput', 'LLMActionParser', 'LLMClient', 'LLMInputBuilder', 'LLMPlayerController', 'LeakDetector', 'LegalAction', 'NoLegalActionAvailable', 'NoopSolverClient', 'ObservationLLMInputBuilder', 'ObservationStrategyQueryBuilder', 'PlatformDTO', 'PlayerAction', 'PlayerController', 'PlayerObservation', 'SimpleLLMActionParser', 'SolverClient', 'StrategyQuery', 'StrategyQueryBuilder', 'StrategyResult', 'TableSnapshot', 'VisibleSeat', 'action_from_observation', 'first_enabled_legal_action', 'normalize_action_type', 'parse_action_text', 'validate_extension_input']`。人话：在模块级别准备一个后面会反复使用的值。

## 类 `ExtensionInterfaceError`（第 57-58 行）

继承：`ValueError`。

源码说明：Base error for invalid extension boundary use.

人话：把一组相关数据和行为封装到一个类型里，供其他模块按统一接口使用。

## 类 `ExtensionInputRejected`（第 61-62 行）

继承：`ExtensionInterfaceError`。

源码说明：Raised when a value attempts to cross the extension boundary unsafely.

人话：把一组相关数据和行为封装到一个类型里，供其他模块按统一接口使用。

## 类 `NoLegalActionAvailable`（第 65-66 行）

继承：`ExtensionInterfaceError`。

源码说明：Raised when an actionable observation has no enabled platform action.

人话：把一组相关数据和行为封装到一个类型里，供其他模块按统一接口使用。

## 类 `ActionType`（第 69-76 行）

继承：`StrEnum`。

源码说明：Platform action semantics shared by humans, bots, and future agents.

人话：把一组相关数据和行为封装到一个类型里，供其他模块按统一接口使用。

字段/类变量：

- `FOLD`：类级变量，值 `'Fold'`。
- `CHECK`：类级变量，值 `'Check'`。
- `CALL`：类级变量，值 `'Call'`。
- `RAISE_TO`：类级变量，值 `'RaiseTo'`。
- `ALL_IN`：类级变量，值 `'AllIn'`。

## 类 `PlatformDTO`（第 79-88 行）

源码说明：Marker base for DTOs that are safe to pass into extension interfaces.

人话：把一组相关数据和行为封装到一个类型里，供其他模块按统一接口使用。

这个类里的方法：

### `to_extension_payload`（第 82-88 行）

签名：

```python
def to_extension_payload(self) -> dict[str, Any]
```

源码说明：Return a JSON-compatible payload after hidden-information checks.

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 85 行：给 `payload` 赋值，准备后面逻辑要用的数据。
- 第 86-87 行：根据条件 `not isinstance(payload, dict)` 分支处理不同情况。
- 第 88 行：返回计算结果，把这个函数的最终答案交给调用者。

## 类 `LegalAction`（第 92-103 行）

装饰器：`@dataclass(frozen=True)`。

继承：`PlatformDTO`。

源码说明：Visible legal-action description exposed by the Observation System.

人话：把一组相关数据和行为封装到一个类型里，供其他模块按统一接口使用。

字段/类变量：

- `action_type`：类型 `ActionType | str`。
- `enabled`：类型 `bool`，默认值 `True`。
- `amount_min`：类型 `int | None`，默认值 `None`。
- `amount_max`：类型 `int | None`，默认值 `None`。
- `amount_fixed`：类型 `int | None`，默认值 `None`。
- `reason_if_disabled`：类型 `str | None`，默认值 `None`。

这个类里的方法：

### `__post_init__`（第 102-103 行）

签名：

```python
def __post_init__(self) -> None
```

人话：dataclass 创建对象后自动执行，用来做校验、标准化或补充字段。

关键代码块：

- 第 103 行：调用 `object.__setattr__`，执行一个有副作用或校验性质的动作。

## 类 `PlayerAction`（第 107-124 行）

装饰器：`@dataclass(frozen=True)`。

继承：`PlatformDTO`。

源码说明：Platform action returned by a controller implementation.

人话：把一组相关数据和行为封装到一个类型里，供其他模块按统一接口使用。

字段/类变量：

- `player_id`：类型 `str`。
- `seat_index`：类型 `int`。
- `hand_id`：类型 `str`。
- `turn_id`：类型 `str`。
- `action_type`：类型 `ActionType | str`。
- `amount`：类型 `int | None`，默认值 `None`。
- `source`：类型 `str`，默认值 `'future_agent'`。

这个类里的方法：

### `__post_init__`（第 118-124 行）

签名：

```python
def __post_init__(self) -> None
```

人话：dataclass 创建对象后自动执行，用来做校验、标准化或补充字段。

关键代码块：

- 第 119 行：给 `action_type` 赋值，准备后面逻辑要用的数据。
- 第 120 行：调用 `object.__setattr__`，执行一个有副作用或校验性质的动作。
- 第 121-122 行：根据条件 `action_type is ActionType.RAISE_TO and self.amount is None` 分支处理不同情况。
- 第 123-124 行：根据条件 `action_type is not ActionType.RAISE_TO and self.amount is not None` 分支处理不同情况。

## 类 `VisibleSeat`（第 128-143 行）

装饰器：`@dataclass(frozen=True)`。

继承：`PlatformDTO`。

源码说明：Seat state visible to the observing player.

人话：把一组相关数据和行为封装到一个类型里，供其他模块按统一接口使用。

字段/类变量：

- `seat_index`：类型 `int`。
- `player_id`：类型 `str | None`，默认值 `None`。
- `player_name`：类型 `str | None`，默认值 `None`。
- `stack`：类型 `int`，默认值 `0`。
- `current_bet`：类型 `int`，默认值 `0`。
- `status`：类型 `str`，默认值 `'empty'`。
- `hole_card_count`：类型 `int`，默认值 `0`。
- `shown_cards`：类型 `tuple[str, ...]`，默认值 `()`。

这个类里的方法：

### `__post_init__`（第 140-143 行）

签名：

```python
def __post_init__(self) -> None
```

人话：dataclass 创建对象后自动执行，用来做校验、标准化或补充字段。

关键代码块：

- 第 141 行：调用 `object.__setattr__`，执行一个有副作用或校验性质的动作。
- 第 142-143 行：根据条件 `self.hole_card_count < 0` 分支处理不同情况。

## 类 `HandEvent`（第 147-159 行）

装饰器：`@dataclass(frozen=True)`。

继承：`PlatformDTO`。

源码说明：Public hand event suitable for extension inputs and future replay.

人话：把一组相关数据和行为封装到一个类型里，供其他模块按统一接口使用。

字段/类变量：

- `event_id`：类型 `str`。
- `hand_id`：类型 `str`。
- `event_type`：类型 `str`。
- `payload`：类型 `Mapping[str, Any]`，默认值 `field(default_factory=dict)`。
- `public`：类型 `bool`，默认值 `True`。

这个类里的方法：

### `__post_init__`（第 156-159 行）

签名：

```python
def __post_init__(self) -> None
```

人话：dataclass 创建对象后自动执行，用来做校验、标准化或补充字段。

关键代码块：

- 第 157-158 行：根据条件 `not self.public` 分支处理不同情况。
- 第 159 行：调用 `validate_extension_input`，执行一个有副作用或校验性质的动作。

## 类 `TableSnapshot`（第 163-175 行）

装饰器：`@dataclass(frozen=True)`。

继承：`PlatformDTO`。

源码说明：Platform-level table snapshot; it is not a PokerKit state object.

人话：把一组相关数据和行为封装到一个类型里，供其他模块按统一接口使用。

字段/类变量：

- `table_id`：类型 `str`。
- `hand_id`：类型 `str | None`。
- `button_seat_index`：类型 `int`。
- `visible_seats`：类型 `tuple[VisibleSeat, ...]`。
- `board_cards`：类型 `tuple[str, ...]`，默认值 `()`。
- `pot_summary`：类型 `Mapping[str, int]`，默认值 `field(default_factory=dict)`。

这个类里的方法：

### `__post_init__`（第 173-175 行）

签名：

```python
def __post_init__(self) -> None
```

人话：dataclass 创建对象后自动执行，用来做校验、标准化或补充字段。

关键代码块：

- 第 174 行：调用 `object.__setattr__`，执行一个有副作用或校验性质的动作。
- 第 175 行：调用 `object.__setattr__`，执行一个有副作用或校验性质的动作。

## 类 `PlayerObservation`（第 179-210 行）

装饰器：`@dataclass(frozen=True)`。

继承：`PlatformDTO`。

源码说明：Per-player platform observation passed to controllers and agents.

This DTO includes the observer's own hole cards and public cards only. It
has no field for undealt cards, PokerKit state, opponent unshown hole cards,
or controller-private state.

人话：把一组相关数据和行为封装到一个类型里，供其他模块按统一接口使用。

字段/类变量：

- `observer_player_id`：类型 `str`。
- `observer_seat_index`：类型 `int`。
- `table_id`：类型 `str`。
- `hand_id`：类型 `str`。
- `turn_id`：类型 `str`。
- `is_actor`：类型 `bool`。
- `button_seat_index`：类型 `int`。
- `own_hole_cards`：类型 `tuple[str, ...]`，默认值 `()`。
- `board_cards`：类型 `tuple[str, ...]`，默认值 `()`。
- `visible_seats`：类型 `tuple[VisibleSeat, ...]`，默认值 `()`。
- `pot_summary`：类型 `Mapping[str, int]`，默认值 `field(default_factory=dict)`。
- `bet_summary`：类型 `Mapping[str, int]`，默认值 `field(default_factory=dict)`。
- `visible_action_history`：类型 `tuple[HandEvent, ...]`，默认值 `()`。
- `legal_actions`：类型 `tuple[LegalAction, ...]`，默认值 `()`。

这个类里的方法：

### `__post_init__`（第 202-210 行）

签名：

```python
def __post_init__(self) -> None
```

人话：dataclass 创建对象后自动执行，用来做校验、标准化或补充字段。

关键代码块：

- 第 203 行：调用 `object.__setattr__`，执行一个有副作用或校验性质的动作。
- 第 204 行：调用 `object.__setattr__`，执行一个有副作用或校验性质的动作。
- 第 205 行：调用 `object.__setattr__`，执行一个有副作用或校验性质的动作。
- 第 206 行：调用 `object.__setattr__`，执行一个有副作用或校验性质的动作。
- 第 207 行：调用 `object.__setattr__`，执行一个有副作用或校验性质的动作。
- 第 208-210 行：循环遍历 `self.visible_action_history`，逐个处理里面的元素。

## 类 `HandReviewInput`（第 214-226 行）

装饰器：`@dataclass(frozen=True)`。

继承：`PlatformDTO`。

源码说明：Coach and analysis input built from Hand History or public events.

人话：把一组相关数据和行为封装到一个类型里，供其他模块按统一接口使用。

字段/类变量：

- `hand_id`：类型 `str`。
- `public_events`：类型 `tuple[HandEvent, ...]`，默认值 `()`。
- `persisted_hand_history_id`：类型 `str | None`，默认值 `None`。
- `table_snapshot`：类型 `TableSnapshot | None`，默认值 `None`。

这个类里的方法：

### `__post_init__`（第 222-226 行）

签名：

```python
def __post_init__(self) -> None
```

人话：dataclass 创建对象后自动执行，用来做校验、标准化或补充字段。

关键代码块：

- 第 223 行：调用 `object.__setattr__`，执行一个有副作用或校验性质的动作。
- 第 224-226 行：循环遍历 `self.public_events`，逐个处理里面的元素。

## 类 `ActionRequestContext`（第 230-237 行）

装饰器：`@dataclass(frozen=True)`。

继承：`PlatformDTO`。

源码说明：Context attached to a controller action request.

人话：把一组相关数据和行为封装到一个类型里，供其他模块按统一接口使用。

字段/类变量：

- `table_id`：类型 `str`。
- `hand_id`：类型 `str`。
- `turn_id`：类型 `str`。
- `player_id`：类型 `str`。
- `seat_index`：类型 `int`。

## 类 `PlayerController`（第 241-262 行）

装饰器：`@runtime_checkable`。

继承：`Protocol`。

源码说明：Controller boundary consumed by the Game Loop.

人话：把一组相关数据和行为封装到一个类型里，供其他模块按统一接口使用。

这个类里的方法：

### `request_action`（第 244-250 行）

签名：

```python
def request_action(self, observation: PlayerObservation, action_request_context: ActionRequestContext | None = None) -> PlayerAction
```

源码说明：Return one platform action for the supplied observation.

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 250 行：执行一个表达式，通常是调用函数或触发某个对象行为。

### `notify_action_rejected`（第 252-254 行）

签名：

```python
def notify_action_rejected(self, action_error: object) -> None
```

源码说明：Receive an action rejection notification from the platform.

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 254 行：执行一个表达式，通常是调用函数或触发某个对象行为。

### `notify_hand_started`（第 256-258 行）

签名：

```python
def notify_hand_started(self, hand_context: object) -> None
```

源码说明：Receive a hand-started notification.

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 258 行：执行一个表达式，通常是调用函数或触发某个对象行为。

### `notify_hand_ended`（第 260-262 行）

签名：

```python
def notify_hand_ended(self, result_summary: object) -> None
```

源码说明：Receive a hand-ended notification.

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 262 行：执行一个表达式，通常是调用函数或触发某个对象行为。

## 类 `BaseFutureController`（第 265-277 行）

源码说明：No-op lifecycle hooks shared by fake future controllers.

人话：把一组相关数据和行为封装到一个类型里，供其他模块按统一接口使用。

字段/类变量：

- `last_error`：类型 `Exception | None`。

这个类里的方法：

### `notify_action_rejected`（第 270-271 行）

签名：

```python
def notify_action_rejected(self, action_error: object) -> None
```

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 271 行：返回计算结果，把这个函数的最终答案交给调用者。

### `notify_hand_started`（第 273-274 行）

签名：

```python
def notify_hand_started(self, hand_context: object) -> None
```

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 274 行：返回计算结果，把这个函数的最终答案交给调用者。

### `notify_hand_ended`（第 276-277 行）

签名：

```python
def notify_hand_ended(self, result_summary: object) -> None
```

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 277 行：返回计算结果，把这个函数的最终答案交给调用者。

## 类 `ControllerRegistry`（第 280-303 行）

源码说明：Small registry used to verify future controller pluggability.

人话：把一组相关数据和行为封装到一个类型里，供其他模块按统一接口使用。

这个类里的方法：

### `__init__`（第 283-284 行）

签名：

```python
def __init__(self) -> None
```

人话：初始化对象，接收外部传入的数据并准备对象内部状态。

关键代码块：

- 第 284 行：声明字段或变量 `self._controllers`，类型是 `dict[str, PlayerController]`。

### `register`（第 286-289 行）

签名：

```python
def register(self, player_id: str, controller: PlayerController) -> None
```

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 287-288 行：根据条件 `not callable(getattr(controller, 'request_action', None))` 分支处理不同情况。
- 第 289 行：给 `self._controllers[player_id]` 赋值，准备后面逻辑要用的数据。

### `get`（第 291-295 行）

签名：

```python
def get(self, player_id: str) -> PlayerController
```

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 292-295 行：尝试执行可能失败的操作，并在异常发生时转成项目自己的处理方式。

### `request_action`（第 297-303 行）

签名：

```python
def request_action(self, player_id: str, observation: PlayerObservation, action_request_context: ActionRequestContext | None = None) -> PlayerAction
```

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 303 行：返回计算结果，把这个函数的最终答案交给调用者。

## 类 `LLMInputBuilder`（第 306-311 行）

继承：`Protocol`。

源码说明：Draft interface for converting an observation into model input.

人话：根据已有状态组装更高层的数据对象。

这个类里的方法：

### `build_input`（第 309-311 行）

签名：

```python
def build_input(self, observation: PlayerObservation) -> Mapping[str, Any]
```

源码说明：Build structured input from a platform observation.

人话：根据已有状态组装更高层的数据对象。

关键代码块：

- 第 311 行：执行一个表达式，通常是调用函数或触发某个对象行为。

## 类 `LLMClient`（第 314-323 行）

继承：`Protocol`。

源码说明：Draft interface for a future model client.

Implementations must not require API keys, SDKs, or network calls in the
MVP. The fake implementation below is deterministic and local.

人话：把一组相关数据和行为封装到一个类型里，供其他模块按统一接口使用。

这个类里的方法：

### `complete`（第 321-323 行）

签名：

```python
def complete(self, structured_input: Mapping[str, Any]) -> str
```

源码说明：Return a model-like action string.

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 323 行：执行一个表达式，通常是调用函数或触发某个对象行为。

## 类 `LLMActionParser`（第 326-331 行）

继承：`Protocol`。

源码说明：Draft parser interface that converts model output to PlayerAction.

人话：把一组相关数据和行为封装到一个类型里，供其他模块按统一接口使用。

这个类里的方法：

### `parse_action`（第 329-331 行）

签名：

```python
def parse_action(self, model_output: str, observation: PlayerObservation) -> PlayerAction
```

源码说明：Parse model output into a platform action.

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 331 行：执行一个表达式，通常是调用函数或触发某个对象行为。

## 类 `ObservationLLMInputBuilder`（第 334-338 行）

源码说明：Local input builder that serializes only the safe observation payload.

人话：根据已有状态组装更高层的数据对象。

这个类里的方法：

### `build_input`（第 337-338 行）

签名：

```python
def build_input(self, observation: PlayerObservation) -> Mapping[str, Any]
```

人话：根据已有状态组装更高层的数据对象。

关键代码块：

- 第 338 行：返回计算结果，把这个函数的最终答案交给调用者。

## 类 `DeterministicLLMClient`（第 342-349 行）

装饰器：`@dataclass(frozen=True)`。

源码说明：Fake local LLM client used only for boundary tests.

人话：把一组相关数据和行为封装到一个类型里，供其他模块按统一接口使用。

字段/类变量：

- `output`：类型 `str`，默认值 `'Check'`。

这个类里的方法：

### `complete`（第 347-349 行）

签名：

```python
def complete(self, structured_input: Mapping[str, Any]) -> str
```

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 348 行：调用 `validate_extension_input`，执行一个有副作用或校验性质的动作。
- 第 349 行：返回计算结果，把这个函数的最终答案交给调用者。

## 类 `SimpleLLMActionParser`（第 352-362 行）

源码说明：Parser for the tiny deterministic fake model vocabulary.

人话：把一组相关数据和行为封装到一个类型里，供其他模块按统一接口使用。

这个类里的方法：

### `parse_action`（第 355-362 行）

签名：

```python
def parse_action(self, model_output: str, observation: PlayerObservation) -> PlayerAction
```

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 356 行：给 `(action_type, amount)` 赋值，准备后面逻辑要用的数据。
- 第 357-362 行：返回计算结果，把这个函数的最终答案交给调用者。

## 类 `LLMPlayerController`（第 365-397 行）

继承：`BaseFutureController`。

源码说明：Fake future LLM controller that needs no model dependency.

人话：把一组相关数据和行为封装到一个类型里，供其他模块按统一接口使用。

这个类里的方法：

### `__init__`（第 368-379 行）

签名：

```python
def __init__(self, input_builder: LLMInputBuilder | None = None, client: LLMClient | None = None, parser: LLMActionParser | None = None, source: str = 'future_agent') -> None
```

人话：初始化对象，接收外部传入的数据并准备对象内部状态。

关键代码块：

- 第 375 行：给 `self.input_builder` 赋值，准备后面逻辑要用的数据。
- 第 376 行：给 `self.client` 赋值，准备后面逻辑要用的数据。
- 第 377 行：给 `self.parser` 赋值，准备后面逻辑要用的数据。
- 第 378 行：给 `self.source` 赋值，准备后面逻辑要用的数据。
- 第 379 行：给 `self.last_error` 赋值，准备后面逻辑要用的数据。

### `request_action`（第 381-397 行）

签名：

```python
def request_action(self, observation: PlayerObservation, action_request_context: ActionRequestContext | None = None) -> PlayerAction
```

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 386 行：处理 `Delete` 语句。
- 第 387 行：调用 `validate_extension_input`，执行一个有副作用或校验性质的动作。
- 第 388-397 行：尝试执行可能失败的操作，并在异常发生时转成项目自己的处理方式。

## 类 `StrategyQuery`（第 401-417 行）

装饰器：`@dataclass(frozen=True)`。

继承：`PlatformDTO`。

源码说明：Platform-only strategy query for future solver or lookup layers.

人话：把一组相关数据和行为封装到一个类型里，供其他模块按统一接口使用。

字段/类变量：

- `table_id`：类型 `str`。
- `hand_id`：类型 `str`。
- `actor_player_id`：类型 `str`。
- `actor_seat_index`：类型 `int`。
- `board_cards`：类型 `tuple[str, ...]`。
- `pot_summary`：类型 `Mapping[str, int]`。
- `bet_summary`：类型 `Mapping[str, int]`。
- `legal_actions`：类型 `tuple[LegalAction, ...]`。
- `public_events`：类型 `tuple[HandEvent, ...]`，默认值 `()`。

这个类里的方法：

### `__post_init__`（第 414-417 行）

签名：

```python
def __post_init__(self) -> None
```

人话：dataclass 创建对象后自动执行，用来做校验、标准化或补充字段。

关键代码块：

- 第 415 行：调用 `object.__setattr__`，执行一个有副作用或校验性质的动作。
- 第 416 行：调用 `object.__setattr__`，执行一个有副作用或校验性质的动作。
- 第 417 行：调用 `object.__setattr__`，执行一个有副作用或校验性质的动作。

## 类 `StrategyQueryBuilder`（第 420-428 行）

继承：`Protocol`。

源码说明：Draft strategy-query builder consuming only platform DTOs.

人话：根据已有状态组装更高层的数据对象。

这个类里的方法：

### `build_query`（第 423-428 行）

签名：

```python
def build_query(self, source: PlayerObservation | TableSnapshot | HandReviewInput) -> StrategyQuery
```

源码说明：Build a strategy query from platform state or hand history input.

人话：根据已有状态组装更高层的数据对象。

关键代码块：

- 第 428 行：执行一个表达式，通常是调用函数或触发某个对象行为。

## 类 `SolverClient`（第 431-436 行）

继承：`Protocol`。

源码说明：Draft solver client interface with no solver dependency in the MVP.

人话：把一组相关数据和行为封装到一个类型里，供其他模块按统一接口使用。

这个类里的方法：

### `solve`（第 434-436 行）

签名：

```python
def solve(self, query: StrategyQuery) -> StrategyResult
```

源码说明：Return a strategy result for a platform-only query.

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 436 行：执行一个表达式，通常是调用函数或触发某个对象行为。

## 类 `StrategyResult`（第 440-456 行）

装饰器：`@dataclass(frozen=True)`。

继承：`PlatformDTO`。

源码说明：Future GTO result shape with optional frequencies and EVs.

人话：把一组相关数据和行为封装到一个类型里，供其他模块按统一接口使用。

字段/类变量：

- `recommended_action`：类型 `ActionType | str | None`，默认值 `None`。
- `recommended_amount`：类型 `int | None`，默认值 `None`。
- `action_frequencies`：类型 `Mapping[str, float]`，默认值 `field(default_factory=dict)`。
- `expected_values`：类型 `Mapping[str, float]`，默认值 `field(default_factory=dict)`。
- `notes`：类型 `tuple[str, ...]`，默认值 `()`。

这个类里的方法：

### `__post_init__`（第 449-456 行）

签名：

```python
def __post_init__(self) -> None
```

人话：dataclass 创建对象后自动执行，用来做校验、标准化或补充字段。

关键代码块：

- 第 450-455 行：根据条件 `self.recommended_action is not None` 分支处理不同情况。
- 第 456 行：调用 `object.__setattr__`，执行一个有副作用或校验性质的动作。

## 类 `ObservationStrategyQueryBuilder`（第 459-479 行）

源码说明：Build a solver query from a current player observation.

人话：根据已有状态组装更高层的数据对象。

这个类里的方法：

### `build_query`（第 462-479 行）

签名：

```python
def build_query(self, source: PlayerObservation | TableSnapshot | HandReviewInput) -> StrategyQuery
```

人话：根据已有状态组装更高层的数据对象。

关键代码块：

- 第 466-467 行：根据条件 `not isinstance(source, PlayerObservation)` 分支处理不同情况。
- 第 468 行：调用 `validate_extension_input`，执行一个有副作用或校验性质的动作。
- 第 469-479 行：返回计算结果，把这个函数的最终答案交给调用者。

## 类 `NoopSolverClient`（第 482-488 行）

源码说明：Fake local solver that recommends the first enabled fallback action.

人话：把一组相关数据和行为封装到一个类型里，供其他模块按统一接口使用。

这个类里的方法：

### `solve`（第 485-488 行）

签名：

```python
def solve(self, query: StrategyQuery) -> StrategyResult
```

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 486 行：调用 `validate_extension_input`，执行一个有副作用或校验性质的动作。
- 第 487 行：给 `legal_action` 赋值，准备后面逻辑要用的数据。
- 第 488 行：返回计算结果，把这个函数的最终答案交给调用者。

## 类 `GTOPlayerController`（第 491-525 行）

继承：`BaseFutureController`。

源码说明：Fake GTO controller that falls back if the solver boundary fails.

人话：把一组相关数据和行为封装到一个类型里，供其他模块按统一接口使用。

这个类里的方法：

### `__init__`（第 494-503 行）

签名：

```python
def __init__(self, query_builder: StrategyQueryBuilder | None = None, solver_client: SolverClient | None = None, source: str = 'future_agent') -> None
```

人话：初始化对象，接收外部传入的数据并准备对象内部状态。

关键代码块：

- 第 500 行：给 `self.query_builder` 赋值，准备后面逻辑要用的数据。
- 第 501 行：给 `self.solver_client` 赋值，准备后面逻辑要用的数据。
- 第 502 行：给 `self.source` 赋值，准备后面逻辑要用的数据。
- 第 503 行：给 `self.last_error` 赋值，准备后面逻辑要用的数据。

### `request_action`（第 505-525 行）

签名：

```python
def request_action(self, observation: PlayerObservation, action_request_context: ActionRequestContext | None = None) -> PlayerAction
```

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 510 行：处理 `Delete` 语句。
- 第 511 行：调用 `validate_extension_input`，执行一个有副作用或校验性质的动作。
- 第 512-525 行：尝试执行可能失败的操作，并在异常发生时转成项目自己的处理方式。

## 类 `DecisionAssessment`（第 529-540 行）

装饰器：`@dataclass(frozen=True)`。

继承：`PlatformDTO`。

源码说明：Draft analysis result for one public decision point.

人话：把一组相关数据和行为封装到一个类型里，供其他模块按统一接口使用。

字段/类变量：

- `hand_id`：类型 `str`。
- `turn_id`：类型 `str`。
- `player_id`：类型 `str`。
- `action_taken`：类型 `ActionType | str`。
- `notes`：类型 `tuple[str, ...]`，默认值 `()`。

这个类里的方法：

### `__post_init__`（第 538-540 行）

签名：

```python
def __post_init__(self) -> None
```

人话：dataclass 创建对象后自动执行，用来做校验、标准化或补充字段。

关键代码块：

- 第 539 行：调用 `object.__setattr__`，执行一个有副作用或校验性质的动作。
- 第 540 行：调用 `object.__setattr__`，执行一个有副作用或校验性质的动作。

## 类 `CoachFeedback`（第 544-557 行）

装饰器：`@dataclass(frozen=True)`。

继承：`PlatformDTO`。

源码说明：Future coach feedback DTO; no coach page is implemented in the MVP.

人话：把一组相关数据和行为封装到一个类型里，供其他模块按统一接口使用。

字段/类变量：

- `feedback_id`：类型 `str`。
- `player_id`：类型 `str`。
- `severity`：类型 `str`。
- `message`：类型 `str`。
- `training_focus`：类型 `str | None`，默认值 `None`。
- `related_hand_ids`：类型 `tuple[str, ...]`，默认值 `()`。
- `metadata`：类型 `Mapping[str, Any]`，默认值 `field(default_factory=dict)`。

这个类里的方法：

### `__post_init__`（第 555-557 行）

签名：

```python
def __post_init__(self) -> None
```

人话：dataclass 创建对象后自动执行，用来做校验、标准化或补充字段。

关键代码块：

- 第 556 行：调用 `object.__setattr__`，执行一个有副作用或校验性质的动作。
- 第 557 行：调用 `validate_extension_input`，执行一个有副作用或校验性质的动作。

## 类 `DecisionAnalyzer`（第 560-565 行）

继承：`Protocol`。

源码说明：Draft interface for future hand-review decision analysis.

人话：把一组相关数据和行为封装到一个类型里，供其他模块按统一接口使用。

这个类里的方法：

### `analyze`（第 563-565 行）

签名：

```python
def analyze(self, review_input: HandReviewInput) -> tuple[DecisionAssessment, ...]
```

源码说明：Analyze public hand-review input into decision assessments.

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 565 行：执行一个表达式，通常是调用函数或触发某个对象行为。

## 类 `LeakDetector`（第 568-577 行）

继承：`Protocol`。

源码说明：Draft interface for future leak detection.

人话：把一组相关数据和行为封装到一个类型里，供其他模块按统一接口使用。

这个类里的方法：

### `detect_leaks`（第 571-577 行）

签名：

```python
def detect_leaks(self, review_input: HandReviewInput, decisions: Sequence[DecisionAssessment]) -> tuple[CoachFeedback, ...]
```

源码说明：Detect stable error patterns from public review inputs.

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 577 行：执行一个表达式，通常是调用函数或触发某个对象行为。

## 模块级函数

### `normalize_action_type`（第 580-597 行）

签名：

```python
def normalize_action_type(action_type: ActionType | str) -> ActionType
```

源码说明：Normalize action type spelling used by draft extension fakes.

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 583-584 行：根据条件 `isinstance(action_type, ActionType)` 分支处理不同情况。
- 第 585 行：给 `token` 赋值，准备后面逻辑要用的数据。
- 第 586-593 行：给 `aliases` 赋值，准备后面逻辑要用的数据。
- 第 594-597 行：尝试执行可能失败的操作，并在异常发生时转成项目自己的处理方式。

### `parse_action_text`（第 600-611 行）

签名：

```python
def parse_action_text(text: str) -> tuple[ActionType, int | None]
```

源码说明：Parse fake LLM action text such as ``Check`` or ``RaiseTo(120)``.

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 603 行：给 `cleaned` 赋值，准备后面逻辑要用的数据。
- 第 604-607 行：根据条件 `'(' in cleaned and cleaned.endswith(')')` 分支处理不同情况。
- 第 608-610 行：根据条件 `':' in cleaned` 分支处理不同情况。
- 第 611 行：返回计算结果，把这个函数的最终答案交给调用者。

### `first_enabled_legal_action`（第 614-630 行）

签名：

```python
def first_enabled_legal_action(legal_actions: Sequence[LegalAction]) -> LegalAction
```

源码说明：Return the safest enabled action in deterministic fallback order.

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 617 行：给 `enabled` 赋值，准备后面逻辑要用的数据。
- 第 618-619 行：根据条件 `not enabled` 分支处理不同情况。
- 第 620-629 行：循环遍历 `(ActionType.CHECK, ActionType.CALL, ActionType.FOLD, ActionType.ALL_IN, ActionType.RAISE_TO)`，逐个处理里面的元素。
- 第 630 行：返回计算结果，把这个函数的最终答案交给调用者。

### `action_from_observation`（第 633-671 行）

签名：

```python
def action_from_observation(observation: PlayerObservation, requested_action: ActionType | str | None = None, requested_amount: int | None = None, source: str = 'future_agent') -> PlayerAction
```

源码说明：Build a legal platform action from an observation.

If the requested action is absent or disabled, the function chooses a local
deterministic fallback from the observation's legal action set.

人话：完成一个明确的小任务，供本模块或其他模块调用。

关键代码块：

- 第 645-661 行：根据条件 `requested_action is None` 分支处理不同情况。
- 第 662 行：给 `amount` 赋值，准备后面逻辑要用的数据。
- 第 663-671 行：返回计算结果，把这个函数的最终答案交给调用者。

### `validate_extension_input`（第 674-677 行）

签名：

```python
def validate_extension_input(value: object) -> None
```

源码说明：Reject PokerKit objects and hidden-information fields recursively.

人话：校验输入或状态是否合法，发现问题时返回错误或抛出异常。

关键代码块：

- 第 677 行：调用 `_to_serializable`，执行一个有副作用或校验性质的动作。

### `_amount_for_legal_action`（第 680-693 行）

签名：

```python
def _amount_for_legal_action(legal_action: LegalAction, requested_amount: int | None) -> int | None
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 684-685 行：根据条件 `legal_action.action_type is not ActionType.RAISE_TO` 分支处理不同情况。
- 第 686 行：给 `amount` 赋值，准备后面逻辑要用的数据。
- 第 687-688 行：根据条件 `amount is None` 分支处理不同情况。
- 第 689-690 行：根据条件 `legal_action.amount_min is not None and amount < legal_action.amount_min` 分支处理不同情况。
- 第 691-692 行：根据条件 `legal_action.amount_max is not None and amount > legal_action.amount_max` 分支处理不同情况。
- 第 693 行：返回计算结果，把这个函数的最终答案交给调用者。

### `_to_serializable`（第 696-724 行）

签名：

```python
def _to_serializable(value: object, path: tuple[str, ...]) -> object
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 697-698 行：根据条件 `_is_pokerkit_object(value)` 分支处理不同情况。
- 第 699-700 行：根据条件 `value is None or isinstance(value, str | int | float | bool)` 分支处理不同情况。
- 第 701-702 行：根据条件 `isinstance(value, Enum)` 分支处理不同情况。
- 第 703-709 行：根据条件 `isinstance(value, Mapping)` 分支处理不同情况。
- 第 710-719 行：根据条件 `is_dataclass(value)` 分支处理不同情况。
- 第 720-721 行：根据条件 `isinstance(value, Sequence) and (not isinstance(value, str | bytes | bytearray))` 分支处理不同情况。
- 第 722-724 行：主动抛出错误，表示传入数据或当前状态不符合要求。

### `_reject_forbidden_key`（第 727-731 行）

签名：

```python
def _reject_forbidden_key(key: str, path: tuple[str, ...]) -> None
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 728 行：给 `normalized` 赋值，准备后面逻辑要用的数据。
- 第 729-731 行：根据条件 `normalized in _FORBIDDEN_INPUT_KEYS or normalized.startswith('pokerkit_')` 分支处理不同情况。

### `_is_pokerkit_object`（第 734-736 行）

签名：

```python
def _is_pokerkit_object(value: object) -> bool
```

人话：内部辅助逻辑，主要服务当前模块，不是对外公开接口。

关键代码块：

- 第 735 行：给 `module` 赋值，准备后面逻辑要用的数据。
- 第 736 行：返回计算结果，把这个函数的最终答案交给调用者。

## 对外公开接口

`__all__` 声明这个模块希望别人主要使用这些名字：

- `ALLOWED_EXTENSION_INPUT_TYPES`
- `MVP_EXCLUSIONS`
- `REPLAY_HAND_HISTORY_REQUIREMENT`
- `ActionRequestContext`
- `ActionType`
- `BaseFutureController`
- `CoachFeedback`
- `ControllerRegistry`
- `DecisionAnalyzer`
- `DecisionAssessment`
- `DeterministicLLMClient`
- `ExtensionInputRejected`
- `ExtensionInterfaceError`
- `GTOPlayerController`
- `HandEvent`
- `HandReviewInput`
- `LLMActionParser`
- `LLMClient`
- `LLMInputBuilder`
- `LLMPlayerController`
- `LeakDetector`
- `LegalAction`
- `NoLegalActionAvailable`
- `NoopSolverClient`
- `ObservationLLMInputBuilder`
- `ObservationStrategyQueryBuilder`
- `PlatformDTO`
- `PlayerAction`
- `PlayerController`
- `PlayerObservation`
- `SimpleLLMActionParser`
- `SolverClient`
- `StrategyQuery`
- `StrategyQueryBuilder`
- `StrategyResult`
- `TableSnapshot`
- `VisibleSeat`
- `action_from_observation`
- `first_enabled_legal_action`
- `normalize_action_type`
- `parse_action_text`
- `validate_extension_input`

## 初学者阅读建议

先看“这个文件是干什么的”，再看类和函数标题。遇到以下划线开头的函数，可以先理解成内部工具；遇到 `to_dict/from_dict/to_json/from_json`，重点记住它们是在对象、字典和 JSON 之间转换。
