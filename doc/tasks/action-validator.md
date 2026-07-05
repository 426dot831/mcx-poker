# Action Validator 任务列表

来源：`doc/detailed-design/engine/action-validator.md`

目标：在平台层拦截非法动作，保证提交给 PokerKit Adapter 的动作属于当前行动机会、当前玩家、当前合法动作集合。

## 最小任务

- [x] AV-01 定义 `ActionContext`，包含当前 `table_id`、`hand_id`、`turn_id`、`actor_player_id`、`actor_seat_index`。
- [x] AV-02 定义 `ValidatedAction`，包含原始动作、标准化动作类型、标准化金额和校验来源。
- [x] AV-03 定义 Validator 输入契约：`PlayerAction`、`ActionContext`、`LegalActionSet`、`TableSnapshot`。
- [x] AV-04 校验 `hand_id` 必须匹配当前手牌。
- [x] AV-05 校验 `turn_id` 必须匹配当前行动机会。
- [x] AV-06 校验 `player_id` 必须坐在提交的 `seat_index` 上。
- [x] AV-07 校验提交座位必须是当前行动座位。
- [x] AV-08 校验动作类型必须存在于当前 `LegalActionSet`。
- [x] AV-09 校验 disabled 的合法动作不能提交，并返回 `action_not_available`。
- [x] AV-10 校验 `RaiseTo` 必须携带正整数 `amount`。
- [x] AV-11 校验非 `RaiseTo` 动作不能携带 `amount`。
- [x] AV-12 校验 `RaiseTo(amount)` 不低于 `amount_min`。
- [x] AV-13 校验 `RaiseTo(amount)` 不高于 `amount_max`。
- [x] AV-14 校验 `Call`、`Check` 与 `amount_fixed` 或 call 金额语义保持一致。
- [x] AV-15 为每一种失败情况返回稳定平台错误码。
- [x] AV-16 保证所有非法动作错误都标记 `retry_same_player = true`。
- [x] AV-17 保证 Validator 不修改传入的状态对象、快照对象或合法动作集合。
- [x] AV-18 保证 Validator 不记录事件、不广播事件、不调用 Adapter。
- [x] AV-19 将 PokerKit Adapter 返回的动作错误统一转换为 Game Loop 可处理的 `ActionError`。
- [x] AV-20 确保 Validator 模块不 import PokerKit。

## 测试与验收

- [x] AV-T01 测试当前行动玩家提交可用 `Fold` 时校验成功。
- [x] AV-T02 测试非当前玩家提交动作返回 `not_current_actor`。
- [x] AV-T03 测试过期 `turn_id` 返回 `turn_mismatch`。
- [x] AV-T04 测试手牌不匹配返回 `hand_mismatch`。
- [x] AV-T05 测试玩家不在座位返回 `player_not_seated`。
- [x] AV-T06 测试不可用动作返回 `action_not_available`。
- [x] AV-T07 测试 `RaiseTo` 无金额返回 `amount_required`。
- [x] AV-T08 测试 `AllIn` 携带金额返回 `amount_not_allowed`。
- [x] AV-T09 测试 `RaiseTo` 低于最小金额返回 `amount_out_of_range`。
- [x] AV-T10 测试 `RaiseTo` 高于最大金额返回 `amount_out_of_range`。
- [x] AV-T11 测试 Validator 失败后状态对象没有变化。
- [x] AV-T12 测试 Adapter 非法动作错误能走同一错误反馈结构。

## 不进入本模块

- [ ] AV-X01 不实现 Bot fallback 动作。
- [ ] AV-X02 不推进 PokerKit 状态。
- [ ] AV-X03 不更新 Table Manager 筹码。
- [ ] AV-X04 不决定 UI 错误展示样式。
