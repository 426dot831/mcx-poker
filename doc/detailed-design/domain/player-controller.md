# Player Controller 详细设计

## 1. 模块目标

Player Controller 统一所有玩家来源。Game Loop 只向 Controller 提供 Observation，并接收 Action，不关心玩家是 Human、Bot 还是未来 Agent。

统一契约：

```text
PlayerObservation -> PlayerAction
```

本模块不负责：

- 判断动作是否合法。
- 直接读取 PokerKit 状态。
- 修改 Table Manager。
- 替 Bot 决定 fallback 动作。
- 生成前端 UI。

## 2. Controller 类型

MVP 需要支持：

- Human Player Controller：等待 Web UI 通过 WebSocket 或 API 提交动作。
- Bot Player Controller：用于验证统一玩家接口和本地可玩闭环。

未来预留：

- LLM Player Controller。
- GTO Player Controller。
- External API Player Controller。

MVP 必须至少具备可验证的 Player Controller 插拔能力。具体需要哪些 Bot 策略仍未确认。

## 3. 核心接口

设计层接口字段概念：

```text
request_action(observation, action_request_context) -> PlayerAction
notify_action_rejected(action_error) -> None
notify_hand_started(hand_context) -> None
notify_hand_ended(result_summary) -> None
```

`action_request_context` 应包含：

| 字段 | 说明 |
| --- | --- |
| `table_id` | 当前牌桌 |
| `hand_id` | 当前手牌 |
| `turn_id` | 当前行动机会 |
| `player_id` | 当前玩家 |
| `seat_index` | 当前座位 |

接口是否使用同步函数、异步函数或回调式等待，取决于 Game Loop 的执行模型；需求文档尚未确认第一版 Game Loop 是否一开始异步化。详细设计只要求存在可等待的行动请求边界。

## 4. Human Player Controller

Human Player Controller 的职责是把 Game Loop 的行动请求转换成前端可提交的等待点。

流程：

```text
Game Loop calls request_action
↓
Human Controller registers pending turn_id
↓
WebSocket Gateway sends "your turn" observation
↓
User submits PlayerAction with same turn_id
↓
Human Controller returns PlayerAction to Game Loop
```

约束：

- 每个 Human Controller 同一时间最多只能有一个 pending action。
- 收到过期 `turn_id` 的动作必须拒绝。
- 收到非当前玩家的动作必须拒绝。
- 非法动作错误返回后，Controller 必须保持同一玩家行动等待，直到 Game Loop 中止或玩家提交合法动作。
- Human Controller 不自行修正非法动作。

## 5. Bot Player Controller

Bot Player Controller 只接收 Observation 并返回 Action。

约束：

- Bot 不能读取 PokerKit 内部状态。
- Bot 不能读取对手未公开底牌。
- Bot 只能从 Observation 的合法动作集合中选择动作。
- 如果 Bot 返回非法动作，平台不替 Bot fallback；Game Loop 会通过同一非法动作路径重新请求该 Bot 行动。
- Bot 策略应作为可替换实现，不侵入平台核心。

MVP 可用的最小 Bot 只需用于验证闭环，不代表最终 AI 策略。

## 6. 错误处理

Controller 需要能接收以下错误：

- 过期行动机会。
- 非当前玩家提交动作。
- 动作类型当前不可执行。
- 金额低于最小值或高于最大值。
- PokerKit 最终判定非法。
- 牌桌暂停或手牌中止。

Human Controller 应把错误传回前端；Bot Controller 应在下一次 `request_action` 时重新选择动作。

## 7. 模块边界

Player Controller 依赖：

- Observation System 输出的 `PlayerObservation`。
- Action Model 定义的 `PlayerAction`。
- WebSocket Gateway 或 API 为 Human Controller 提供动作输入。

Player Controller 不依赖：

- PokerKit。
- Table Manager 内部状态。
- Frontend 组件实现。
- 具体 Bot 策略以外的策略引擎。

## 8. 测试策略

- fake Observation 输入下 Bot 返回合法 `PlayerAction`。
- Bot 返回非法动作时平台不自动替换动作。
- Human Controller 注册 pending `turn_id`。
- 过期 `turn_id` 被拒绝。
- 非当前玩家动作被拒绝。
- 非法动作错误会传递给 Human Controller。
- Game Loop 可以用 fake Controller 独立测试，不依赖真实 WebSocket。

## 9. 开放问题

- MVP 必须实现哪些 Bot：Random、Always Call、Nit、Aggressive 是否都进入 MVP。
- Player Controller 是否需要超时、自动弃牌或断线托管。
- 第一版 Game Loop 和 Human Controller 的接口采用同步、异步还是回调式等待。

