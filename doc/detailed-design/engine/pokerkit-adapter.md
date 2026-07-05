# PokerKit Adapter 详细设计

## 1. 模块目标

PokerKit Adapter 是平台层与 PokerKit 的唯一规则交互边界。它负责初始化 PokerKit 状态、读取权威状态摘要、提交平台层动作，并将 PokerKit 结果转换为平台层数据。

Adapter 不负责：

- Table Manager 长期座位和筹码生命周期。
- Player Controller 策略。
- Frontend 展示。
- 持久化手牌历史。
- 业务侧未确认的产品决策。

## 2. 已验证 PokerKit 接口

已核对 GitHub `uoftcprg/pokerkit` 的 `v0.7.4` tag，并在临时 venv `/tmp/mcx-poker-pokerkit-venv` 安装 `pokerkit==0.7.4` 运行 smoke test。以下接口可以在实现中直接引用。

顶层导出：

```text
Automation
Mode
NoLimitTexasHoldem
State
Card
Folding
CheckingOrCalling
CompletionBettingOrRaisingTo
Pot
```

初始化签名：

```text
NoLimitTexasHoldem.create_state(
    automations,
    ante_trimming_status,
    raw_antes,
    raw_blinds_or_straddles,
    min_bet,
    raw_starting_stacks,
    player_count,
    mode=Mode.CASH_GAME,
)
```

状态读取：

| PokerKit 接口 | Adapter 用途 |
| --- | --- |
| `State.status` | 判断手牌是否仍活动 |
| `State.turn_index` | 读取当前需要决策的 player index，覆盖下注行动、摊牌等需要玩家决策的阶段 |
| `State.actor_index` | 读取当前下注行动玩家；只用于投注动作阶段 |
| `State.actor_indices` | 调试或验证投注行动队列 |
| `State.stacks` | 当前 PokerKit player index 的筹码 |
| `State.bets` | 当前下注轮各 player index 已投入额 |
| `State.payoffs` | 当前手牌内各 player index 的盈亏累计 |
| `State.total_pot_amount` | 当前总底池；源码说明该值包含未收集的 outstanding bets |
| `State.pots` | 主池和边池迭代器 |
| `State.operations` | PokerKit 已执行操作列表，用于摘要和调试 |

牌面读取：

| PokerKit 接口 | Adapter 用途 |
| --- | --- |
| `State.hole_cards` | 内部读取完整底牌，再由 Observation 过滤 |
| `State.hole_card_statuses` | 判断底牌公开状态 |
| `State.get_down_cards(player_index)` | 读取指定玩家未公开底牌，禁止直接外发给非本人 |
| `State.get_up_cards(player_index)` | 读取指定玩家公开牌 |
| `State.get_censored_hole_cards(player_index)` | 读取隐藏牌替换为 `Card.UNKNOWN` 后的牌面 |
| `State.get_board_cards(board_index)` | 读取公共牌；MVP 默认使用 `board_index=0` |

动作和金额：

| PokerKit 接口 | Adapter 用途 |
| --- | --- |
| `State.can_fold()` | 判断 `Fold` 是否可用 |
| `State.can_check_or_call()` | 判断 `Check` 或 `Call` 是否可用 |
| `State.can_complete_bet_or_raise_to(amount)` | 判断 `RaiseTo(amount)` 是否可用 |
| `State.checking_or_calling_amount` | 区分平台 `Check` 与 `Call`，并给出 call 金额 |
| `State.min_completion_betting_or_raising_to_amount` | 读取最小 raise-to 金额 |
| `State.max_completion_betting_or_raising_to_amount` | 读取最大 raise-to 金额 |
| `State.fold()` | 执行 fold，返回 `Folding` |
| `State.check_or_call()` | 执行 check 或 call，返回 `CheckingOrCalling` |
| `State.complete_bet_or_raise_to(amount)` | 执行 bet/raise-to，返回 `CompletionBettingOrRaisingTo` |

## 3. PokerKit 自动化策略

MVP 目标是让 Game Loop 只处理玩家决策。因此 Adapter 应默认启用 PokerKit 的非玩家动作自动化：

```text
Automation.ANTE_POSTING
Automation.BET_COLLECTION
Automation.BLIND_OR_STRADDLE_POSTING
Automation.CARD_BURNING
Automation.HOLE_DEALING
Automation.BOARD_DEALING
Automation.HOLE_CARDS_SHOWING_OR_MUCKING
Automation.HAND_KILLING
Automation.CHIPS_PUSHING
Automation.CHIPS_PULLING
```

是否启用 `Automation.RUNOUT_COUNT_SELECTION` 取决于是否支持多次发牌。MVP 需求未确认多次发牌，因此不作为必须项。

## 4. 初始化契约

`create_hand` 输入字段概念：

| 字段 | 说明 |
| --- | --- |
| `hand_id` | 平台层手牌 id |
| `seat_to_player` | 本手参与座位到玩家映射 |
| `starting_stacks` | 按 PokerKit player index 排列的起始筹码 |
| `button_seat_index` | 本手 Button |
| `small_blind` | 小盲 |
| `big_blind` | 大盲，同时作为 No-Limit 最小下注 |
| `ante` | 前注；MVP 可为 0，具体配置未确认 |

Adapter 内部需要维护映射：

```text
seat_index <-> pokerkit_player_index
player_id <-> pokerkit_player_index
hand_id -> PokerKit State
```

PokerKit 不应看到空座位。若 6 个固定座位中只有部分玩家参与本手，Adapter 应只为 active seats 创建 PokerKit player index，并通过映射还原座位。

## 5. 状态摘要

Adapter 输出 `PokerKitStateSummary`，供 Game Loop、Observation System 和 Table Manager 使用。

字段概念：

| 字段 | 说明 |
| --- | --- |
| `hand_id` | 手牌 |
| `is_active` | 对应 PokerKit `State.status` |
| `current_actor` | 由 `State.turn_index` 映射出的平台 actor |
| `board_cards` | 公共牌 |
| `stacks` | 按座位映射后的筹码 |
| `bets` | 当前下注轮各座位已投入金额 |
| `pot_summary` | 来自 `State.total_pot_amount` 和 `State.pots` 的底池摘要 |
| `hole_cards_by_seat` | 内部字段，只供 Observation System 按玩家视角过滤 |
| `shown_cards_by_seat` | 已公开底牌 |
| `legal_action_boundaries` | 当前 actor 的动作可用性和金额边界 |
| `operations_summary` | 来自 `State.operations` 的平台层操作摘要 |

摘要不能把 PokerKit `State` 对象传出 Adapter。

## 6. 动作映射

平台动作到 PokerKit 操作：

| Platform Action | PokerKit 操作 |
| --- | --- |
| `Fold` | `State.fold()` |
| `Check` | `State.check_or_call()`，前提是 `State.checking_or_calling_amount == 0` |
| `Call` | `State.check_or_call()` |
| `RaiseTo(amount)` | `State.complete_bet_or_raise_to(amount)` |
| `AllIn` | 根据当前状态映射为 `State.check_or_call()` 或 `State.complete_bet_or_raise_to(State.max_completion_betting_or_raising_to_amount)` |

`AllIn` 的映射必须保持平台语义独立：

- 如果 `State.checking_or_calling_amount` 大于 0，且玩家当前可用筹码不足以形成合法 raise-to，平台 `AllIn` 应调用 `State.check_or_call()`。
- 如果 `State.max_completion_betting_or_raising_to_amount` 非空，且该金额对应玩家当前本轮可投入总额，平台 `AllIn` 可调用 `State.complete_bet_or_raise_to(max_amount)`。
- 具体分类必须由 Adapter 使用 `checking_or_calling_amount`、`min_completion_betting_or_raising_to_amount`、`max_completion_betting_or_raising_to_amount` 和 `can_complete_bet_or_raise_to(max_amount)` 共同判断。

## 7. 合法动作边界

Adapter 从 PokerKit 读取动作可用性和金额边界：

- `State.can_fold()`
- `State.can_check_or_call()`
- `State.can_complete_bet_or_raise_to(amount)`
- `State.checking_or_calling_amount`
- `State.min_completion_betting_or_raising_to_amount`
- `State.max_completion_betting_or_raising_to_amount`

在 6 人现金桌、盲注 `(1, 2)`、筹码 200 的验证样例中：

- 自动化初始化后 `State.turn_index == 2`。
- `State.checking_or_calling_amount == 2`。
- `State.min_completion_betting_or_raising_to_amount == 4`。
- `State.max_completion_betting_or_raising_to_amount == 200`。
- `State.can_complete_bet_or_raise_to(200)` 为 `True`。
- `State.can_complete_bet_or_raise_to(201)` 为 `False`。

实现不能只依赖平台金额计算绕过 PokerKit。`RaiseTo(amount)` 必须最终通过 `State.can_complete_bet_or_raise_to(amount)` 或 `State.complete_bet_or_raise_to(amount)` 的 PokerKit 校验。

## 8. 结算输出

一手结束时，Adapter 输出 `HandSettlement`：

| 字段 | 说明 |
| --- | --- |
| `hand_id` | 手牌 |
| `final_stacks` | 按座位映射后的最终筹码 |
| `payoffs` | 来自 `State.payoffs` 并按座位映射后的盈亏 |
| `winners` | 赢家座位和公开手牌摘要 |
| `final_board` | 来自 `State.get_board_cards(0)` 的最终公共牌 |
| `showdown_summary` | 摊牌摘要 |
| `operations_summary` | 来自 `State.operations` 的 PokerKit 操作摘要，用于事件日志和调试 |

手牌结束后是否公开所有玩家底牌仍未确认。Adapter 可以读取完整结果，但 Observation 和事件输出必须按需求过滤。

## 9. 错误映射

Adapter 应捕获 PokerKit 异常并转换成平台错误：

| 平台错误码 | 说明 |
| --- | --- |
| `pokerkit_illegal_action` | PokerKit 拒绝动作 |
| `pokerkit_state_mismatch` | 当前状态不允许该操作 |
| `pokerkit_hand_not_active` | 手牌已结束 |
| `pokerkit_actor_mismatch` | 平台 actor 与 PokerKit 当前 actor 不一致 |
| `pokerkit_adapter_bug` | 映射或内部状态不一致 |

错误对象不得泄露 PokerKit 原始异常对象给前端。

## 10. 不变量

- 只有 Adapter 可以 import PokerKit。
- Adapter 输出平台层 DTO，不输出 PokerKit `State`。
- 任何动作提交前必须校验平台 actor 与 PokerKit `turn_index` 一致。
- PokerKit 拒绝动作时，Adapter 不伪造成功结果。
- Table Manager 只根据 Adapter 的 settlement 更新长期筹码。

## 11. 测试策略

单元测试：

- seat/player 与 PokerKit index 映射正确。
- 状态摘要不包含 PokerKit `State`。
- `Fold`、`Call`、`RaiseTo` 动作映射到正确 Adapter 分支。
- PokerKit 异常映射为平台错误。

集成测试：

- 使用 `pokerkit==0.7.4` 初始化 6 人现金桌。
- 验证自动化后首个 actor。
- 验证 preflop call 后 stacks 和 bets 变化。
- 验证 `checking_or_calling_amount == 2`、`min_completion_betting_or_raising_to_amount == 4`、`max_completion_betting_or_raising_to_amount == 200`。
- 验证合法 `RaiseTo(4)` 成功。
- 验证非法 `RaiseTo(2)` 和 `RaiseTo(201)` 失败。
- 验证 fold 到手牌结束后可读取 settlement。

## 12. 开放问题

- 初始筹码、大小盲、前注是否由配置文件、API 命令或硬编码 MVP 默认值提供。
- 6 个固定座位中少于 6 人时，开局最少人数和座位到 PokerKit player index 的 Button 规则需要确认。
- 是否支持 run it twice 或多 board。
- 手牌结束后是否公开所有玩家底牌。
