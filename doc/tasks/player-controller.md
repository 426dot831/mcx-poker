# Player Controller 任务列表

来源：`doc/detailed-design/domain/player-controller.md`

目标：统一 Human、Bot 和未来玩家来源。Game Loop 只通过 `Observation -> Action` 契约请求动作。

## 最小任务

- [x] PC-01 定义 Player Controller 基础接口：`request_action(observation, action_request_context)`。
- [x] PC-02 定义通知接口：`notify_action_rejected(action_error)`。
- [x] PC-03 定义通知接口：`notify_hand_started(hand_context)`。
- [x] PC-04 定义通知接口：`notify_hand_ended(result_summary)`。
- [x] PC-05 定义 `ActionRequestContext`，包含 `table_id`、`hand_id`、`turn_id`、`player_id`、`seat_index`。
- [x] PC-06 实现 Controller Registry，可通过 `player_id` 或座位找到 Controller。
- [x] PC-07 实现 Human Player Controller 的 pending action 注册。
- [x] PC-08 保证 Human Controller 同一时间最多一个 pending `turn_id`。
- [x] PC-09 实现 Human Controller 接收前端提交动作并唤醒等待点。
- [x] PC-10 拒绝过期 `turn_id` 的 Human 动作。
- [x] PC-11 拒绝非当前玩家或非当前座位的 Human 动作。
- [x] PC-12 Human 非法动作错误后保持同一 pending 行动等待。
- [x] PC-13 实现最小 Bot Controller，用于验证本地闭环。
- [x] PC-14 Bot Controller 只能从 Observation 的 `legal_actions` 中选择动作。
- [x] PC-15 Bot 返回非法动作时平台不替 Bot 自动 fallback。
- [x] PC-16 为 Bot 策略预留可替换实现，不侵入核心接口。
- [x] PC-17 预留 `future_agent` controller 类型，但不实现真实 LLM/GTO。
- [x] PC-18 确保 Controller 模块不读取 PokerKit 内部状态。
- [x] PC-19 确保 Controller 不修改 Table Manager。
- [x] PC-20 确保 Controller 返回的是 Action Model 中定义的 `PlayerAction`。

## 测试与验收

- [x] PC-T01 fake Observation 输入下 Bot 返回合法 `PlayerAction`。
- [x] PC-T02 Bot 无合法动作时返回可诊断错误或受控结果。
- [x] PC-T03 Bot 返回非法动作时平台不自动替换动作。
- [x] PC-T04 Human Controller 可以注册 pending `turn_id`。
- [x] PC-T05 过期 `turn_id` 被拒绝。
- [x] PC-T06 非当前玩家动作被拒绝。
- [x] PC-T07 非法动作错误会传递给 Human Controller。
- [x] PC-T08 Game Loop 可以使用 fake Controller 独立测试。
- [x] PC-T09 Controller 输出序列化后不包含 PokerKit 对象。

## 不进入本模块

- [ ] PC-X01 不实现复杂 Bot 策略。
- [ ] PC-X02 不实现超时自动弃牌，除非后续确认。
- [ ] PC-X03 不实现断线托管，除非后续确认。
- [ ] PC-X04 不生成前端 UI。
