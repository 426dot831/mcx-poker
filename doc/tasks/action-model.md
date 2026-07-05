# Action Model 任务列表

来源：`doc/detailed-design/engine/action-model.md`

目标：定义平台层统一动作格式，让 Web UI、Bot、Human Controller 和未来 Agent 都只提交 `PlayerAction`，不接触 PokerKit 细节。

## 最小任务

- [x] AM-01 定义动作类型枚举：`Fold`、`Check`、`Call`、`RaiseTo`、`AllIn`。
- [x] AM-02 定义 `PlayerAction` 数据结构，包含 `player_id`、`seat_index`、`hand_id`、`turn_id`、`action_type`、`amount`、`source`。
- [x] AM-03 统一金额类型为整数筹码单位，拒绝浮点金额作为核心模型输入。
- [x] AM-04 实现 `RaiseTo(amount)` 语义说明和字段约束：`amount` 表示本轮总下注额。
- [x] AM-05 实现 `AllIn` 独立动作约束：不得通过特殊金额表达，也不得携带 `amount`。
- [x] AM-06 定义 `LegalAction` 数据结构，包含 `action_type`、`enabled`、`amount_min`、`amount_max`、`amount_fixed`、`reason_if_disabled`。
- [x] AM-07 定义 `LegalActionSet` 或等价集合结构，供 Observation、Validator 和 UI 复用。
- [x] AM-08 定义 `ActionError` 数据结构，包含 `code`、`message`、`player_id`、`hand_id`、`turn_id`、`retry_same_player`。
- [x] AM-09 定义平台动作来源枚举或常量：`human`、`bot`、`future_agent`。
- [x] AM-10 实现动作输入的基础 shape 校验：`RaiseTo` 必须有金额，非 `RaiseTo` 不能有金额。
- [x] AM-11 实现动作模型序列化，保证 API/WebSocket 可以直接使用平台 DTO。
- [x] AM-12 实现动作模型反序列化，保证前端提交和 Bot 返回走同一结构。
- [x] AM-13 确保 Action Model 模块不 import PokerKit。
- [x] AM-14 为未来扩展预留未知来源或 future agent 来源，但不引入 LLM/GTO 依赖。
- [x] AM-15 补充模块导出入口，方便其他模块稳定 import。

## 测试与验收

- [x] AM-T01 测试所有动作类型可以稳定序列化和反序列化。
- [x] AM-T02 测试 `RaiseTo` 缺少金额会被基础校验拒绝。
- [x] AM-T03 测试 `Fold`、`Check`、`Call`、`AllIn` 携带金额会被基础校验拒绝。
- [x] AM-T04 测试 `AllIn` 不携带金额时 shape 校验通过。
- [x] AM-T05 测试金额为浮点数、负数或非数字时被拒绝。
- [x] AM-T06 测试 `ActionError.retry_same_player` 对非法动作默认保持 `true`。
- [x] AM-T07 测试 Action Model 序列化结果不包含 PokerKit 类型名或对象 repr。

## 不进入本模块

- [ ] AM-X01 不实现动作合法性上下文判断。
- [ ] AM-X02 不调用 PokerKit。
- [ ] AM-X03 不决定前端控件如何展示。
