# `actions.py` 人话讲解

源文件：`/Users/machengqi/Documents/mcx-poker/src/mcx_poker/engine/actions.py`

这个文件做的事情很集中：定义“扑克平台里和玩家动作有关的数据格式”，并且保证这些数据格式是干净、合法、方便传输的。

你可以把它理解成一组“表格模板”：

- `PlayerAction`：某个玩家真的提交了一个动作，比如跟注、弃牌、加注到 120。
- `LegalAction`：当前轮到某个玩家时，系统告诉他“你现在可以做哪些动作”。
- `LegalActionSet`：一组 `LegalAction`。
- `ActionError`：玩家提交了不合法动作时，系统返回的错误。
- `ActionType`：动作类型清单。
- `ActionSource`：动作来源清单，比如人类、机器人。

这些类还有一个共同目标：可以在 Python 对象、字典、JSON 字符串之间互相转换。这样后端、前端、机器人控制器、WebSocket/API 都能用同一套格式说话。

## 1. 文件开头：说明和导入

```python
"""Platform action DTOs for table clients and controllers."""
```

这是文件说明。`DTO` 是 `Data Transfer Object` 的缩写，意思是“专门用来传递数据的对象”。它通常不负责真正的业务计算，只负责把数据包装成可靠的形状。

这里的 “table clients and controllers” 可以理解为：

- table clients：牌桌客户端，比如网页界面、WebSocket 连接方。
- controllers：控制玩家行为的模块，比如真人玩家控制器、机器人控制器。

```python
from __future__ import annotations
```

这行是 Python 的兼容性写法。它让类型注解延迟解析。简单说，它让代码里写类型时更灵活，尤其是类还没完全定义完时也能在类型里引用它。

```python
import json
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Self, TypeVar
```

这些是后面会用到的工具：

- `json`：把 Python 字典转换成 JSON 字符串，或者把 JSON 字符串读回来。
- `Iterable`：表示“可以被循环遍历的东西”，比如列表、元组。
- `Mapping`：表示“像字典一样的东西”，能通过 key 取 value。
- `dataclass`：帮你快速定义“主要用来装数据的类”。
- `StrEnum`：一种枚举类型，枚举值本身也是字符串。
- `Any`：任意类型。
- `Self`：表示“当前这个类自身的类型”。
- `TypeVar`：定义泛型类型变量，给辅助函数用。

## 2. 类型别名

```python
Identifier = str | int
EnumT = TypeVar("EnumT", bound=StrEnum)
```

`Identifier = str | int` 是一个类型别名。它的意思是：项目里的各种 ID，可以是字符串，也可以是整数。

例如这些都可以：

```python
player_id = "player-1"
hand_id = "hand-abc"
turn_id = 123
```

但这些不可以：

```python
player_id = None
player_id = True
player_id = ""
```

`EnumT = TypeVar("EnumT", bound=StrEnum)` 是给 `_parse_enum` 这个辅助函数用的。它的意思是：这个泛型类型必须是某种 `StrEnum`。

不用被这行吓到。你可以先把它理解成：“后面有个函数可以解析不同的字符串枚举，这行是在帮那个函数保留准确的类型信息。”

## 3. `ActionType`：玩家动作类型

```python
class ActionType(StrEnum):
    """Supported player action types."""

    FOLD = "Fold"
    CHECK = "Check"
    CALL = "Call"
    RAISE_TO = "RaiseTo"
    ALL_IN = "AllIn"
```

这是一个枚举。枚举就是“固定选项清单”。

这里定义了平台支持的 5 种玩家动作：

- `FOLD = "Fold"`：弃牌。
- `CHECK = "Check"`：过牌。
- `CALL = "Call"`：跟注。
- `RAISE_TO = "RaiseTo"`：加注到某个总额。
- `ALL_IN = "AllIn"`：全下。

为什么不用普通字符串？

如果代码里到处手写 `"Fold"`、`"Call"`，很容易拼错，比如写成 `"foldd"`。枚举能让代码更稳定，也更容易被编辑器和测试发现错误。

因为它继承自 `StrEnum`，所以它既是枚举，又能像字符串一样序列化成 `"Fold"` 这种值。

## 4. `ActionSource`：动作来源

```python
class ActionSource(StrEnum):
    """Diagnostic source marker for submitted actions."""

    HUMAN = "human"
    BOT = "bot"
    FUTURE_AGENT = "future_agent"
    UNKNOWN = "unknown"
```

这也是一个枚举，用来标记动作从哪里来：

- `HUMAN`：真人玩家。
- `BOT`：机器人。
- `FUTURE_AGENT`：未来可能接入的智能代理。
- `UNKNOWN`：不知道来源。

注释里说它是 “Diagnostic source marker”，意思是主要用于诊断、排查和记录。比如同样是一个 `Call`，系统可能想知道这是人点按钮提交的，还是机器人策略自动选的。

## 5. `PlayerAction`：玩家提交的动作

```python
@dataclass(frozen=True, slots=True)
class PlayerAction:
    """A submitted player action in platform-native shape."""
```

`PlayerAction` 表示“玩家真的提交过来的一个动作”。

比如：“玩家 player-1，在第 0 号座位，在 hand-1 这手牌、turn-1 这个行动轮，选择加注到 120，来源是 human。”

`@dataclass` 会自动帮这个类生成初始化、比较等基础方法。

`frozen=True` 表示对象创建之后不允许随便改属性。比如创建后不能直接 `action.amount = 200`。这能减少很多“数据中途被偷偷改掉”的问题。

`slots=True` 是一种内存和结构优化。对新手来说可以先理解为：这个类只允许拥有明确定义过的字段，不能随便加新字段。

### 5.1 字段定义

```python
player_id: Identifier
seat_index: int
hand_id: Identifier
turn_id: Identifier
action_type: ActionType
amount: int | None = None
source: ActionSource = ActionSource.UNKNOWN
```

每个字段的意思：

- `player_id`：玩家 ID，可以是字符串或整数。
- `seat_index`：座位编号，必须是非负整数，比如 `0`、`1`、`2`。
- `hand_id`：当前这手牌的 ID。
- `turn_id`：当前行动轮的 ID。
- `action_type`：动作类型，必须是 `ActionType` 里的某一种。
- `amount`：筹码数量。只有 `RaiseTo` 需要带这个值，其他动作不允许带。
- `source`：动作来源，默认是 `UNKNOWN`。

注意 `amount: int | None = None`：

- `int` 表示整数。
- `None` 表示没有值。
- 所以 `int | None` 表示“可以是整数，也可以没有值”。

### 5.2 `__post_init__`：创建后立刻校验

```python
def __post_init__(self) -> None:
```

`dataclass` 创建对象时，会先把字段塞进去，然后自动调用 `__post_init__`。这个方法通常用来做校验和修正。

```python
action_type = _parse_enum(ActionType, self.action_type, "action_type")
source = _parse_enum(ActionSource, self.source, "source")
amount = _validate_optional_amount(self.amount, "amount")
```

这三行在做标准化：

- 把传入的 `action_type` 解析成真正的 `ActionType`。
- 把传入的 `source` 解析成真正的 `ActionSource`。
- 检查 `amount` 是不是合法筹码数量。

这意味着下面两种写法都可以：

```python
PlayerAction(..., action_type=ActionType.CALL)
PlayerAction(..., action_type="Call")
```

内部最终都会变成 `ActionType.CALL`。

```python
if action_type is ActionType.RAISE_TO:
    if amount is None:
        raise ValueError("RaiseTo requires amount")
elif amount is not None:
    raise ValueError(f"{action_type.value} does not accept amount")
```

这是 `PlayerAction` 最重要的规则：

- 如果动作是 `RaiseTo`，必须有 `amount`。
- 如果动作不是 `RaiseTo`，就不能有 `amount`。

例如：

```python
RaiseTo 120  # 合法
Call        # 合法
Fold        # 合法
RaiseTo     # 不合法，因为不知道加注到多少
Call 100    # 不合法，因为 Call 的金额应该由系统规则决定，不由玩家动作对象携带
```

然后下面这些行校验并写回字段：

```python
object.__setattr__(self, "player_id", _validate_identifier(self.player_id, "player_id"))
object.__setattr__(self, "seat_index", _validate_seat_index(self.seat_index))
object.__setattr__(self, "hand_id", _validate_identifier(self.hand_id, "hand_id"))
object.__setattr__(self, "turn_id", _validate_identifier(self.turn_id, "turn_id"))
object.__setattr__(self, "action_type", action_type)
object.__setattr__(self, "amount", amount)
object.__setattr__(self, "source", source)
```

为什么不用普通的 `self.player_id = ...`？

因为这个 dataclass 设置了 `frozen=True`，对象理论上不能被修改。但 `__post_init__` 里又需要把原始输入清洗成标准格式，所以这里用 `object.__setattr__` 这种底层方式写入最终值。

简单说：对象创建阶段允许最后整理一次，创建完成后就不再允许乱改。

### 5.3 `to_dict`：转成字典

```python
def to_dict(self) -> dict[str, object]:
    return {
        "player_id": self.player_id,
        "seat_index": self.seat_index,
        "hand_id": self.hand_id,
        "turn_id": self.turn_id,
        "action_type": self.action_type.value,
        "amount": self.amount,
        "source": self.source.value,
    }
```

这个方法把 `PlayerAction` 转成普通字典。

例如一个 Python 对象：

```python
PlayerAction(
    player_id="player-1",
    seat_index=0,
    hand_id="hand-1",
    turn_id="turn-1",
    action_type=ActionType.RAISE_TO,
    amount=120,
    source=ActionSource.HUMAN,
)
```

会变成：

```python
{
    "player_id": "player-1",
    "seat_index": 0,
    "hand_id": "hand-1",
    "turn_id": "turn-1",
    "action_type": "RaiseTo",
    "amount": 120,
    "source": "human",
}
```

注意 `action_type` 和 `source` 用了 `.value`。这是为了输出平台通用的字符串，而不是 Python 内部枚举对象。

### 5.4 `from_dict`：从字典创建对象

```python
@classmethod
def from_dict(cls, data: Mapping[str, Any]) -> Self:
```

`@classmethod` 表示这是类方法。调用方式是：

```python
PlayerAction.from_dict(payload)
```

这里的 `cls` 代表当前类，也就是 `PlayerAction`。

```python
_require_mapping(data, "PlayerAction")
```

先确认传进来的是字典类型。

```python
_require_keys(
    data,
    "PlayerAction",
    ("player_id", "seat_index", "hand_id", "turn_id", "action_type"),
)
```

再确认必填字段都存在。

`PlayerAction` 的必填字段是：

- `player_id`
- `seat_index`
- `hand_id`
- `turn_id`
- `action_type`

`amount` 和 `source` 不是必填，因为它们有默认处理。

```python
return cls(
    player_id=data["player_id"],
    seat_index=data["seat_index"],
    hand_id=data["hand_id"],
    turn_id=data["turn_id"],
    action_type=data["action_type"],
    amount=data.get("amount"),
    source=data.get("source", ActionSource.UNKNOWN),
)
```

这段用字典里的值创建 `PlayerAction`。

`data.get("amount")` 的意思是：如果字典里有 `amount` 就取它，没有就返回 `None`。

`data.get("source", ActionSource.UNKNOWN)` 的意思是：如果字典里有 `source` 就取它，没有就用 `ActionSource.UNKNOWN`。

### 5.5 `to_json` 和 `from_json`

```python
def to_json(self) -> str:
    return json.dumps(self.to_dict(), separators=(",", ":"), sort_keys=True)
```

这个方法先调用 `to_dict()`，再把字典转成 JSON 字符串。

`separators=(",", ":")` 会让 JSON 更紧凑，去掉多余空格。

`sort_keys=True` 会让 JSON 字段按 key 排序。好处是输出稳定，测试和日志比较时更容易看。

```python
@classmethod
def from_json(cls, payload: str) -> Self:
    return cls.from_dict(_loads_mapping(payload, "PlayerAction"))
```

这个方法从 JSON 字符串恢复成 `PlayerAction`。流程是：

1. `_loads_mapping` 把 JSON 字符串读成字典。
2. `from_dict` 把字典转成对象。

## 6. `LegalAction`：当前允许做的某个动作

```python
@dataclass(frozen=True, slots=True)
class LegalAction:
    """A platform description of one currently available action."""
```

`LegalAction` 表示“现在这个玩家可以做的一个动作”。

例如：

```python
LegalAction(ActionType.CALL, amount_fixed=20)
```

意思是：玩家现在可以跟注，跟注金额固定是 20。

再比如：

```python
LegalAction(ActionType.RAISE_TO, amount_min=40, amount_max=200)
```

意思是：玩家现在可以加注到某个总额，最低 40，最高 200。

### 6.1 字段定义

```python
action_type: ActionType
enabled: bool = True
amount_min: int | None = None
amount_max: int | None = None
amount_fixed: int | None = None
reason_if_disabled: str | None = None
```

字段意思：

- `action_type`：动作类型。
- `enabled`：这个动作当前是否可用，默认可用。
- `amount_min`：金额下限，主要用于 `RaiseTo`。
- `amount_max`：金额上限，主要用于 `RaiseTo`。
- `amount_fixed`：固定金额，常用于 `Call`。
- `reason_if_disabled`：如果这个动作不可用，为什么不可用。

举几个例子：

```python
LegalAction(ActionType.FOLD)
```

表示可以弃牌。

```python
LegalAction(ActionType.CHECK, enabled=False, reason_if_disabled="must call first")
```

表示理论上有 `Check` 这个动作位，但现在不能过牌，原因是你必须先跟注。

```python
LegalAction(ActionType.RAISE_TO, amount_min=40, amount_max=200)
```

表示可以加注到 40 到 200 之间。

### 6.2 `__post_init__` 校验

```python
action_type = _parse_enum(ActionType, self.action_type, "action_type")
amount_min = _validate_optional_amount(self.amount_min, "amount_min")
amount_max = _validate_optional_amount(self.amount_max, "amount_max")
amount_fixed = _validate_optional_amount(self.amount_fixed, "amount_fixed")
```

这几行把动作类型和金额字段都校验一遍。

金额字段允许是 `None`，如果有值就必须是非负整数。

```python
if not isinstance(self.enabled, bool):
    raise ValueError("enabled must be a bool")
```

`enabled` 必须是布尔值，也就是 `True` 或 `False`。

```python
if amount_min is not None and amount_max is not None and amount_min > amount_max:
    raise ValueError("amount_min cannot be greater than amount_max")
```

如果同时给了最小值和最大值，那么最小值不能大于最大值。

例如：

```python
amount_min = 200
amount_max = 40
```

这明显不合理，所以会报错。

```python
if self.reason_if_disabled is not None and not isinstance(self.reason_if_disabled, str):
    raise ValueError("reason_if_disabled must be a string or None")
```

不可用原因要么没有，也就是 `None`，要么必须是字符串。

```python
object.__setattr__(self, "action_type", action_type)
object.__setattr__(self, "amount_min", amount_min)
object.__setattr__(self, "amount_max", amount_max)
object.__setattr__(self, "amount_fixed", amount_fixed)
```

最后把标准化后的值写回对象。

### 6.3 字典和 JSON 转换

`LegalAction` 的 `to_dict`、`from_dict`、`to_json`、`from_json` 和 `PlayerAction` 思路一样。

`to_dict` 输出：

```python
{
    "action_type": "RaiseTo",
    "enabled": True,
    "amount_min": 40,
    "amount_max": 200,
    "amount_fixed": None,
    "reason_if_disabled": None,
}
```

`from_dict` 只有 `action_type` 是必填：

```python
_require_keys(data, "LegalAction", ("action_type",))
```

其他字段都有默认值：

- `enabled` 默认 `True`
- 金额字段默认 `None`
- `reason_if_disabled` 默认 `None`

## 7. `LegalActionSet`：一组可用动作

```python
@dataclass(frozen=True, slots=True)
class LegalActionSet:
    """Reusable collection of legal action descriptions."""

    actions: tuple[LegalAction, ...]
```

`LegalActionSet` 是多个 `LegalAction` 的集合。

例如当前玩家可以：

- 弃牌
- 跟注 20
- 加注到 40 到 200
- 全下

就可以表示为：

```python
LegalActionSet(
    (
        LegalAction(ActionType.FOLD),
        LegalAction(ActionType.CALL, amount_fixed=20),
        LegalAction(ActionType.RAISE_TO, amount_min=40, amount_max=200),
        LegalAction(ActionType.ALL_IN),
    )
)
```

`tuple[LegalAction, ...]` 的意思是：一个元组，里面有任意多个 `LegalAction`。

### 7.1 `__post_init__`：校验整个集合

```python
if isinstance(self.actions, Mapping | str | bytes) or not isinstance(
    self.actions, Iterable
):
    raise ValueError("actions must be an iterable of LegalAction values")
```

这里要求 `actions` 必须是“可以遍历的一组动作”。

但是它特意拒绝了：

- 字典：`Mapping`
- 字符串：`str`
- 字节串：`bytes`

为什么字符串也要拒绝？因为字符串在 Python 里也能被遍历，比如 `"Call"` 会被遍历成 `"C"`、`"a"`、`"l"`、`"l"`。这不是我们想要的动作列表。

```python
actions: list[LegalAction] = []
seen: set[ActionType] = set()
```

这里准备两个临时容器：

- `actions`：收集整理后的 `LegalAction`。
- `seen`：记录已经出现过的动作类型，防止重复。

```python
for action in self.actions:
    if isinstance(action, LegalAction):
        legal_action = action
    elif isinstance(action, Mapping):
        legal_action = LegalAction.from_dict(action)
    else:
        raise ValueError("actions must contain LegalAction values or dictionaries")
```

这个循环允许集合里有两种东西：

1. 已经是 `LegalAction` 对象。
2. 是字典，可以转成 `LegalAction`。

例如这两种都可以：

```python
LegalAction(ActionType.CALL)
{"action_type": "Call", "amount_fixed": 20}
```

如果是别的东西，比如字符串 `"Call"`，就会报错。

```python
if legal_action.action_type in seen:
    raise ValueError(f"duplicate legal action type: {legal_action.action_type.value}")
seen.add(legal_action.action_type)
actions.append(legal_action)
```

这里防止同一种动作出现两次。

例如这个不允许：

```python
LegalActionSet(
    (
        LegalAction(ActionType.CALL),
        LegalAction(ActionType.CALL),
    )
)
```

因为“可用动作列表”里重复出现两个 `Call` 会让后续逻辑变复杂。

```python
object.__setattr__(self, "actions", tuple(actions))
```

最后把整理好的列表转成元组，写回 `actions` 字段。

### 7.2 让集合可以被循环

```python
def __iter__(self) -> Iterable[LegalAction]:
    return iter(self.actions)
```

有了这个方法，你可以直接循环 `LegalActionSet`：

```python
for action in legal_action_set:
    print(action.action_type)
```

而不是必须写：

```python
for action in legal_action_set.actions:
    print(action.action_type)
```

### 7.3 让集合可以用 `len`

```python
def __len__(self) -> int:
    return len(self.actions)
```

有了这个方法，可以这样写：

```python
len(legal_action_set)
```

返回里面有几个动作。

### 7.4 `get`：按动作类型查找

```python
def get(self, action_type: ActionType | str) -> LegalAction | None:
    parsed_type = _parse_enum(ActionType, action_type, "action_type")
    return next((action for action in self.actions if action.action_type is parsed_type), None)
```

这个方法用动作类型找对应的 `LegalAction`。

例如：

```python
legal_action_set.get("RaiseTo")
legal_action_set.get(ActionType.RAISE_TO)
```

都可以。

`_parse_enum` 会先把传入值转成标准的 `ActionType`。

`next(..., None)` 的意思是：

- 找到第一个匹配动作就返回。
- 如果找不到，就返回 `None`。

### 7.5 `enabled_actions`：只取可用动作

```python
def enabled_actions(self) -> tuple[LegalAction, ...]:
    return tuple(action for action in self.actions if action.enabled)
```

这个方法过滤出 `enabled=True` 的动作。

例如集合里有：

```python
LegalAction(ActionType.CHECK, enabled=False)
LegalAction(ActionType.CALL, enabled=True)
```

`enabled_actions()` 只会返回 `CALL`。

### 7.6 字典和 JSON 转换

```python
def to_dict(self) -> dict[str, object]:
    return {"actions": [action.to_dict() for action in self.actions]}
```

这个方法把整个集合转成字典：

```python
{
    "actions": [
        {"action_type": "Fold", ...},
        {"action_type": "Call", ...},
        {"action_type": "RaiseTo", ...},
    ]
}
```

```python
@classmethod
def from_dict(cls, data: Mapping[str, Any]) -> Self:
    _require_mapping(data, "LegalActionSet")
    _require_keys(data, "LegalActionSet", ("actions",))
    return cls(tuple(data["actions"]))
```

从字典恢复时，要求必须有 `actions` 字段。然后把 `data["actions"]` 转成元组，再交给构造函数。

注意：真正把里面每个字典转成 `LegalAction` 的工作，是 `__post_init__` 里完成的。

## 8. `ActionError`：动作被拒绝时的错误

```python
@dataclass(frozen=True, slots=True)
class ActionError:
    """Platform error returned for rejected actions."""
```

`ActionError` 表示玩家提交动作失败时，平台返回的错误。

比如玩家不是当前行动者，却提交了 `Call`，系统可以返回：

```python
ActionError(
    code="not_current_player",
    message="It is not this player's turn",
    player_id="player-1",
    hand_id="hand-1",
    turn_id="turn-1",
)
```

### 8.1 字段定义

```python
code: str
message: str
player_id: Identifier | None = None
hand_id: Identifier | None = None
turn_id: Identifier | None = None
retry_same_player: bool = True
```

字段意思：

- `code`：机器可读的错误代码，比如 `"invalid_action"`。
- `message`：给人看的错误说明。
- `player_id`：相关玩家 ID，可选。
- `hand_id`：相关手牌 ID，可选。
- `turn_id`：相关行动轮 ID，可选。
- `retry_same_player`：是否让同一个玩家重新行动，默认是 `True`。

`retry_same_player=True` 很重要。比如玩家提交了非法加注金额，通常不应该直接跳到下一个玩家，而是让这个玩家重新选一个合法动作。

### 8.2 `__post_init__` 校验

```python
if not isinstance(self.code, str) or not self.code:
    raise ValueError("code must be a non-empty string")
if not isinstance(self.message, str) or not self.message:
    raise ValueError("message must be a non-empty string")
if not isinstance(self.retry_same_player, bool):
    raise ValueError("retry_same_player must be a bool")
```

这里要求：

- `code` 必须是非空字符串。
- `message` 必须是非空字符串。
- `retry_same_player` 必须是布尔值。

```python
object.__setattr__(
    self,
    "player_id",
    _validate_optional_identifier(self.player_id, "player_id"),
)
object.__setattr__(self, "hand_id", _validate_optional_identifier(self.hand_id, "hand_id"))
object.__setattr__(self, "turn_id", _validate_optional_identifier(self.turn_id, "turn_id"))
```

这里校验可选 ID：

- 如果是 `None`，可以。
- 如果不是 `None`，必须是合法 ID，也就是非空字符串或整数。

### 8.3 字典和 JSON 转换

`ActionError` 的转换逻辑和前面类似。

`to_dict` 输出普通字典。

`from_dict` 要求必须有：

- `code`
- `message`

其他字段都可以没有。

```python
retry_same_player=data.get("retry_same_player", True)
```

如果字典里没有 `retry_same_player`，默认就是 `True`。

## 9. `_parse_enum`：把字符串转成枚举

```python
def _parse_enum(enum_type: type[EnumT], value: object, field_name: str) -> EnumT:
```

这是一个内部辅助函数。函数名前面有 `_`，表示它主要给本文件内部使用，不鼓励外部直接调用。

它的作用：把输入值解析成某种枚举。

```python
if isinstance(value, enum_type):
    return value
```

如果传进来的已经是正确枚举，就直接返回。

例如：

```python
ActionType.CALL
```

已经是 `ActionType`，不用处理。

```python
if isinstance(value, str):
    candidate = value.casefold()
    for enum_value in enum_type:
        if candidate in {enum_value.name.casefold(), str(enum_value.value).casefold()}:
            return enum_value
```

如果传进来的是字符串，就忽略大小写去匹配。

它既支持枚举名字，也支持枚举值。

例如对 `ActionType.RAISE_TO = "RaiseTo"` 来说：

- `"RAISE_TO"` 可以匹配枚举名字。
- `"RaiseTo"` 可以匹配枚举值。
- `"raiseto"` 也可以，因为用了 `casefold()` 做大小写无关比较。

```python
valid_values = ", ".join(str(enum_value.value) for enum_value in enum_type)
raise ValueError(f"{field_name} must be one of: {valid_values}")
```

如果匹配不上，就报错，并告诉你有哪些合法值。

## 10. `_validate_identifier`：校验 ID

```python
def _validate_identifier(value: object, field_name: str) -> Identifier:
```

这个函数校验必填 ID。

```python
if isinstance(value, bool) or value is None:
    raise ValueError(f"{field_name} must be a string or integer identifier")
```

`None` 不可以。

`bool` 也不可以。虽然 Python 里 `True` 和 `False` 技术上是 `int` 的子类，但在业务上它们明显不应该当 ID，所以这里专门排除。

```python
if isinstance(value, int):
    return value
```

整数 ID 可以。

```python
if isinstance(value, str) and value:
    return value
```

非空字符串 ID 可以。

```python
raise ValueError(f"{field_name} must be a non-empty string or integer identifier")
```

其他情况都报错。比如空字符串、浮点数、列表、字典。

## 11. `_validate_optional_identifier`：校验可选 ID

```python
def _validate_optional_identifier(value: object, field_name: str) -> Identifier | None:
    if value is None:
        return None
    return _validate_identifier(value, field_name)
```

这个函数用于可选 ID。

规则很简单：

- 如果是 `None`，直接允许。
- 如果不是 `None`，就按必填 ID 的规则校验。

`ActionError` 里的 `player_id`、`hand_id`、`turn_id` 就用它，因为错误对象不一定总能关联到具体玩家或具体手牌。

## 12. `_validate_seat_index`：校验座位编号

```python
def _validate_seat_index(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError("seat_index must be a non-negative integer")
    return value
```

座位编号必须是非负整数：

- `0` 可以。
- `1` 可以。
- `-1` 不可以。
- `1.5` 不可以。
- `"0"` 不可以。
- `True` 不可以。

这里也专门排除了 `bool`，原因和 ID 一样：`True` 虽然在 Python 里有点像 `1`，但业务上不应该被当成座位号。

## 13. `_validate_optional_amount`：校验筹码金额

```python
def _validate_optional_amount(value: object, field_name: str) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{field_name} must be an integer chip amount")
    if value < 0:
        raise ValueError(f"{field_name} must be non-negative")
    return value
```

这个函数校验“可选金额”。

规则：

- `None` 可以，表示没有金额。
- 必须是整数。
- 不能是布尔值。
- 不能是负数。

合法例子：

```python
None
0
20
120
```

不合法例子：

```python
True
10.5
"20"
-1
```

这里的金额指筹码数量，所以必须是整数。

## 14. `_require_mapping`：要求输入是字典

```python
def _require_mapping(data: object, model_name: str) -> None:
    if not isinstance(data, Mapping):
        raise ValueError(f"{model_name} payload must be a dictionary")
```

这个函数用于 `from_dict` 和 `from_json`。

它确保传进来的 payload 是字典形状。

比如这个可以：

```python
{"action_type": "Call"}
```

这个不可以：

```python
["Call"]
```

报错信息里会带上模型名，比如：

```text
PlayerAction payload must be a dictionary
```

## 15. `_require_keys`：要求字典里有必填字段

```python
def _require_keys(data: Mapping[str, Any], model_name: str, keys: tuple[str, ...]) -> None:
    missing = [key for key in keys if key not in data]
    if missing:
        missing_list = ", ".join(missing)
        raise ValueError(f"{model_name} payload missing required field(s): {missing_list}")
```

这个函数检查字典里有没有缺字段。

例如 `PlayerAction` 必须有：

```python
("player_id", "seat_index", "hand_id", "turn_id", "action_type")
```

如果传入：

```python
{"player_id": "p1", "action_type": "Call"}
```

就会发现缺少：

- `seat_index`
- `hand_id`
- `turn_id`

然后报错。

## 16. `_loads_mapping`：从 JSON 读出字典

```python
def _loads_mapping(payload: str, model_name: str) -> Mapping[str, Any]:
    loaded = json.loads(payload)
    _require_mapping(loaded, model_name)
    return loaded
```

这个函数做两步：

1. `json.loads(payload)`：把 JSON 字符串转成 Python 数据。
2. `_require_mapping(...)`：确认读出来的是字典。

为什么要确认？

因为合法 JSON 不一定是字典。比如这些也是合法 JSON：

```json
["Call"]
```

```json
123
```

```json
"hello"
```

但本文件的 `from_json` 需要的是对象形状，也就是字典，所以要检查。

## 17. `__all__`：声明对外公开的名字

```python
__all__ = [
    "ActionError",
    "ActionSource",
    "ActionType",
    "LegalAction",
    "LegalActionSet",
    "PlayerAction",
]
```

`__all__` 表示这个模块希望对外公开哪些名字。

当其他地方写：

```python
from mcx_poker.engine.actions import *
```

只会导入这里列出来的名字。

注意：前面那些以下划线开头的辅助函数，比如 `_parse_enum`、`_validate_identifier`，没有放进 `__all__`，说明它们只是内部工具，不是这个模块对外承诺的公共接口。

## 18. 整个文件的数据流

可以把这个文件想象成“动作数据的安检口”。

### 玩家提交动作

外部可能传来一个字典：

```python
{
    "player_id": "player-1",
    "seat_index": 0,
    "hand_id": "hand-1",
    "turn_id": "turn-1",
    "action_type": "RaiseTo",
    "amount": 120,
    "source": "human",
}
```

系统用：

```python
PlayerAction.from_dict(data)
```

转成干净的 `PlayerAction` 对象。转换过程中会检查：

- ID 是否合法。
- 座位号是否合法。
- 动作类型是否存在。
- `RaiseTo` 是否带了金额。
- 非 `RaiseTo` 是否错误携带金额。

### 系统告诉玩家有哪些动作可选

系统可以创建：

```python
LegalActionSet(
    (
        LegalAction(ActionType.FOLD),
        LegalAction(ActionType.CALL, amount_fixed=20),
        LegalAction(ActionType.RAISE_TO, amount_min=40, amount_max=200),
    )
)
```

再通过：

```python
legal_action_set.to_dict()
```

变成普通字典，传给前端或控制器。

### 动作失败时返回错误

系统可以创建：

```python
ActionError(
    code="invalid_action",
    message="Raise amount is too small",
    player_id="player-1",
    hand_id="hand-1",
    turn_id="turn-1",
)
```

然后转成 JSON 传出去。

## 19. 初学者最容易误解的点

### `PlayerAction.amount` 不是所有动作的金额

这里只有 `RaiseTo` 允许带 `amount`。

`Call` 的金额虽然在牌局里也有意义，但这个动作对象不让玩家自己带 `amount`。跟注金额应该由当前牌局状态和合法动作信息决定，通常会放在 `LegalAction.amount_fixed` 里。

### `LegalAction` 是“允许做什么”，不是“玩家做了什么”

`LegalAction(ActionType.CALL, amount_fixed=20)` 的意思不是“玩家已经跟注 20”，而是“玩家现在可以跟注，金额是 20”。

真正的玩家提交动作是 `PlayerAction`。

### `ActionError` 不是 Python 异常

虽然名字里有 `Error`，但它本身只是一个数据对象，用来返回给平台或客户端。

代码里真正抛出的异常是：

```python
raise ValueError(...)
```

`ActionError` 更像 API 返回体。

### `frozen=True` 不是说完全不能初始化

`frozen=True` 是说对象创建完成后不能改。

但 `__post_init__` 里仍然可以用 `object.__setattr__` 做最后的标准化和校验。

## 20. 这个文件在项目里的角色

从项目结构看，其他模块会导入这里的类：

- 观察构建模块用 `LegalAction` 告诉当前玩家有哪些动作可以做。
- 玩家控制器用 `PlayerAction` 表示玩家或机器人选出来的动作。
- 校验器用 `ActionType`、`LegalActionSet` 判断提交动作是否合法。
- API/WebSocket 层用这些对象和字典/JSON 互相转换。

所以这个文件不是牌局规则引擎本身。它更像“动作数据格式合同”。大家都按照这份合同传数据，系统就更不容易乱。

## 21. 一句话总结

`actions.py` 定义了扑克平台里“动作相关数据”的标准形状，并在创建对象时主动校验输入，保证动作类型、金额、ID、错误信息都合法，同时提供字典和 JSON 转换，方便后端、前端、机器人和 API 之间稳定通信。
