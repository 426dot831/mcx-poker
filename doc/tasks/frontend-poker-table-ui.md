# Frontend Poker Table UI 任务列表

来源：`doc/detailed-design/delivery/frontend-poker-table-ui.md`

目标：提供最小 Web 牌桌，Human Player 可以通过 UI 查看自己可见状态并提交动作；前端不参与规则判定。

## 最小任务

- [x] FE-01 选择简单前端技术栈，并记录如何与本地 Python 后端集成。
- [x] FE-02 创建第一屏牌桌页面，不做营销 landing page。
- [x] FE-03 实现 6 个固定座位布局。
- [x] FE-04 展示每个座位的玩家名、筹码和公开状态。
- [x] FE-05 展示当前 Human 玩家自己的底牌。
- [x] FE-06 对手未公开底牌只显示牌背、数量或隐藏占位。
- [x] FE-07 展示公共牌区域。
- [x] FE-08 展示底池摘要。
- [x] FE-09 展示当前手牌、当前行动玩家和连接状态。
- [x] FE-10 实现 Table Controls：开始、暂停、继续、重开。
- [x] FE-11 实现 Action Bar：`Fold`、`Check`、`Call`、`RaiseTo`、`AllIn`。
- [x] FE-12 根据 `legal_actions` 渲染按钮启用和禁用状态。
- [x] FE-13 实现 `RaiseTo` 金额输入，提交值必须是“总下注额 X”。
- [x] FE-14 实现 `AllIn` 提交时不携带金额。
- [x] FE-15 接入初始 `table_snapshot` 获取流程。
- [x] FE-16 接入 WebSocket 连接和断线状态展示。
- [x] FE-17 处理 `table_snapshot`、`hand_started`、`board_updated`、`player_acted`、`hand_ended` 事件。
- [x] FE-18 处理私有 `action_requested` 事件并记录 `hand_id`、`turn_id`。
- [x] FE-19 提交 `PlayerAction` 时带上 `player_id`、`seat_index`、`hand_id`、`turn_id`。
- [x] FE-20 提交动作后等待后端确认，不自行推进手牌状态。
- [x] FE-21 处理 `action_rejected`，展示错误并保持当前行动状态。
- [x] FE-22 手牌结束后只展示后端明确公开的摊牌信息。
- [x] FE-23 保证前端不本地计算底池、胜负、行动玩家或合法动作。
- [x] FE-24 保证页面在桌面浏览器宽度下无明显遮挡或溢出。
- [x] FE-25 提供本地开发运行方式，并与后端启动流程对齐。

## 测试与验收

- [x] FE-T01 使用静态 mock snapshot 测试 6 个座位稳定渲染。
- [x] FE-T02 测试当前玩家底牌显示，其他玩家未公开底牌隐藏。
- [x] FE-T03 测试公共牌、底池和筹码全部来自后端数据。
- [x] FE-T04 测试 `legal_actions` 可以控制动作按钮可用性。
- [x] FE-T05 测试 `RaiseTo` 提交的是总下注额，不是追加额。
- [x] FE-T06 测试 `AllIn` 提交 payload 不包含金额。
- [x] FE-T07 测试收到 `action_rejected` 后不会推进本地状态。
- [x] FE-T08 测试收到 `player_acted` 或新 snapshot 后才更新牌桌。
- [x] FE-T09 使用 fake WebSocket server 验证 Human 行动流。
- [x] FE-T10 使用浏览器手动或自动检查桌面视口下布局可用。

## 不进入本模块

- [ ] FE-X01 不实现规则判断。
- [ ] FE-X02 不实现移动端专项适配，除非后续确认。
- [ ] FE-X03 不追求高质量动画或美术级牌面素材。
- [ ] FE-X04 不直接调用 PokerKit。
