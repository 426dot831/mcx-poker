# PokerKit Adapter 任务列表

来源：`doc/detailed-design/engine/pokerkit-adapter.md`

目标：作为唯一允许 import PokerKit 的模块，负责创建手牌、读取权威状态摘要、提交平台动作，并将 PokerKit 结果映射为平台层 DTO。

## 最小任务

- [x] PK-01 创建 Adapter 模块，并限制 PokerKit import 只出现在该模块或该模块子包。
- [x] PK-02 定义 `CreateHandRequest`，包含 `hand_id`、`seat_to_player`、`starting_stacks`、`button_seat_index`、`small_blind`、`big_blind`、`ante`。
- [x] PK-03 定义 seat/player 到 PokerKit player index 的双向映射。
- [x] PK-04 实现 `create_hand`，调用 `NoLimitTexasHoldem.create_state(..., mode=Mode.CASH_GAME)`。
- [x] PK-05 启用 MVP 需要的 PokerKit 自动化：盲注、发牌、收注、烧牌、推筹码等非玩家动作。
- [x] PK-06 确保 PokerKit 不看到空座位，只为 active seats 创建 player index。
- [x] PK-07 定义 `PokerKitStateSummary` DTO。
- [x] PK-08 实现 `get_state_summary(hand_id)`，输出平台层摘要。
- [x] PK-09 在摘要中填充 `is_active`。
- [x] PK-10 在摘要中用 `State.turn_index` 映射平台层 current actor。
- [x] PK-11 在摘要中填充公共牌。
- [x] PK-12 在摘要中填充按座位映射的 stacks。
- [x] PK-13 在摘要中填充按座位映射的 bets。
- [x] PK-14 在摘要中填充底池摘要。
- [x] PK-15 在摘要中保留内部底牌信息，仅供 Observation 按视角过滤。
- [x] PK-16 在摘要中填充已公开底牌。
- [x] PK-17 在摘要中填充 legal action boundaries。
- [x] PK-18 实现 `Fold` 到 `State.fold()` 的映射。
- [x] PK-19 实现 `Check` 到 `State.check_or_call()` 的映射，并要求 call 金额为 0。
- [x] PK-20 实现 `Call` 到 `State.check_or_call()` 的映射。
- [x] PK-21 实现 `RaiseTo(amount)` 到 `State.complete_bet_or_raise_to(amount)` 的映射。
- [x] PK-22 实现 `AllIn` 独立映射逻辑，根据 call 金额、min/max raise-to 和可用性选择 call 或 max raise-to。
- [x] PK-23 提交动作前校验平台 actor 与 PokerKit 当前 actor 一致。
- [x] PK-24 捕获 PokerKit 拒绝动作并映射为平台错误。
- [x] PK-25 定义 `HandSettlement` DTO。
- [x] PK-26 实现手牌结束后的 settlement 提取：final stacks、payoffs、winners、final board、showdown summary、operations summary。
- [x] PK-27 确保 Adapter 输出不包含 PokerKit `State` 对象。
- [x] PK-28 确保错误对象不向前端泄露 PokerKit 原始异常。
- [x] PK-29 为 Button 与 PokerKit player index 映射添加显式验证或 TODO 注记。
- [x] PK-30 为少于 6 人参与时的 active seats 映射添加测试覆盖。

## 测试与验收

- [x] PK-T01 单元测试 seat/player 与 PokerKit index 映射正确。
- [x] PK-T02 单元测试状态摘要不包含 PokerKit `State`。
- [x] PK-T03 单元测试 `Fold`、`Call`、`RaiseTo` 进入正确 Adapter 分支。
- [x] PK-T04 单元测试 PokerKit 异常映射为平台错误。
- [x] PK-T05 集成测试使用 `pokerkit==0.7.4` 初始化 6 人现金桌。
- [x] PK-T06 集成测试验证自动化后首个 actor。
- [x] PK-T07 集成测试验证 preflop call 后 stacks 和 bets 变化。
- [x] PK-T08 集成测试验证 call 金额、min raise-to、max raise-to 边界。
- [x] PK-T09 集成测试验证合法 `RaiseTo(4)` 成功。
- [x] PK-T10 集成测试验证非法 `RaiseTo(2)` 和 `RaiseTo(201)` 失败。
- [x] PK-T11 集成测试验证 fold 到手牌结束后可读取 settlement。
- [x] PK-T12 集成测试验证 `AllIn` 在 call、raise-to max、短筹 all-in 场景下映射正确。

## 不进入本模块

- [ ] PK-X01 不管理长期座位和筹码生命周期。
- [ ] PK-X02 不实现 Bot 策略。
- [ ] PK-X03 不渲染前端。
- [ ] PK-X04 不持久化 Hand History。
