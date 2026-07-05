# Observation System 任务列表

来源：`doc/detailed-design/domain/observation-system.md`

目标：将 Table Manager 快照、PokerKit Adapter 摘要和当前手牌事件转换为指定玩家可见的 `PlayerObservation`，并严格过滤隐藏信息。

## 最小任务

- [x] OBS-01 定义 `PlayerObservation` 数据结构。
- [x] OBS-02 定义 `VisibleSeat` 数据结构。
- [x] OBS-03 定义 `PotSummary` 或等价底池摘要结构。
- [x] OBS-04 定义 `BetSummary` 或等价下注摘要结构。
- [x] OBS-05 定义 Observation 构建输入：`TableSnapshot`、`PokerKitStateSummary`、公开 `HandEvent`。
- [x] OBS-06 实现座位和玩家 id 映射逻辑，输出固定 6 个 visible seats。
- [x] OBS-07 为观察者填充自己的底牌。
- [x] OBS-08 对其他玩家未公开底牌只输出 `hole_card_count` 或隐藏占位。
- [x] OBS-09 填充公共牌，保证所有观察者一致。
- [x] OBS-10 填充各座位公开状态、筹码和本轮下注额。
- [x] OBS-11 填充底池摘要。
- [x] OBS-12 填充当前下注摘要。
- [x] OBS-13 从 Temporary Hand Event Log 填充公开动作历史。
- [x] OBS-14 只在观察者是当前 actor 时附加 `legal_actions`。
- [x] OBS-15 非当前 actor 的 `legal_actions` 为空或明确不可行动。
- [x] OBS-16 支持摊牌公开牌：只有事件或 Adapter 摘要明确公开后才填入 `shown_cards`。
- [x] OBS-17 默认支持“不公开未摊牌底牌”的手牌结束展示。
- [x] OBS-18 确保 Observation 输出不包含 PokerKit 原始对象。
- [x] OBS-19 确保 Observation 输出不包含未发出的牌、牌堆顺序或 Controller 私有状态。
- [x] OBS-20 提供供 WebSocket 私有事件复用的玩家视角 DTO。

## 测试与验收

- [x] OBS-T01 给定 6 名玩家底牌，只向观察者暴露自己的底牌。
- [x] OBS-T02 测试对手未公开底牌只显示数量或背面状态。
- [x] OBS-T03 测试公共牌对所有观察者一致。
- [x] OBS-T04 测试当前行动玩家收到合法动作集合。
- [x] OBS-T05 测试非当前行动玩家不能收到可提交动作。
- [x] OBS-T06 测试摊牌公开牌只在事件明确公开后进入 `shown_cards`。
- [x] OBS-T07 测试 Observation 序列化后不存在 PokerKit 类型名或对象 repr。
- [x] OBS-T08 测试输出座位数量始终为 6。
- [x] OBS-T09 测试可见动作历史只包含公开事件。

## 不进入本模块

- [ ] OBS-X01 不推进 PokerKit 状态。
- [ ] OBS-X02 不判断玩家策略。
- [ ] OBS-X03 不渲染前端。
- [ ] OBS-X04 不持久化 Hand History。
