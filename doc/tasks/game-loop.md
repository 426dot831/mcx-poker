# Game Loop 任务列表

来源：`doc/detailed-design/engine/game-loop.md`

目标：驱动一手牌从开始到结束，串联 Table Manager、PokerKit Adapter、Observation System、Player Controller、Action Validator、Temporary Hand Event Log 和 WebSocket Gateway。

## 最小任务

- [x] GL-01 定义 `CurrentActor`，包含 `hand_id`、`turn_id`、`seat_index`、`player_id`。
- [x] GL-02 定义 Game Loop 依赖接口，使用抽象或协议隔离真实模块。
- [x] GL-03 实现 `start_hand(hand_context)` 入口。
- [x] GL-04 从 PokerKit Adapter 读取当前手牌是否仍活动。
- [x] GL-05 从 PokerKit Adapter 读取当前平台层 actor。
- [x] GL-06 当 actor 为空时调用非玩家状态推进边界或跳过到下一轮状态读取。
- [x] GL-07 为每次玩家行动生成新的 `turn_id`。
- [x] GL-08 调用 Observation System 为当前 actor 生成 Observation。
- [x] GL-09 调用 Player Controller Registry 找到当前玩家 Controller。
- [x] GL-10 调用 Controller 的 `request_action(observation, context)`。
- [x] GL-11 调用 Action Validator 校验返回动作。
- [x] GL-12 Validator 拒绝时通知同一 Controller，并记录 rejected action。
- [x] GL-13 Validator 拒绝后不推进 Adapter，不更新筹码，不记录成功动作。
- [x] GL-14 Validator 通过后调用 PokerKit Adapter 提交动作。
- [x] GL-15 Adapter 拒绝时通知同一 Controller，并记录 rejected action。
- [x] GL-16 Adapter 拒绝后保持同一玩家重新行动。
- [x] GL-17 Adapter 接受时记录 successful action。
- [x] GL-18 成功动作后广播状态更新。
- [x] GL-19 在请求玩家行动前检查 Table Manager 暂停或重开状态。
- [x] GL-20 在收到动作后、提交 Adapter 前检查暂停或中止边界。
- [x] GL-21 手牌结束后从 Adapter 读取 settlement。
- [x] GL-22 调用 Table Manager `apply_hand_settlement(settlement)`。
- [x] GL-23 记录 `hand_ended` 和 settlement 事件。
- [x] GL-24 广播 `hand_ended`。
- [x] GL-25 在 Table Manager 仍 running 时触发下一手创建边界。
- [x] GL-26 确保所有事件 payload 都是平台层 DTO。
- [x] GL-27 确保 Game Loop 不 import PokerKit。

## 测试与验收

- [x] GL-T01 使用 fake Adapter、fake Controller、fake Table Manager 测试正常动作推进到一手结束。
- [x] GL-T02 测试 Validator 拒绝动作后同一 actor 再次被请求行动。
- [x] GL-T03 测试 Adapter 拒绝动作后同一 actor 再次被请求行动。
- [x] GL-T04 测试 Human Controller pending 时 Game Loop 不错误推进。
- [x] GL-T05 测试一手结束后必须调用 `apply_hand_settlement`。
- [x] GL-T06 测试事件顺序符合 hand started -> actor requested -> action -> hand ended。
- [x] GL-T07 测试暂停状态在安全边界阻止继续请求新动作。
- [x] GL-T08 测试 reset 后当前 pending action 失效。
- [x] GL-T09 测试 Game Loop 不接收或传播 PokerKit 原始对象。
- [x] GL-T10 使用真实 PokerKit Adapter 做最小集成测试：6 人现金桌能进入首个 actor。

## 不进入本模块

- [ ] GL-X01 不实现 Bot 策略。
- [ ] GL-X02 不渲染前端 UI。
- [ ] GL-X03 不直接访问 PokerKit `State`。
- [ ] GL-X04 不直接修改长期筹码，除非通过 Table Manager settlement。
