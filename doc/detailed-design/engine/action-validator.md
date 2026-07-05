# Action Validator 详细设计

## 1. 模块目标

Action Validator 在平台层拦截非法动作，保证提交给 PokerKit Adapter 的动作满足当前平台上下文和 Observation 合法动作集合。

Action Validator 是第一层防线，PokerKit 仍是最终规则权威。

本模块不负责：

- 生成玩家策略。
- 修改 PokerKit 状态。
- 更新 Table Manager 筹码。
- 渲染前端错误。

## 2. 校验输入

校验输入字段概念：

| 输入 | 说明 |
| --- | --- |
| `PlayerAction` | 玩家提交的平台层动作 |
| `ActionContext` | 当前手牌、当前行动座位、当前 `turn_id` |
| `LegalActionSet` | Observation 或 Adapter 生成的合法动作集合 |
| `TableSnapshot` | 玩家与座位关系、当前手牌状态 |

`ActionContext` 应由 Game Loop 创建，不能由前端或 Bot 自行决定。

## 3. 校验步骤

```text
validate hand_id
↓
validate turn_id
↓
validate player_id and seat_index
↓
validate current actor
↓
validate action type is available
↓
validate amount shape
↓
validate platform amount bounds
↓
return ValidatedAction
```

若平台校验通过，Game Loop 再调用 PokerKit Adapter。Adapter 调用 PokerKit 前后仍需处理 PokerKit 自身的合法性结果。

## 4. 具体规则

通用规则：

- `hand_id` 必须等于当前手牌。
- `turn_id` 必须等于当前行动机会。
- `player_id` 必须坐在 `seat_index` 上。
- `seat_index` 必须是当前行动座位。
- `action_type` 必须属于当前 `LegalActionSet`。

金额规则：

- `RaiseTo` 必须携带 `amount`。
- 非 `RaiseTo` 动作不能携带 `amount`。
- `amount` 必须是正整数筹码单位。
- `RaiseTo(amount)` 必须满足当前合法金额范围。
- `AllIn` 不使用 `amount`，具体投入金额由 PokerKit Adapter 根据当前状态转换。

PokerKit 验证：

- `State.can_fold()` 对应平台 `Fold` 可用性。
- `State.can_check_or_call()` 对应平台 `Check` 或 `Call` 可用性。
- `State.can_complete_bet_or_raise_to(amount)` 对应平台 `RaiseTo(amount)` 可用性。
- `State.checking_or_calling_amount` 用于区分平台 `Check` 与 `Call`：金额为 0 时是 `Check`，大于 0 时是 `Call`。
- `State.min_completion_betting_or_raising_to_amount` 提供最小合法 raise-to 金额。
- `State.max_completion_betting_or_raising_to_amount` 提供最大合法 raise-to 金额。

以上 PokerKit 接口已在 GitHub `v0.7.4` 源码和临时 venv 中验证。最终实现仍应在 Adapter 层集中引用，不应从 Validator 直接访问 PokerKit。

## 5. 输出

成功输出 `ValidatedAction`：

| 字段 | 说明 |
| --- | --- |
| `action` | 原始 `PlayerAction` |
| `normalized_type` | 平台标准动作类型 |
| `normalized_amount` | 标准化后的金额，仅 `RaiseTo` 使用 |
| `validation_source` | `platform` |

失败输出 `ActionError`：

| 错误码 | 触发条件 |
| --- | --- |
| `hand_mismatch` | 动作手牌不是当前手牌 |
| `turn_mismatch` | `turn_id` 过期或不匹配 |
| `player_not_seated` | 玩家不在该座位 |
| `not_current_actor` | 不是当前行动玩家 |
| `action_not_available` | 动作类型当前不可执行 |
| `amount_required` | `RaiseTo` 缺少金额 |
| `amount_not_allowed` | 非金额动作携带金额 |
| `amount_out_of_range` | 金额低于最小值或高于最大值 |

所有非法动作错误都应指示 Game Loop 让同一牌手重新选择。

## 6. 不变量

- Validator 不改变任何状态。
- Validator 不写事件日志。
- Validator 不广播前端事件。
- Validator 不捕获或吞掉 PokerKit Adapter 的最终错误。
- Validator 不直接 import PokerKit。

## 7. 测试策略

- 当前行动玩家提交 `Fold` 成功。
- 非当前玩家提交动作失败。
- 过期 `turn_id` 失败。
- `RaiseTo` 无金额失败。
- `AllIn` 携带金额失败。
- `RaiseTo` 低于最小值失败。
- `RaiseTo` 高于最大值失败。
- Validator 返回错误后状态对象未被修改。
- PokerKit Adapter 返回非法动作时，Game Loop 仍走同一错误反馈路径。

## 8. 开放问题

- 是否需要将 `Check` 和 `Call` 在 Action Model 中保留为两个用户动作，还是内部统一为 PokerKit `check_or_call()` 后再按金额区分展示。当前需求要求动作集合同时包含 `Check` 和 `Call`。
- 是否向 UI 暴露完整金额边界，还是只后端校验后返回错误。
