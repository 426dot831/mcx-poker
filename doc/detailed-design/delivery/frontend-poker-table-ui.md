# Frontend Poker Table UI 详细设计

## 1. 模块目标

Frontend Poker Table UI 提供本地可玩的最小 Web 牌桌。前端只展示后端状态和提交用户动作，不参与规则判定。

MVP UI 需要展示：

- 6 个座位。
- 玩家名。
- 筹码。
- 当前玩家底牌。
- 公共牌。
- 底池。
- 当前可执行动作按钮。
- 非法动作错误。

本模块不负责：

- 判断动作是否合法。
- 判断谁该行动。
- 计算 Pot。
- 判断谁赢。
- 推断隐藏信息。
- 直接调用 PokerKit。

## 2. 页面结构

MVP 第一屏就是牌桌，不做营销式 landing page。

建议界面区域：

| 区域 | 内容 |
| --- | --- |
| Table Surface | 椭圆或圆桌布局，展示公共牌和底池 |
| Seat Ring | 6 个固定座位，展示玩家名、筹码、状态、牌背或公开牌 |
| Player Hand | 当前 Human 玩家自己的底牌 |
| Action Bar | Fold、Check、Call、RaiseTo、AllIn 控件 |
| Status Strip | 当前手牌、当前行动玩家、错误提示 |
| Table Controls | 开始、暂停、继续、重开等基础控制 |

是否移动端适配、是否使用图片牌面素材，需求尚未确认。MVP 可以只要求桌面浏览器可玩。

## 3. 前端状态

前端状态只来自后端：

| 状态 | 来源 |
| --- | --- |
| `table_snapshot` | Backend API 或 WebSocket |
| `player_observation` | WebSocket 私有事件 |
| `pending_action` | `action_requested` |
| `last_error` | `action_rejected` |
| `connection_status` | WebSocket 本地状态 |

前端不得本地维护权威筹码、底池或胜负结果。

## 4. Action Bar

Action Bar 根据 Observation 的 `legal_actions` 渲染。

控件行为：

- `Fold`：提交 `Fold`。
- `Check`：提交 `Check`。
- `Call`：提交 `Call`。
- `RaiseTo`：允许输入或选择总下注额 X，提交 `RaiseTo(amount)`。
- `AllIn`：提交 `AllIn`，不附带金额。

前端可以禁用后端标记不可用的动作，但不能把禁用当成唯一校验。后端必须再次校验。

## 5. WebSocket 交互

启动：

```text
load page
↓
fetch or receive table_snapshot
↓
open websocket
↓
bind connection to human player/seat
↓
render live events
```

行动：

```text
receive action_requested
↓
render legal actions
↓
user submits PlayerAction with hand_id and turn_id
↓
wait for player_acted or action_rejected
```

前端提交动作后，在收到后端确认前不得自行推进 UI 到下一状态。

## 6. 隐藏信息展示

展示规则：

- 当前玩家自己的底牌显示正面。
- 对手未公开底牌显示背面或只显示张数。
- 公共牌显示正面。
- 已公开摊牌按后端事件展示。
- 未发出的牌不展示。

手牌结束后是否公开所有玩家底牌未确认，因此 UI 必须支持“只展示已公开牌”的结果页。

## 7. 错误展示

错误来源：

- 动作提交格式错误。
- 非当前行动玩家。
- 过期 `turn_id`。
- 非法动作。
- 牌桌暂停或重开。
- 连接断开。

非法动作错误展示后，Action Bar 应仍然停留在当前玩家行动状态，等待重新提交。

## 8. 测试策略

前端测试使用静态 mock 数据：

- 6 个座位稳定渲染。
- 当前玩家底牌显示，对手底牌隐藏。
- 公共牌、底池、筹码从 snapshot 渲染。
- `legal_actions` 控制动作按钮显示和禁用。
- `RaiseTo` 提交的是总下注额。
- `AllIn` 不携带金额。
- 收到 `action_rejected` 后不推进本地状态。
- 收到 `player_acted` 或新 snapshot 后再更新 UI。

端到端测试可使用 fake WebSocket server，不依赖真实 PokerKit。

## 9. 开放问题

- 是否需要移动端适配。
- 第一版是否只服务本机浏览器，还是需要局域网多人访问。
- 牌面素材使用文本、Unicode、简单 CSS，还是图片素材。
- 前端技术栈未指定，需实现阶段按“越简单越好、适合 Python/PokerKit 项目”选择。

