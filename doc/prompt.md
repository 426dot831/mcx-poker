# Vibe Coding 起始 Prompt：mcx-poker MVP

你是 `mcx-poker` 的 Vibe Coding 主 Agent。你的任务是在无人参与的情况下，从当前仓库文档出发，实现一个本地可玩的 MVP，并通过完整的自动化验证。

工作目录：`/Users/machengqi/Documents/mcx-poker`

## 1. 必须先阅读的输入

开始编码前，主 Agent 必须完整阅读并提炼以下文档：

- `doc/proposal.md`
- `doc/high-level-design.md`
- `doc/detailed-design/README.md`
- `doc/detailed-design/domain/table-manager.md`
- `doc/detailed-design/domain/observation-system.md`
- `doc/detailed-design/domain/player-controller.md`
- `doc/detailed-design/engine/action-model.md`
- `doc/detailed-design/engine/action-validator.md`
- `doc/detailed-design/engine/pokerkit-adapter.md`
- `doc/detailed-design/engine/game-loop.md`
- `doc/detailed-design/data/temporary-hand-event-log.md`
- `doc/detailed-design/delivery/backend-api.md`
- `doc/detailed-design/delivery/websocket-gateway.md`
- `doc/detailed-design/delivery/frontend-poker-table-ui.md`
- `doc/detailed-design/extensions/future-extension-interfaces.md`
- `doc/tasks/*.md`
- `pyproject.toml`
- `README.md`

不要只按本 Prompt 编码；本 Prompt 是执行编排，设计细节和验收清单以 `doc/` 为准。

## 2. 总目标

实现 `mcx-poker` MVP：一个基于 `pokerkit==0.7.4` 的本地 No-Limit Texas Hold'em 现金桌平台层。

最终交付必须满足：

- 一张本地长期存在的牌桌。
- 固定 6 个座位。
- 普通 No-Limit Texas Hold'em 现金桌，不做锦标赛。
- 后端是唯一权威。
- PokerKit 只负责规则、状态转移、下注合法性、胜负判定和结算。
- `mcx-poker` 负责牌桌、座位、玩家、Observation、Action、Game Loop、API、WebSocket、最小 Web UI 和未来扩展接口边界。
- Human Player 通过 Web UI 操作。
- 至少一个 Bot Controller 通过同一 `Observation -> Action` 契约行动。
- Action Model 支持 `Fold`、`Check`、`Call`、`RaiseTo(amount)`、`AllIn`。
- `RaiseTo(amount)` 的 `amount` 表示“本轮总下注额到 amount”，不是追加金额。
- `AllIn` 是独立动作，不能用特殊金额表达。
- 非法动作必须严格拦截，不能推进状态；报错后同一行动玩家重新选择。
- Observation 和所有前端/事件输出不得泄露对手未公开底牌、未发出的牌、牌堆顺序或 PokerKit 内部对象。
- LLM、GTO、Coach 第一版只保留接口边界，不实现真实能力。

## 3. 无人工参与执行规则

整个实现过程不得等待人工确认。若文档中存在未确认事项，按以下 MVP 默认策略执行，并把关键决策记录到 `doc/implementation-decisions.md`：

- Python 版本沿用 `pyproject.toml`：`>=3.11`。
- 目标运行环境是本机开发原型；不承诺线上部署、账号体系、认证、局域网多人访问或长期运行稳定性。
- 后端默认使用 FastAPI + Uvicorn；如果实现时发现更简单且更适合当前仓库的 Python 方案，也可替换，但必须记录理由。
- Human 动作默认走 WebSocket；HTTP API 只负责牌桌控制、查询和预留 `submit_action` 边界。
- 前端默认使用后端直接服务的静态 HTML/CSS/原生 JavaScript，不引入复杂前端构建链。
- 第一版只要求桌面浏览器可用，不做移动端专项适配。
- 牌面素材默认使用文本、Unicode 或简单 CSS，不追求动画和美术级素材。
- 默认牌桌参数集中配置：6 seats、small blind = 1、big blind = 2、ante = 0、default starting stack = 200、minimum active players = 2。
- Bot MVP 至少实现一个简单、可测试、只从 `legal_actions` 中选择动作的 Bot；优先确定性策略，必要随机性必须支持固定 seed。
- 手牌结束后默认只公开 PokerKit/事件明确公开的牌，不公开未摊牌或 muck 的隐藏底牌。
- 不实现玩家离桌、补充筹码、断线托管、旁观者、多客户端特殊语义、持久化 Hand History、Replay、SQLite、统计、真实 LLM、真实 GTO Solver、Coach 页面、OpenAPI 或 CI，除非完成 MVP 必需闭环时无法避免。

如果某个默认策略与文档中已确认的 P0 要求冲突，以 `doc/` 已确认 P0 要求为准。

## 4. 主 Agent 职责

主 Agent 负责整体进度、依赖顺序、子 Agent 派发、集成和最终验收。

主 Agent 必须：

1. 建立任务板，任务来源为 `doc/tasks/progress.md` 和每个模块任务文件。
2. 先完成项目工具链基础：pytest、mypy、ruff 配置和运行命令。
3. 按建议顺序派发子 Agent，每个模块一个子 Agent。
4. 每个子 Agent 开始前，明确该模块输入文档、可修改范围、验收清单和依赖模块。
5. 每个子 Agent 完成后，主 Agent 负责审查代码边界、运行相关测试、修复集成问题。
6. 只有当模块代码、单元测试、相关集成测试、mypy、ruff 都通过时，才能在 `doc/tasks/progress.md` 和模块任务文件中勾选完成项。
7. 最终运行全量验证，并留下本地运行说明。

如果 Vibe Coding 环境提供真正的子 Agent 能力，必须使用子 Agent。若环境没有子 Agent 工具，则以隔离实施阶段模拟子 Agent，但仍必须保留每个模块独立的输入、范围、验收和总结。

## 5. 全局工程约束

- 优先使用 `dataclasses`、`Enum`、`Protocol`、显式 DTO 和类型标注。
- 模块边界返回平台层 DTO 或稳定错误对象，不把 PokerKit 原始对象、异常或 repr 泄露给其他模块或前端。
- 只有 PokerKit Adapter 模块或其子包允许 import PokerKit。
- Game Loop、Table Manager、Observation、Player Controller、API、WebSocket、Frontend 都不得直接 import PokerKit。
- 内部金额统一使用整数筹码单位，不使用浮点金额作为核心输入。
- 公共 API、WebSocket payload 和前端状态必须可序列化。
- 测试优先使用 fake/stub 隔离下游模块；只有 Adapter 和最终闭环测试使用真实 PokerKit。
- 不要扩大 MVP 范围。未确认事项按第 3 节处理。

建议包结构可基于现有目录扩展：

```text
src/mcx_poker/
  engine/
    actions.py
    validator.py
    pokerkit_adapter.py
    game_loop.py
  table/
    manager.py
  history/
    events.py
  players/
    controllers.py
  observation/
    builder.py
  delivery/
    api.py
    websocket.py
    static/
  extensions/
    interfaces.py
```

实际结构可以调整，但必须保持模块边界清晰。

## 6. 必须通过的验证命令

主 Agent 在最终交付前必须确保以下命令通过：

```bash
python -m pytest
python -m mypy src tests
python -m ruff check .
python -m ruff format --check .
```

还必须额外检查 PokerKit import 边界：

```bash
rg "from pokerkit|import pokerkit" src tests
```

该检查结果中，PokerKit import 只能出现在 PokerKit Adapter 模块或该模块测试中。

如果需要格式化，先运行：

```bash
python -m ruff format .
```

## 7. 子 Agent 派发顺序

### 7.1 Project Foundation Agent

输入：

- `pyproject.toml`
- `README.md`
- 全部 `doc/` 设计文档

任务：

- 配置 pytest、mypy、ruff。
- 添加必要运行依赖和开发依赖。
- 选择并记录后端/API/WebSocket/静态前端方案。
- 建立基础测试目录、类型检查配置和本地运行入口。

验收：

- `python -m pytest` 可以运行。
- `python -m mypy src tests` 可以运行。
- `python -m ruff check .` 可以运行。
- `doc/implementation-decisions.md` 记录 MVP 默认策略。

### 7.2 Action Model Agent

输入：

- `doc/detailed-design/engine/action-model.md`
- `doc/tasks/action-model.md`

任务：

- 完成 AM-01 到 AM-15。
- 定义动作枚举、`PlayerAction`、`LegalAction`、`LegalActionSet`、`ActionError`、来源枚举和序列化/反序列化。
- 实现基础 shape 校验。

验收：

- 完成 AM-T01 到 AM-T07。
- 模块不 import PokerKit。

### 7.3 PokerKit Adapter Agent

输入：

- `doc/detailed-design/engine/pokerkit-adapter.md`
- `doc/tasks/pokerkit-adapter.md`
- Action Model 代码

任务：

- 完成 PK-01 到 PK-30。
- 封装 `pokerkit==0.7.4`，创建现金桌手牌，读取摘要，提交动作，提取 settlement。
- 实现 seat/player 与 PokerKit player index 映射。
- 实现 `AllIn` 独立映射。

验收：

- 完成 PK-T01 到 PK-T12。
- Adapter 输出不包含 PokerKit `State`。
- PokerKit 异常映射为平台错误。

### 7.4 Table Manager Agent

输入：

- `doc/detailed-design/domain/table-manager.md`
- `doc/tasks/table-manager.md`
- PokerKit Adapter 契约

任务：

- 完成 TM-01 到 TM-26。
- 管理固定 6 座、玩家入座、筹码、Button、手牌上下文、暂停/继续/重开。

验收：

- 完成 TM-T01 到 TM-T12。
- 快照不包含隐藏牌或 PokerKit 对象。
- 不直接 import PokerKit。

### 7.5 Temporary Hand Event Log Agent

输入：

- `doc/detailed-design/data/temporary-hand-event-log.md`
- `doc/tasks/temporary-hand-event-log.md`

任务：

- 完成 HH-01 到 HH-22。
- 支持 public 和 player-scoped 事件，保证同一手牌内 sequence number 单调递增。

验收：

- 完成 HH-T01 到 HH-T08。
- 私有底牌事件只能由目标玩家读取。

### 7.6 Observation System Agent

输入：

- `doc/detailed-design/domain/observation-system.md`
- `doc/tasks/observation-system.md`
- Table Snapshot、PokerKit Summary、Hand Event 契约

任务：

- 完成 OBS-01 到 OBS-20。
- 构建 `PlayerObservation` 和 `VisibleSeat`。
- 严格过滤隐藏信息。

验收：

- 完成 OBS-T01 到 OBS-T09。
- 序列化后无 PokerKit 类型名、对象 repr、未发出牌或对手隐藏底牌。

### 7.7 Player Controller Agent

输入：

- `doc/detailed-design/domain/player-controller.md`
- `doc/tasks/player-controller.md`
- Observation 和 Action Model 契约

任务：

- 完成 PC-01 到 PC-20。
- 实现 Controller Registry、Human pending action、最小 Bot Controller、future_agent 类型预留。

验收：

- 完成 PC-T01 到 PC-T09。
- Human Controller 支持 pending `turn_id`，非法动作后保持等待。
- Bot 只能从 `legal_actions` 中选择动作。

### 7.8 Action Validator Agent

输入：

- `doc/detailed-design/engine/action-validator.md`
- `doc/tasks/action-validator.md`
- Action Model、Table Snapshot、LegalActionSet

任务：

- 完成 AV-01 到 AV-20。
- 校验 `hand_id`、`turn_id`、玩家座位、当前 actor、动作可用性和金额边界。

验收：

- 完成 AV-T01 到 AV-T12。
- Validator 不修改状态、不记录事件、不广播、不调用 Adapter、不 import PokerKit。

### 7.9 Game Loop Agent

输入：

- `doc/detailed-design/engine/game-loop.md`
- `doc/tasks/game-loop.md`
- Table Manager、Adapter、Observation、Controller、Validator、Event Log 契约

任务：

- 完成 GL-01 到 GL-27。
- 串联一手牌生命周期、非法动作重试、事件记录、状态广播边界和一手结束 settlement。

验收：

- 完成 GL-T01 到 GL-T10。
- Validator 或 Adapter 拒绝动作时，同一 actor 再次请求行动。
- 一手结束后必须通过 Table Manager 应用 settlement。
- 不 import PokerKit。

### 7.10 Backend API Agent

输入：

- `doc/detailed-design/delivery/backend-api.md`
- `doc/tasks/backend-api.md`
- Table Manager 契约

任务：

- 完成 API-01 到 API-20。
- 提供初始化、入座、开始、暂停、继续、重开、查询当前牌桌等本地控制能力。
- 统一 `ApiResponse` 和错误映射。

验收：

- 完成 API-T01 到 API-T09。
- 通用 `get_table` 不泄露私有底牌或 PokerKit 对象。
- 不实现认证、账号、多桌或 OpenAPI。

### 7.11 WebSocket Gateway Agent

输入：

- `doc/detailed-design/delivery/websocket-gateway.md`
- `doc/tasks/websocket-gateway.md`
- Human Controller、Observation、Event Log、Table Snapshot 契约

任务：

- 完成 WS-01 到 WS-23。
- 管理连接、绑定 human player/seat、接收 `submit_action`、发送广播和私有事件。

验收：

- 完成 WS-T01 到 WS-T08。
- `action_requested`、`hole_cards_dealt`、`action_rejected` 等私有事件只发给对应玩家。
- Gateway 不判断扑克规则，不 import PokerKit。

### 7.12 Frontend Poker Table UI Agent

输入：

- `doc/detailed-design/delivery/frontend-poker-table-ui.md`
- `doc/tasks/frontend-poker-table-ui.md`
- API/WebSocket 事件契约

任务：

- 完成 FE-01 到 FE-25。
- 实现第一屏牌桌页面，桌面浏览器可用。
- 展示 6 座、玩家名、筹码、底牌、公共牌、底池、行动按钮、错误和连接状态。
- 通过 WebSocket 提交 Human `PlayerAction`。

验收：

- 完成 FE-T01 到 FE-T10。
- 前端不计算底池、胜负、行动玩家或合法动作。
- `RaiseTo` 提交总下注额。
- `AllIn` payload 不携带金额。
- 收到 `action_rejected` 后不推进本地状态。

### 7.13 Future Extension Interfaces Agent

输入：

- `doc/detailed-design/extensions/future-extension-interfaces.md`
- `doc/tasks/future-extension-interfaces.md`

任务：

- 完成 EXT-01 到 EXT-18。
- 定义 LLM、GTO、Coach、Replay 的接口边界和 fake controller。
- 不引入真实 LLM、solver、数据库或外部服务依赖。

验收：

- 完成 EXT-T01 到 EXT-T05。
- 扩展接口不能 import PokerKit，不能读取隐藏信息，失败不能阻塞 MVP 闭环。

### 7.14 Integration QA Agent

输入：

- 全部代码和测试
- `doc/tasks/progress.md`

任务：

- 运行全量测试、mypy、ruff。
- 运行 PokerKit import 边界检查。
- 执行最小本地可玩闭环验证：
  - 初始化 6 座牌桌。
  - 至少 2 名玩家可入座。
  - 可启动普通 NLHE cash hand。
  - Bot 可通过 `Observation -> Action` 行动。
  - Human pending action 可通过 WebSocket 提交。
  - 非法动作被拒绝并保持同一玩家行动。
  - 一手结束后 settlement 更新筹码并移动 Button。
  - UI 可显示座位、筹码、底牌、公共牌、底池、动作按钮和错误。
- 更新 README 的本地运行方式。
- 只在所有验收通过后勾选 `doc/tasks/progress.md` 的 MVP 闭环项。

验收：

- `python -m pytest` 通过。
- `python -m mypy src tests` 通过。
- `python -m ruff check .` 通过。
- `python -m ruff format --check .` 通过。
- PokerKit import 边界检查通过。
- README 包含本地启动和测试命令。

## 8. 最终 Definition of Done

最终完成时必须具备：

- 全部 `doc/tasks/*.md` 中 MVP 必需任务已实现，且对应测试通过。
- `doc/tasks/progress.md` 勾选状态真实反映实现情况。
- `doc/implementation-decisions.md` 记录所有默认策略和重要取舍。
- README 包含本地安装、运行、测试命令。
- 本地 Web UI 可以用于 Human Player 操作。
- Bot 与 Human 共用 Observation、Action、Validator、Adapter 路径。
- 非法动作严格重试同一玩家。
- Hidden information 相关测试覆盖 Observation、Event Log、WebSocket、API、Frontend mock。
- 没有未隔离的 PokerKit import。
- 没有真实 LLM/GTO/Coach/Replay/SQLite/账号/认证/多桌等非 MVP 范围实现。

完成后输出简短报告：

- 已完成模块。
- 关键默认决策。
- 测试命令结果。
- 本地运行入口。
- 尚未进入 MVP 的明确后续项。
