# Temporary Hand Event Log 任务列表

来源：`doc/detailed-design/data/temporary-hand-event-log.md`

目标：记录当前手牌运行期间的临时事件，为 UI 展示、调试和未来 Hand History 演进提供基础；MVP 不做跨重启持久化。

## 最小任务

- [x] HH-01 定义 `HandEvent`，包含 `hand_id`、`sequence_number`、`event_type`、`actor_player_id`、`actor_seat_index`、`public_payload`、`private_payload`、`visibility`、`created_at`。
- [x] HH-02 定义事件类型：`hand_started`、`seat_snapshot`、`hole_cards_dealt`、`board_dealt`、`action_succeeded`、`action_rejected`、`pot_updated`、`showdown`、`settlement`、`hand_ended`。
- [x] HH-03 实现 `append(event)`，自动分配当前手牌内单调递增 `sequence_number`。
- [x] HH-04 实现 `list_public_events(hand_id)`。
- [x] HH-05 实现 `list_player_events(hand_id, player_id)`。
- [x] HH-06 实现 `clear_hand(hand_id)`。
- [x] HH-07 实现 `get_last_sequence(hand_id)`。
- [x] HH-08 支持 public 事件和 player-scoped 私有事件。
- [x] HH-09 确保 `hole_cards_dealt` 只能作为 player-scoped 事件读取。
- [x] HH-10 记录手牌开始事件。
- [x] HH-11 记录本手座位和初始筹码快照。
- [x] HH-12 记录公开盲注、前注或下注摘要。
- [x] HH-13 记录公共牌更新事件。
- [x] HH-14 记录玩家成功动作事件。
- [x] HH-15 记录非法动作错误事件，但不标记为成功动作。
- [x] HH-16 记录摊牌公开信息。
- [x] HH-17 记录 settlement 摘要。
- [x] HH-18 记录 hand ended 事件。
- [x] HH-19 默认只保证当前手牌和刚结束摘要可用。
- [x] HH-20 确保公开事件不包含对手未公开底牌、未发出的牌、牌堆顺序或 PokerKit 对象。
- [x] HH-21 确保私有事件只能发给目标玩家。
- [x] HH-22 为未来持久化 Hand History 保持事件结构可扩展。

## 测试与验收

- [x] HH-T01 sequence number 在同一手牌内单调递增。
- [x] HH-T02 公开事件读取不包含私有底牌。
- [x] HH-T03 指定玩家读取能看到自己的私有底牌事件。
- [x] HH-T04 其他玩家不能读取该玩家私有底牌事件。
- [x] HH-T05 非法动作事件不会出现在成功动作列表或成功动作流中。
- [x] HH-T06 hand ended 后能读取 settlement 摘要。
- [x] HH-T07 clear hand 后事件不可再读取。
- [x] HH-T08 事件 payload 不包含 PokerKit 原始对象。

## 不进入本模块

- [ ] HH-X01 不保存每一手牌到文件或数据库。
- [ ] HH-X02 不实现 SQLite。
- [ ] HH-X03 不实现 Replay。
- [ ] HH-X04 不兼容 PokerStars 或通用 Hand History 文本格式。
- [ ] HH-X05 不实现统计系统。
