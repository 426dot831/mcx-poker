# Observation System 详细设计

## 1. 模块目标

Observation System 将 PokerKit 权威状态摘要和 Table Manager 牌桌状态转换为指定玩家可见的 Observation。

本模块的核心职责是：

- 提供当前玩家可见信息。
- 屏蔽隐藏信息。
- 提供当前玩家可执行的合法动作集合。
- 为 Human、Bot 和未来 Agent 提供同一类平台层输入。

本模块不负责：

- 调用 PokerKit 推进状态。
- 判断玩家策略。
- 渲染前端。
- 持久化手牌历史。

## 2. 输入

Observation System 的输入来自三个模块：

| 来源 | 输入 |
| --- | --- |
| PokerKit Adapter | 权威牌局状态摘要、当前行动玩家、公共牌、底池、下注状态、合法性边界 |
| Table Manager | 座位、玩家、筹码、Button、当前手牌上下文 |
| Temporary Hand Event Log | 当前手牌已发生的公开事件 |

Observation System 不直接读取 PokerKit 原始 `State` 对象。若实现需要 PokerKit 数据，必须通过 PokerKit Adapter 提供的摘要。

## 3. 输出

`PlayerObservation` 字段概念：

| 字段 | 说明 |
| --- | --- |
| `observer_player_id` | 观察者玩家 |
| `observer_seat_index` | 观察者座位 |
| `table_id` | 牌桌 |
| `hand_id` | 当前手牌 |
| `turn_id` | 当前行动机会 |
| `is_actor` | 是否轮到该观察者行动 |
| `button_seat_index` | Button 座位 |
| `own_hole_cards` | 观察者自己的底牌 |
| `board_cards` | 公共牌 |
| `visible_seats` | 各座位公开状态 |
| `pot_summary` | 底池摘要 |
| `bet_summary` | 当前下注摘要 |
| `visible_action_history` | 当前手牌公开动作历史 |
| `legal_actions` | 若轮到该玩家行动，则包含合法动作集合 |

`VisibleSeat` 字段概念：

| 字段 | 说明 |
| --- | --- |
| `seat_index` | 座位 |
| `player_id` | 玩家，可为空 |
| `player_name` | 展示名 |
| `stack` | 当前筹码 |
| `current_bet` | 当前下注轮已投入金额 |
| `status` | 公开状态，如 empty、active、folded、all_in |
| `hole_card_count` | 对手底牌数量，可用于 UI 背面牌展示 |
| `shown_cards` | 公开亮出的牌；未公开时为空 |

## 4. 隐藏信息规则

Observation 不得包含：

- 对手未公开底牌。
- 未发出的牌。
- 牌堆顺序。
- PokerKit 原始对象。
- 可通过内部状态推断牌堆顺序的信息。
- 其他玩家的私有 Controller 状态。

允许包含：

- 当前玩家自己的底牌。
- 公共牌。
- 已公开亮出的对手底牌。
- 各玩家公开座位状态。
- 各玩家筹码和当前下注金额。
- 公开动作历史。

手牌结束后是否公开所有玩家底牌，需求仍未确认。Observation System 必须支持“不公开未摊牌底牌”的默认行为。

## 5. 合法动作集合

当 `observer_seat_index` 是当前行动座位时，Observation 应包含合法动作集合。

合法动作集合来源：

```text
PokerKit Adapter extracts can_* availability and amount properties
↓
Action Validator normalizes platform action legality
↓
Observation System exposes visible legal actions
```

Adapter 已可基于 PokerKit `State.checking_or_calling_amount`、`State.min_completion_betting_or_raising_to_amount` 和 `State.max_completion_betting_or_raising_to_amount` 生成后端内部合法动作边界。MVP 中至少需要向当前行动玩家暴露动作类型是否可执行。金额边界是否作为稳定 Observation 字段对外冻结，仍待确认；但后端内部必须拥有足够信息校验 `RaiseTo(amount)`。

## 6. 生成流程

```text
read TableSnapshot
↓
read PokerKitStateSummary
↓
read public HandEvents
↓
map seat and player ids
↓
redact hidden cards
↓
attach legal actions if observer is actor
↓
return PlayerObservation
```

## 7. 不变量

- 同一时刻对不同玩家生成的 Observation 可以不同。
- 非当前玩家的 `legal_actions` 应为空或明确标记不可行动。
- Observation 中的座位数量必须为 6。
- Observation 中的行动历史只能包含公开事件。
- Observation 不能携带 PokerKit 对象引用。

## 8. 测试策略

- 给定包含 6 名玩家底牌的状态摘要，只向观察者暴露自己的底牌。
- 对手未公开底牌只显示数量或背面状态。
- 公共牌对所有观察者一致。
- 当前行动玩家收到合法动作集合。
- 非当前行动玩家不收到可提交动作。
- 摊牌公开牌只在事件明确公开后进入 `shown_cards`。
- 序列化 Observation 后不存在 PokerKit 类型名或对象 repr。

## 9. 开放问题

- Observation 是否需要区分 Bot 版、Human UI 版、LLM 版三种 schema。
- 历史动作需要保留到什么粒度：街、下注轮、每个动作、动作前后筹码变化。
- 是否需要稳定暴露最小加注额、可 call 金额、有效筹码等派生字段。
- 手牌结束后是否公开所有玩家底牌。
