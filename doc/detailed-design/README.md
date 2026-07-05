# mcx-poker 详细设计文档

状态：根据 `doc/high-level-design.md` 拆分生成  
版本：v0.1  
输入文档：`doc/high-level-design.md`、`doc/proposal.md`、`README.md`、`pyproject.toml`

## 1. 设计范围

本组文档面向 `mcx-poker` MVP 的模块详细设计。设计只覆盖需求文档和概要设计中已经确认的范围：

- 基于 `pokerkit==0.7.4` 实现普通 No-Limit Texas Hold'em 现金桌。
- 只支持一张本地长期存在的牌桌。
- 固定 6 个座位。
- 后端是唯一权威，PokerKit 是规则内核。
- Human Player 通过 Web UI 操作。
- Bot、Human 和未来玩家统一走 `Observation -> Action` 接口。
- Observation 不泄露隐藏信息。
- Action Model 不暴露 PokerKit 细节。
- All-in 是独立动作。
- Raise 语义是“加注到总下注额 X”。
- 非法动作严格拦截，报错后同一牌手重新选择。
- MVP 先能玩，不要求持久化保存每一手牌。
- LLM、GTO、Coach 第一版只保留接口，不实现具体能力。

本组文档不替以下未确认事项做决定：

- 玩家离桌、坐下、补充筹码、断线重连是否进入 MVP。
- Web UI 是否需要移动端适配。
- 第一版是否只服务本机浏览器，还是需要局域网多人访问。
- 手牌结束后，历史记录是否公开所有玩家底牌。
- 后续持久化 Hand History 使用本地文件还是 SQLite。
- API 是否认证、是否版本化、是否交付 OpenAPI。
- WebSocket 外部事件 schema 是否在第一版冻结。
- 是否支持旁观者或同一用户多客户端连接。
- Replay、数据库、统计、CI、测试覆盖率门槛等 MVP 后事项。

## 2. 目录结构

详细设计文档统一放在 `doc/detailed-design/` 下，并按职责分组：

```text
doc/detailed-design/
├── README.md
├── domain/
├── engine/
├── delivery/
├── data/
└── extensions/
```

分组规则：

- `domain/`：牌桌、玩家、观察信息等平台领域模型。
- `engine/`：动作、校验、Game Loop、PokerKit 适配器等运行时核心。
- `delivery/`：API、WebSocket、前端 UI 等交互边界。
- `data/`：当前手牌事件和后续数据系统基础。
- `extensions/`：LLM、GTO、Coach 等未来扩展边界。

## 3. 文档列表

| 模块 | 文档 |
| --- | --- |
| Table Manager | `doc/detailed-design/domain/table-manager.md` |
| Player Controller | `doc/detailed-design/domain/player-controller.md` |
| Observation System | `doc/detailed-design/domain/observation-system.md` |
| Action Model | `doc/detailed-design/engine/action-model.md` |
| Action Validator | `doc/detailed-design/engine/action-validator.md` |
| Game Loop | `doc/detailed-design/engine/game-loop.md` |
| PokerKit Adapter | `doc/detailed-design/engine/pokerkit-adapter.md` |
| Backend API | `doc/detailed-design/delivery/backend-api.md` |
| WebSocket Gateway | `doc/detailed-design/delivery/websocket-gateway.md` |
| Frontend Poker Table UI | `doc/detailed-design/delivery/frontend-poker-table-ui.md` |
| Temporary Hand Event Log | `doc/detailed-design/data/temporary-hand-event-log.md` |
| Future Extension Interfaces | `doc/detailed-design/extensions/future-extension-interfaces.md` |

## 4. 模块独立性原则

每个模块应通过明确输入、输出和错误结果与其他模块协作。测试时优先使用 fake 或 stub 替代下游模块：

- Table Manager 测试不依赖真实 PokerKit。
- Game Loop 测试不依赖真实前端或真实 Bot 策略。
- Player Controller 测试不依赖 PokerKit 内部对象。
- Observation System 使用状态摘要测试隐藏信息过滤。
- Action Validator 使用 `PlayerAction` 和合法动作集合测试。
- PokerKit Adapter 的单元测试使用适配器契约；集成测试再连接 PokerKit。
- API、WebSocket、Frontend 都只依赖平台层快照和 Action Model。
- Temporary Hand Event Log 不依赖持久化存储。
- Future Extension Interfaces 不引入 LLM、solver 或 Coach 实现依赖。

## 5. 共同约定

- 后端状态优先级高于前端和 Bot 本地状态。
- 金额类动作使用平台层 `RaiseTo(amount)` 表示“总下注额到 amount”。
- `AllIn` 不能通过特殊金额隐式表达。
- 非法动作不能推进 PokerKit 状态，不能更新筹码，不能广播为成功动作。
- 前端和未来 Agent 不直接调用 PokerKit。
- 任何对 PokerKit 内部 API 的依赖只能出现在 PokerKit Adapter 内。

## 6. PokerKit 验证状态

已核对 GitHub `uoftcprg/pokerkit` 的 `v0.7.4` tag，并在临时虚拟环境 `/tmp/mcx-poker-pokerkit-venv` 安装同版本运行 smoke test。以下 PokerKit 类名、枚举、属性和方法可在详细设计中直接引用：

- 顶层导出：`Automation`、`Mode`、`NoLimitTexasHoldem`、`State`、`Card`、`Folding`、`CheckingOrCalling`、`CompletionBettingOrRaisingTo`。
- 初始化：`NoLimitTexasHoldem.create_state(automations, ante_trimming_status, raw_antes, raw_blinds_or_straddles, min_bet, raw_starting_stacks, player_count, *, mode=Mode.TOURNAMENT, starting_board_count=1, divmod=..., rake=...) -> State`。
- 现金桌模式：`Mode.CASH_GAME`。
- 当前行动：`State.turn_index`、`State.actor_index`、`State.actor_indices`。
- 手牌状态：`State.status`。
- 筹码和下注：`State.stacks`、`State.bets`、`State.payoffs`。
- 底池：`State.total_pot_amount`、`State.pots`。
- 牌面：`State.hole_cards`、`State.hole_card_statuses`、`State.get_down_cards(player_index)`、`State.get_up_cards(player_index)`、`State.get_censored_hole_cards(player_index)`、`State.get_board_cards(board_index)`。
- 动作可用性：`State.can_fold()`、`State.can_check_or_call()`、`State.can_complete_bet_or_raise_to(amount)`。
- 金额边界：`State.checking_or_calling_amount`、`State.min_completion_betting_or_raising_to_amount`、`State.max_completion_betting_or_raising_to_amount`。
- 动作执行：`State.fold()`、`State.check_or_call()`、`State.complete_bet_or_raise_to(amount)`。
- 操作记录：`State.operations`。

实现 PokerKit Adapter 时仍需做场景验证或需求确认：

- Button 与 PokerKit player index 的完整映射。
- 少于 6 人参与时的盲注和行动顺序。
- `AllIn` 在跟注、下注、加注和不足额全下场景中的平台语义映射。
- 手牌结束后哪些底牌允许公开。
- PokerKit `ValueError` 和 warning 到平台错误码的完整映射。
