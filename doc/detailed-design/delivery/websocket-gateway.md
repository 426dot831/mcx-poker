# WebSocket Gateway 详细设计

## 1. 模块目标

WebSocket Gateway 向前端实时推送牌桌状态和行动事件，并接收 Human Player 的动作提交。

本模块不负责：

- 判断动作是否合法。
- 直接调用 PokerKit。
- 生成 Bot 动作。
- 持久化事件。
- 冻结未来长期兼容的公共事件 schema。

WebSocket 完整事件 schema 是否在第一版冻结仍未确认。本文只定义 MVP 内部需要满足的事件契约。

## 2. 连接职责

每个连接需要关联：

| 字段 | 说明 |
| --- | --- |
| `connection_id` | 后端生成 |
| `player_id` | Human 玩家，可为空 |
| `seat_index` | Human 玩家座位，可为空 |
| `table_id` | 当前本地牌桌 |
| `visibility_scope` | player 或 table |

是否支持旁观者、同一用户多客户端连接，当前需求未确认。

## 3. 服务端事件

MVP 服务端事件类型：

| 事件 | 说明 |
| --- | --- |
| `table_snapshot` | 当前牌桌公开快照 |
| `hand_started` | 新手牌开始 |
| `hole_cards_dealt` | 仅发给对应玩家的底牌可见事件 |
| `board_updated` | 公共牌更新 |
| `action_requested` | 轮到当前 Human 玩家行动 |
| `player_acted` | 玩家成功行动 |
| `action_rejected` | Human 玩家提交非法动作 |
| `hand_ended` | 手牌结束和公开结算摘要 |
| `table_paused` | 牌桌暂停 |
| `table_resumed` | 牌桌继续 |
| `table_reset` | 牌桌重开 |

所有事件 payload 必须是平台层 DTO，不包含 PokerKit 对象。

## 4. 客户端事件

MVP 客户端事件类型：

| 事件 | 说明 |
| --- | --- |
| `submit_action` | 提交 `PlayerAction` |
| `request_snapshot` | 请求当前快照 |

`submit_action` payload 字段概念：

| 字段 | 说明 |
| --- | --- |
| `player_id` | 提交玩家 |
| `seat_index` | 提交座位 |
| `hand_id` | 当前手牌 |
| `turn_id` | 当前行动机会 |
| `action_type` | Fold、Check、Call、RaiseTo、AllIn |
| `amount` | 仅 RaiseTo 使用 |

Gateway 只做连接级和形状级校验，业务合法性由 Human Player Controller、Action Validator 和 PokerKit Adapter 处理。

## 5. Human 行动流

```text
Game Loop requests Human action
↓
Human Player Controller registers pending turn_id
↓
WebSocket Gateway sends action_requested with Observation
↓
Frontend submits submit_action
↓
Gateway checks connection owns player/seat
↓
Gateway passes PlayerAction to Human Controller
↓
Game Loop continues validation path
```

过期 `turn_id`、非当前玩家或非当前座位的动作必须拒绝，并返回 `action_rejected`。

## 6. 隐私与广播

Gateway 必须区分广播事件和私有事件：

广播给所有连接：

- 公共牌更新。
- 玩家公开行动。
- 公开座位和筹码变化。
- 手牌结束公开摘要。

只发给对应玩家：

- 自己底牌。
- 轮到你行动。
- 该玩家的非法动作错误。
- 玩家视角 Observation。

不能通过通用广播泄露对手未公开底牌。

## 7. 错误处理

Gateway 错误类型：

- `invalid_message`
- `unknown_event_type`
- `connection_not_bound_to_player`
- `stale_turn`
- `not_current_actor`
- `action_rejected`
- `table_unavailable`

对于业务非法动作，Gateway 应传递平台错误，不自行决定 fallback。

## 8. 测试策略

- 收到 `action_requested` 时只对应连接获得私有 Observation。
- 广播 `table_snapshot` 不包含隐藏底牌。
- `submit_action` 缺字段被拒绝。
- 过期 `turn_id` 被拒绝。
- 非绑定 player 的连接不能替其他玩家行动。
- Action Validator 返回非法动作时 Gateway 向原连接发送错误。
- fake Human Controller 可独立测试 Gateway，不依赖真实 Game Loop。

## 9. 开放问题

- WebSocket 外部事件 schema 是否需要第一版完整冻结。
- 是否需要支持旁观者。
- 是否需要支持同一用户多客户端连接。
- Human 动作是否需要 HTTP fallback。
- 第一版是否只服务本机浏览器，还是允许局域网多人访问。

