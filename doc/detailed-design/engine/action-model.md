# Action Model 详细设计

## 1. 模块目标

Action Model 定义平台层统一动作格式，使 Web UI、Bot、Human Player Controller 和未来 Agent 不需要了解 PokerKit 内部调用方式。

本模块只定义动作语义和数据契约，不负责：

- 判断动作是否合法。
- 推进 PokerKit 状态。
- 决定 UI 如何展示控件。
- 决定 Bot 如何选择动作。

## 2. 动作集合

MVP 动作集合固定为：

```text
Fold
Check
Call
RaiseTo(amount)
AllIn
```

语义约束：

- `Fold`：放弃当前手牌。
- `Check`：在无需补注时过牌。
- `Call`：跟注到当前要求的下注额。
- `RaiseTo(amount)`：加注到当前下注轮内该玩家的总下注额 `amount`。
- `AllIn`：投入当前可用全部筹码，是独立动作，不用 `RaiseTo(stack)` 或特殊金额表达。

`RaiseTo(amount)` 的 `amount` 不是“额外加注额”，也不是“本次追加金额”。

## 3. 数据结构

设计层 `PlayerAction` 应包含以下字段概念：

| 字段 | 说明 |
| --- | --- |
| `player_id` | 提交动作的玩家 |
| `seat_index` | 提交动作的座位，用于校验玩家与座位关系 |
| `hand_id` | 动作所属手牌 |
| `turn_id` | 当前行动机会标识，用于拒绝过期动作 |
| `action_type` | `Fold`、`Check`、`Call`、`RaiseTo`、`AllIn` |
| `amount` | 仅 `RaiseTo` 需要；其他动作必须为空 |
| `source` | `human`、`bot`、`future_agent` 等来源标记，仅用于诊断 |

金额建议使用整数筹码单位，避免浮点误差。若后续需要真实货币、小数盲注或不同展示单位，需另行确认金额精度和转换规则。

## 4. 合法动作描述

Observation 中应向当前行动玩家提供合法动作集合。Action Model 对合法动作集合只定义平台语义，不决定 UI 文案。

设计层 `LegalAction` 字段概念：

| 字段 | 说明 |
| --- | --- |
| `action_type` | 可执行动作类型 |
| `enabled` | 该动作当前是否可提交 |
| `amount_min` | 金额类动作的最小允许值 |
| `amount_max` | 金额类动作的最大允许值 |
| `amount_fixed` | `Call` 等固定金额动作的金额说明 |
| `reason_if_disabled` | 不可执行原因，仅用于调试或 UI 提示 |

是否把最小加注额、可 call 金额、有效筹码等派生字段作为 Observation 对外稳定字段，仍属于需求文档中的待确认事项。实现可以先把这些字段作为后端内部合法性校验数据。

## 5. 错误模型

Action Model 不直接抛出 PokerKit 错误。非法动作统一由 Action Validator 或 PokerKit Adapter 转换成平台错误。

错误字段概念：

| 字段 | 说明 |
| --- | --- |
| `code` | 平台错误码 |
| `message` | 面向调用方的简短说明 |
| `player_id` | 原动作玩家 |
| `hand_id` | 原动作手牌 |
| `turn_id` | 原行动机会 |
| `retry_same_player` | 是否要求同一玩家重新行动 |

MVP 中非法动作的 `retry_same_player` 必须为 `true`，除非外部控制命令中止当前手牌或牌桌。

## 6. 不变量

- `AllIn` 不接受 `amount`。
- `RaiseTo` 必须携带 `amount`。
- 非 `RaiseTo` 动作携带 `amount` 应被拒绝。
- `player_id`、`seat_index`、`hand_id`、`turn_id` 必须足以校验动作是否属于当前行动机会。
- Action Model 不允许出现 PokerKit 类、枚举或异常对象。

## 7. 测试策略

- 枚举动作序列化和反序列化测试。
- `RaiseTo` 金额字段必填测试。
- `AllIn` 禁止金额测试。
- 过期 `turn_id` 动作被拒绝的校验测试。
- 前端提交和 Bot 返回使用同一 `PlayerAction` 结构的契约测试。

## 8. 开放问题

- 金额单位是否需要支持小数或真实货币展示。
- Observation 是否需要稳定暴露 `call_amount`、`min_raise_to`、`max_raise_to`、`effective_stack` 等派生字段。

