# Game Loop 详细设计

## 1. 模块目标

Game Loop 驱动一手牌从开始到结束。它读取权威状态，找到当前行动玩家，生成 Observation，请求 Player Controller 返回 Action，调用 Action Validator 和 PokerKit Adapter 推进状态，并处理非法动作重试。

Game Loop 不负责：

- PokerKit 规则实现。
- Bot 策略。
- 前端渲染。
- Table Manager 长期筹码生命周期。
- 直接操作 PokerKit 原始对象。

## 2. 依赖模块

Game Loop 依赖以下抽象：

| 模块 | 用途 |
| --- | --- |
| Table Manager | 获取当前手牌上下文、座位和玩家 |
| PokerKit Adapter | 读取当前牌局状态、提交动作、读取结算 |
| Observation System | 生成当前玩家视角 |
| Player Controller Registry | 根据当前玩家找到 Controller |
| Action Validator | 平台层动作校验 |
| Temporary Hand Event Log | 记录当前手牌临时事件 |
| WebSocket Gateway | 广播状态变化和行动提示 |

## 3. 一手牌循环

核心流程：

```text
start_hand(hand_context)
↓
while adapter.hand_is_active(hand_id):
    actor = adapter.get_current_actor(hand_id)
    if actor is None:
        adapter.advance_non_player_state(hand_id)
        continue
    observation = observation_system.build(actor)
    action = controller.request_action(observation, context)
    validation = action_validator.validate(action, context)
    if validation failed:
        controller.notify_action_rejected(error)
        hand_event_log.record_rejected_action(error)
        continue same actor
    result = adapter.submit_action(validation)
    if result failed:
        controller.notify_action_rejected(error)
        hand_event_log.record_rejected_action(error)
        continue same actor
    hand_event_log.record_successful_action(result)
    websocket.broadcast_state_update()
↓
settlement = adapter.get_settlement(hand_id)
table_manager.apply_hand_settlement(settlement)
hand_event_log.record_hand_ended(settlement)
websocket.broadcast_hand_ended(settlement)
```

在使用 PokerKit 自动化非玩家动作时，`advance_non_player_state` 通常由 PokerKit 在动作提交后自动完成。若实现选择不自动化某些步骤，该边界用于保持 Game Loop 不把发牌、收注、推筹码等内部步骤暴露给 Player Controller。

## 4. 当前行动玩家

PokerKit `State.turn_index` 已在 `pokerkit==0.7.4` 源码和临时 venv 中验证，可用于读取当前需要决策的玩家索引。PokerKit Adapter 应把该索引映射到平台层 `seat_index` 和 `player_id`。下注阶段也可用 `State.actor_index` 校验当前投注动作玩家，但 Game Loop 只消费 Adapter 返回的平台层 actor。

Game Loop 只能使用 Adapter 返回的平台层 actor：

```text
CurrentActor:
  hand_id
  turn_id
  seat_index
  player_id
```

`turn_id` 由平台生成，用于拒绝前端或 Bot 的过期动作。

## 5. 非法动作处理

非法动作来源：

- Action Validator 拒绝。
- PokerKit Adapter 调用 PokerKit 后拒绝。
- 牌桌控制命令使当前等待失效。

处理规则：

- 当前行动玩家不变。
- PokerKit 状态不推进。
- Table Manager 筹码不变化。
- 不记录为成功动作。
- 可记录 rejected action 事件用于调试或 UI 提示。
- 同一 Player Controller 重新选择动作。

```text
PlayerAction
↓
ValidationError or AdapterError
↓
notify same controller
↓
request action again with fresh or same Observation
```

如果错误来自过期 `turn_id`，Game Loop 应重新发送当前合法 Observation，而不是推进手牌。

## 6. 暂停和中止边界

需求确认 Table Manager 支持暂停、继续和重开。Game Loop 应在安全边界检查牌桌控制状态：

- 请求玩家行动前。
- 收到玩家动作后、提交 Adapter 前。
- 一手结束准备创建下一手前。

暂停时不应在中途修改 PokerKit 状态。是否允许正在等待 Human 输入的行动在暂停期间继续提交，需要在实现阶段明确；当前需求未确认。

## 7. 事件输出

Game Loop 应输出事件给 Temporary Hand Event Log 和 WebSocket Gateway：

- hand started
- actor requested
- action accepted
- action rejected
- board updated
- hand ended

事件 payload 必须是平台层可见数据，不包含 PokerKit 原始对象。

## 8. 不变量

- Game Loop 不 import PokerKit。
- Game Loop 不直接访问 PokerKit `State`。
- Game Loop 不修改 Table Manager 筹码，除非通过 `apply_hand_settlement`。
- 成功动作必须先经过 Validator，再提交 Adapter。
- Bot 和 Human 的非法动作路径一致。
- 一手结束后必须通过 Table Manager 更新长期筹码。

## 9. 测试策略

单元测试使用 fake Adapter、fake Controller 和 fake Table Manager：

- 正常动作推进到一手结束。
- Validator 拒绝动作后同一 actor 再次请求行动。
- Adapter 拒绝动作后同一 actor 再次请求行动。
- Human Controller pending 时 Game Loop 不错误推进。
- 一手结束后调用 `apply_hand_settlement`。
- 事件顺序符合 hand started -> action -> hand ended。
- Game Loop 不接收或传播 PokerKit 原始对象。

集成测试可使用临时 venv 中的 `pokerkit==0.7.4` 验证：

- 6 人 No-Limit Texas Hold'em 现金桌初始化后首个 actor 可由 `State.turn_index` 读取。
- 当前 call 金额和 raise-to 边界可由 `State.checking_or_calling_amount`、`State.min_completion_betting_or_raising_to_amount`、`State.max_completion_betting_or_raising_to_amount` 读取。
- `Fold`、`Check/Call`、`RaiseTo` 能通过 Adapter 推进状态。
- 非法 raise-to 金额被 PokerKit 拒绝并映射成平台错误。

## 10. 开放问题

- 第一版 Game Loop 是否从一开始异步化以适配 WebSocket 和 Web UI，还是先实现同步核心再包 Web 交互。
- Bot 行动是否需要可配置延迟，还是即时行动即可。
- 暂停期间是否允许当前 pending Human 动作继续提交。
