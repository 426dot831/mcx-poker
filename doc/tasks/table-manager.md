# Table Manager 任务列表

来源：`doc/detailed-design/domain/table-manager.md`

目标：管理唯一一张长期存在的本地牌桌，负责固定 6 个座位、玩家、筹码、Button、手牌生命周期、暂停、继续和重开。

## 最小任务

- [x] TM-01 定义 `TableState`，包含 `table_id`、`seat_count`、`status`、`seats`、`button_seat_index`、`current_hand_id`、`hand_context`。
- [x] TM-02 定义 `SeatState`，包含 `seat_index`、`player_id`、`player_name`、`controller_type`、`stack`、`status`。
- [x] TM-03 定义 `HandContext`，包含 `hand_id`、`button_seat_index`、`active_seat_indexes`、`starting_stacks`、`adapter_hand_ref`。
- [x] TM-04 定义 `TableSnapshot`，只包含公开牌桌状态。
- [x] TM-05 实现 `initialize_table`，创建固定 6 个空座位。
- [x] TM-06 实现座位索引校验，拒绝 0 到 5 之外的座位。
- [x] TM-07 实现 `seat_player`，支持玩家入座、展示名、controller 类型和初始筹码。
- [x] TM-08 拒绝同一玩家同时占用多个座位。
- [x] TM-09 拒绝已占用座位再次入座。
- [x] TM-10 校验入座筹码必须有效。
- [x] TM-11 实现 `start_table`，从可开始状态进入 running。
- [x] TM-12 明确 MVP 最小开局人数默认策略，并在代码或配置中集中表达。
- [x] TM-13 实现 `create_next_hand`，生成 hand id、active seats 和 starting stacks。
- [x] TM-14 在 `create_next_hand` 中通过 PokerKit Adapter 创建手牌，不直接调用 PokerKit。
- [x] TM-15 实现 `apply_hand_settlement`，校验 settlement 属于当前手牌。
- [x] TM-16 根据 settlement 更新长期筹码。
- [x] TM-17 一手正式结束后移动 Button。
- [x] TM-18 running 状态下一手结束后可创建下一手。
- [x] TM-19 实现 `pause_table`，阻止新的推进动作。
- [x] TM-20 实现 `resume_table`，从 paused 恢复。
- [x] TM-21 实现 `reset_table`，清理当前手牌和座位/筹码状态到约定初始状态。
- [x] TM-22 实现 `get_table_snapshot`，输出公开快照。
- [x] TM-23 确保快照不包含对手未公开底牌、未发出的牌或 PokerKit 对象。
- [x] TM-24 确保非法动作不会触发 settlement 或筹码变更。
- [x] TM-25 确保 Button 只在一手正式结束后移动。
- [x] TM-26 为牌桌状态冲突、座位不存在、玩家重复、结算不匹配等情况返回平台错误。

## 测试与验收

- [x] TM-T01 初始化后固定 6 个座位。
- [x] TM-T02 玩家入座成功。
- [x] TM-T03 重复玩家入座失败。
- [x] TM-T04 已占用座位不能重复入座。
- [x] TM-T05 非法 seat index 被拒绝。
- [x] TM-T06 `start_table` 只在满足最小开局条件时成功。
- [x] TM-T07 `create_next_hand` 生成正确 active seats 和 starting stacks。
- [x] TM-T08 一手结算后筹码按 settlement 更新。
- [x] TM-T09 一手结束后 Button 移动。
- [x] TM-T10 暂停状态不创建下一手。
- [x] TM-T11 reset 后 pending hand context 被清理。
- [x] TM-T12 快照不包含隐藏牌或 PokerKit 对象。

## 不进入本模块

- [ ] TM-X01 不实现扑克规则判定。
- [ ] TM-X02 不直接 import PokerKit。
- [ ] TM-X03 不实现玩家策略。
- [ ] TM-X04 不实现前端展示。
- [ ] TM-X05 不实现玩家离桌、补充筹码、断线重连，除非后续确认。
