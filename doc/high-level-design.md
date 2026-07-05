# mcx-poker 概要设计文档

状态：根据 `doc/proposal.md` 生成的概要设计  
版本：v0.1  
输入文档：`doc/proposal.md`  
输出文件：`doc/high-level-desigh.md`

## 1. 设计范围

本文档面向 `mcx-poker` 的 MVP 概要设计，目标是把需求文档中的已确认内容拆分为模块，并说明模块之间的关系。

MVP 已确认范围：

- 基于 PokerKit 实现普通 No-Limit Texas Hold'em 现金桌。
- 后端作为唯一权威，PokerKit 作为规则内核。
- 只支持一张本地长期存在的牌桌。
- 固定 6 个座位。
- 支持一手牌和连续手牌生命周期。
- Human Player 使用 Web UI 操作。
- Player Controller 通过统一接口接入 Human、Bot 以及未来扩展玩家。
- Observation 不泄露隐藏信息。
- Action Model 不暴露 PokerKit 细节。
- All-in 是独立动作。
- Raise 语义为“加注到总下注额 X”。
- 非法动作严格拦截，报错后同一牌手重新选择。
- MVP 先能玩，不要求持久化保存每一手牌。
- LLM、GTO、Coach 第一版只保留接口，不实现具体能力。

MVP 不包含：

- 多桌大厅。
- 账号体系。
- 线上部署。
- 锦标赛模式。
- 真实货币系统。
- 高质量动画或美术级扑克牌素材。
- 真实 GTO Solver 接入。
- LLM 玩家实装。
- Coach 系统实装。
- 持久化 Hand History、Replay、SQLite、统计等完整数据系统。

## 2. 总体架构

`mcx-poker` 是 PokerKit 之上的牌桌平台层。PokerKit 负责扑克规则和状态转移，`mcx-poker` 负责牌桌、座位、玩家、观察信息、动作模型、交互通道和未来扩展接口。

```text
Web UI / Bot / Future Agent
        ↓
Player Controller
        ↓ Observation -> Action
Game Loop
        ↓ PlayerAction
Action Validator
        ↓ Validated PlayerAction
PokerKit Adapter
        ↓ PokerKit operation
PokerKit
        ↓ authoritative game state
Table Manager
        ↓ table snapshot / events
API / WebSocket / Temporary Hand Events / Future Replay
```

核心约束：

- 后端是唯一权威。
- 前端只展示后端状态和提交用户动作。
- Bot 与 Human 使用同一套 Observation、Action 和校验路径。
- Game Loop 不关心玩家来源。
- Player Controller 不直接调用 PokerKit。
- Web UI、LLM、GTO、Coach 不直接调用 PokerKit。
- PokerKit Adapter 是平台层与 PokerKit 的唯一规则交互边界。

## 3. 模块划分

### 3.1 Table Manager

职责：

- 管理唯一一张本地长期存在的牌桌。
- 管理固定 6 个座位。
- 管理玩家入座状态、座位状态和玩家筹码。
- 管理 Button 移动。
- 创建新一手牌。
- 在一手结束后接收结算结果并更新筹码。
- 控制牌桌暂停、继续和重开。

输入：

- 后端 API 或内部控制命令。
- Game Loop 返回的一手牌结束结果。
- PokerKit Adapter 暴露的权威牌局状态摘要。

输出：

- 当前牌桌快照。
- 新一手牌初始化参数。
- 面向 API、WebSocket 和 UI 的牌桌状态。

与其他模块关系：

- 向 Game Loop 提供当前手牌上下文。
- 通过 PokerKit Adapter 间接持有和更新 PokerKit 牌局状态。
- 向 WebSocket Gateway 提供状态变更事件。
- 向 Temporary Hand Event Log 写入当前手牌临时事件。

### 3.2 Game Loop

职责：

- 驱动一手牌从开始到结束。
- 读取当前权威牌局状态。
- 找到当前行动玩家。
- 调用 Observation System 生成当前玩家可见信息。
- 调用 Player Controller 获取动作。
- 将动作交给 Action Validator 和 PokerKit Adapter。
- 处理合法动作后的状态推进。
- 处理非法动作错误，并让同一牌手重新选择。

流程：

```text
读取当前牌局状态
↓
识别当前行动玩家
↓
生成 Observation
↓
请求 Player Controller 返回 Action
↓
校验 Action
↓
提交 PokerKit Adapter
↓
更新状态并广播事件
↓
继续循环，直到一手结束
```

与其他模块关系：

- 从 Table Manager 获取当前手牌和座位信息。
- 使用 Observation System 生成玩家视角。
- 调用 Player Controller 获取动作。
- 使用 Action Validator 拦截非法动作。
- 使用 PokerKit Adapter 推进 PokerKit 状态。
- 将动作和状态变化写入 Temporary Hand Event Log。
- 通过 WebSocket Gateway 通知前端。

设计约束：

- Game Loop 不包含具体 Bot 策略。
- Game Loop 不包含前端展示逻辑。
- Game Loop 不绕过 PokerKit Adapter 直接操作 PokerKit。
- 非法动作不推进状态、不记录为已执行动作。

### 3.3 Player Controller

职责：

- 统一所有玩家来源。
- 接收 Observation。
- 返回 Action。

统一接口：

```text
Observation -> Action
```

MVP 需要支持的玩家类型：

- Human Player：通过 Web UI 和 WebSocket/API 提交动作。
- Bot Player：用于验证统一玩家接口和本地可玩闭环。

未来扩展玩家类型：

- LLM Player。
- GTO Player。
- API Player。

与其他模块关系：

- 由 Game Loop 调用。
- 只接收 Observation System 生成的信息。
- 只返回 Action Model 定义的动作。
- 不直接访问 PokerKit 内部状态。

设计约束：

- Bot 逻辑独立于平台层。
- 平台不替 Bot 决定 fallback 动作。
- Bot 和 Human 的非法动作处理路径一致。

### 3.4 Observation System

职责：

- 将 PokerKit 权威状态转换为指定玩家可见的 Observation。
- 屏蔽隐藏信息。
- 提供当前玩家可执行的合法动作集合。

Observation 应包含：

- 当前玩家自己的底牌。
- 公共牌。
- 各玩家公开状态。
- 各玩家筹码。
- 底池。
- 当前下注状态。
- 当前手牌已发生的公开动作。
- 当前玩家合法动作集合。

Observation 不得包含：

- 对手未公开底牌。
- 未发出的牌。
- 完整 PokerKit 内部对象。
- 可用于推断牌堆顺序的隐藏状态。

与其他模块关系：

- 从 PokerKit Adapter 和 Table Manager 读取权威状态摘要。
- 向 Player Controller 输出玩家视角数据。
- 向 WebSocket Gateway 或 API 提供前端可展示状态。

设计约束：

- MVP 只要求满足 Human UI 和基础 Bot 使用。
- LLM 专用 schema、GTO 专用 schema 可在未来扩展接口中预留，不在 MVP 中实装。

### 3.5 Action Model

职责：

- 定义平台层统一动作格式。
- 隔离前端、Bot、未来 Agent 与 PokerKit 具体调用细节。

动作集合：

```text
Fold
Check
Call
Raise to X
All-in
```

语义：

- `Raise to X` 表示加注到总下注额 X，不表示额外加 X。
- `All-in` 是独立动作，不通过特殊金额隐式表达。

与其他模块关系：

- Player Controller 只返回 Action Model。
- Web UI 只提交 Action Model。
- Action Validator 校验 Action Model。
- PokerKit Adapter 将 Action Model 转换为 PokerKit 操作。

设计约束：

- Action Model 不暴露 PokerKit 内部 API。
- 非法动作必须返回错误，不得推进状态。

### 3.6 Action Validator

职责：

- 在平台层拦截非法动作。
- 确保提交动作属于当前 Observation 的合法动作集合。
- 校验金额类动作的范围和语义。
- 在调用 PokerKit Adapter 前提供第一层防护。
- 接收 PokerKit Adapter 或 PokerKit 返回的非法动作错误，并统一反馈给 Game Loop。

校验路径：

```text
PlayerAction
↓
Observation legal actions check
↓
platform amount and turn check
↓
PokerKit Adapter
↓
PokerKit final legality check
```

非法动作处理：

- 不推进 PokerKit 状态。
- 不更新 Table Manager 筹码。
- 不广播为成功动作。
- 返回错误给原 Player Controller。
- Game Loop 继续请求同一牌手重新选择动作。

### 3.7 PokerKit Adapter

职责：

- 封装 PokerKit 初始化、状态读取和动作提交。
- 将平台层 Action Model 转换为 PokerKit 操作。
- 将 PokerKit 状态转换为平台可消费的状态摘要。
- 暴露胜负判定和边池结算结果。

与其他模块关系：

- 被 Game Loop 调用以推进牌局。
- 被 Observation System 调用以读取状态摘要。
- 被 Table Manager 调用以创建新一手牌和获取结算结果。

设计约束：

- PokerKit 是规则权威。
- 其他模块不得直接操作 PokerKit 内部对象。
- Adapter 不包含 UI、API、Bot 策略或持久化逻辑。

### 3.8 Backend API

职责：

- 提供基础牌桌控制能力。
- 提供查询当前牌桌状态的能力。
- 接收 Human Player 的必要控制请求。

MVP 基础能力：

- 创建或初始化本地牌桌。
- 加入座位。
- 开始游戏。
- 暂停。
- 继续。
- 重开。
- 查询牌桌。

与其他模块关系：

- 调用 Table Manager 执行控制命令。
- 查询 Table Manager 的牌桌快照。
- 可与 WebSocket Gateway 共享状态模型。

设计约束：

- MVP 不要求历史手牌查询。
- 是否提供认证、`/api/v1` 版本路径、OpenAPI 文档仍属待确认事项，概要设计不替需求做决定。

### 3.9 WebSocket Gateway

职责：

- 向前端实时推送牌桌状态和行动事件。
- 接收 Human Player 的动作提交。
- 将前端动作转交给 Human Player Controller 或 Game Loop 的动作等待点。

后端事件类型：

- 新手牌开始。
- 发牌。
- 玩家行动。
- 公共牌更新。
- 轮到你行动。
- 手牌结束。
- 非法动作错误。

前端动作类型：

- Fold。
- Check。
- Call。
- Raise to X。
- All-in。

与其他模块关系：

- 从 Table Manager 和 Game Loop 接收状态变化。
- 向 Human Player Controller 传递用户提交动作。
- 使用 Observation System 生成前端可见状态。

设计约束：

- 前端收到的是可见状态，不是完整 PokerKit 内部状态。
- 前端不判断动作是否合法，只展示后端给出的合法动作并提交用户选择。
- WebSocket 完整事件 schema 是否在第一版冻结，仍属待确认事项。

### 3.10 Frontend Poker Table UI

职责：

- 展示本地可玩牌桌。
- 展示 6 个座位、玩家名、筹码、底牌、公共牌、底池和操作按钮。
- 展示当前玩家可执行动作。
- 提交 Human Player 动作。
- 展示非法动作错误。

与其他模块关系：

- 通过 Backend API 获取初始状态和基础控制能力。
- 通过 WebSocket Gateway 接收实时状态。
- 通过 WebSocket Gateway 或 API 提交 Action Model。

设计约束：

- 前端不是规则权威。
- 前端不计算 Pot。
- 前端不判断谁赢。
- 前端不判断谁该行动。
- 前端不自行推断隐藏信息。
- 技术栈按需求保持未指定，由实现阶段依据“越简单越好、适合 Python/PokerKit 项目”选择。

### 3.11 Temporary Hand Event Log

职责：

- 在 MVP 中保留当前手牌的临时事件记录。
- 支持 UI 展示、调试和后续 Hand History 演进。

MVP 临时记录可包含：

- 手牌开始。
- 座位和初始筹码快照。
- 发牌和公共牌事件的公开部分。
- 玩家成功动作。
- 非法动作错误。
- 手牌结束和结算摘要。

与其他模块关系：

- Game Loop 写入事件。
- Table Manager 在一手结束时读取结算摘要。
- WebSocket Gateway 可复用事件生成前端通知。
- 未来 Hand History 持久化可基于该事件模型扩展。

设计约束：

- MVP 不要求保存每一手牌到本地文件或数据库。
- 手牌结束后是否公开所有玩家底牌仍属待确认事项。
- 是否兼容 PokerStars 或通用 HH 文本格式仍属待确认事项。

### 3.12 Future Extension Interfaces

职责：

- 为 LLM、GTO、Coach 等后续能力保留模块边界。
- 防止未来扩展侵入 Game Loop 和 PokerKit Adapter。

预留接口：

- LLM Harness：`Observation -> Prompt / Structured Input -> Parser -> PlayerAction`。
- GTO Layer：`Game State / Hand History -> Strategy Query -> GTO Result`。
- Analysis / Coach：`Hand History -> Decision Analysis -> Leak Detection -> Training Advice`。

设计约束：

- MVP 不实现真实 LLM 玩家。
- MVP 不引入 solver 依赖。
- MVP 不实现 Coach 系统。
- 这些能力不得与主 Game Loop 强绑定。

## 4. 模块关系视图

### 4.1 运行时依赖关系

```text
Frontend Poker Table UI
  ↓
Backend API / WebSocket Gateway
  ↓
Human Player Controller
  ↓
Game Loop
  ├─ Observation System
  ├─ Action Validator
  ├─ Temporary Hand Event Log
  └─ PokerKit Adapter
        ↓
      PokerKit
  ↓
Table Manager
```

Bot Player Controller 与 Human Player Controller 在 Game Loop 眼中是同一类依赖：

```text
Game Loop
  ↓ Observation
Player Controller
  ↓ Action
Game Loop
```

### 4.2 权威状态关系

```text
PokerKit
  ↓ rules, state transition, showdown, pot settlement
PokerKit Adapter
  ↓ normalized state summary
Table Manager
  ↓ table snapshot
Observation System
  ↓ player-visible state
Player Controller / Frontend
```

权威顺序：

1. PokerKit 判定规则和牌局状态。
2. PokerKit Adapter 暴露平台层摘要。
3. Table Manager 维护长期牌桌状态和筹码生命周期。
4. Observation System 生成玩家视角。
5. Frontend 和 Player Controller 只消费玩家可见状态。

### 4.3 动作提交关系

```text
Frontend / Bot
  ↓ Action Model
Player Controller
  ↓ PlayerAction
Game Loop
  ↓
Action Validator
  ↓
PokerKit Adapter
  ↓
PokerKit
```

非法动作返回路径：

```text
PokerKit / Action Validator
  ↓ error
Game Loop
  ↓ same player's turn remains active
Player Controller
  ↓ choose again
```

## 5. 关键数据模型概念

### 5.1 Table

表示长期存在的一张本地牌桌。

核心字段概念：

- table id。
- fixed seat count = 6。
- seats。
- current button。
- current hand id。
- table status：未开始、运行中、暂停、已重开。

### 5.2 Seat

表示一个固定座位。

核心字段概念：

- seat index。
- player id。
- player name。
- chip stack。
- seat status。

### 5.3 Player

表示平台层玩家。

核心字段概念：

- player id。
- display name。
- controller type：Human、Bot、Future Agent。
- current seat。

### 5.4 Observation

表示某个玩家在当前时刻可见的牌局信息。

核心字段概念：

- observer player id。
- hand id。
- own hole cards。
- public board cards。
- visible seats。
- stacks。
- pot summary。
- current bet summary。
- action history visible to observer。
- legal actions。

### 5.5 PlayerAction

表示玩家提交的平台层动作。

核心字段概念：

- player id。
- hand id。
- action type：Fold、Check、Call、RaiseTo、AllIn。
- amount：仅金额类动作需要。

### 5.6 Hand Event

表示当前手牌的临时事件。

核心字段概念：

- hand id。
- sequence number。
- event type。
- actor player id。
- public payload。
- timestamp 或顺序号。

MVP 中 Hand Event 只要求服务当前手牌 UI 和调试，不要求持久化。

## 6. 主要流程设计

### 6.1 牌桌启动流程

```text
Backend API receives start command
↓
Table Manager verifies table can start
↓
Table Manager creates hand context
↓
PokerKit Adapter initializes PokerKit state
↓
Game Loop starts hand loop
↓
WebSocket Gateway broadcasts hand started
```

### 6.2 玩家行动流程

```text
Game Loop reads current actor
↓
Observation System builds actor observation
↓
Game Loop requests action from Player Controller
↓
Player Controller returns PlayerAction
↓
Action Validator validates action
↓
PokerKit Adapter submits operation to PokerKit
↓
Game Loop records event and broadcasts update
```

### 6.3 Human Player 行动流程

```text
Game Loop waits for Human Player action
↓
WebSocket Gateway sends "your turn" and legal actions
↓
Frontend renders action buttons
↓
User submits Action Model
↓
WebSocket Gateway passes action to Human Player Controller
↓
Game Loop receives PlayerAction
```

### 6.4 非法动作处理流程

```text
PlayerAction submitted
↓
Action Validator or PokerKit rejects action
↓
Game Loop returns error to same Player Controller
↓
Frontend or Bot receives error
↓
Same player chooses again
```

处理规则：

- 当前行动玩家不变。
- 当前牌局状态不推进。
- 筹码不变化。
- 成功动作事件不写入。
- 可记录错误事件用于调试或 UI 提示。

### 6.5 一手结束与下一手流程

```text
PokerKit reports hand completed
↓
PokerKit Adapter extracts settlement result
↓
Table Manager updates stacks and button
↓
Temporary Hand Event Log records summary
↓
WebSocket Gateway broadcasts hand ended
↓
Table Manager creates next hand when table continues
```

## 7. MVP 交付边界

MVP 必须形成的闭环：

1. 初始化一张 6 人本地牌桌。
2. 玩家坐在固定座位。
3. PokerKit 跑通 No-Limit Texas Hold'em 现金桌。
4. Game Loop 能连续驱动手牌。
5. Human Player 能通过 Web UI 行动。
6. 至少具备可验证 Player Controller 插拔能力。
7. Observation 不泄露隐藏信息。
8. Action Model 支持 Fold、Check、Call、Raise to X、All-in。
9. 非法动作会报错并要求同一牌手重新选择。
10. 最小 UI 能展示座位、筹码、底牌、公共牌、底池和动作按钮。

MVP 后增强项：

- 持久化 Hand History。
- Replay。
- SQLite。
- 统计。
- 更复杂 Bot。
- 更完整 WebSocket 事件 schema。
- API 版本化和 OpenAPI 文档。

## 8. 待决策事项

以下事项来自需求文档中的待确认内容。本文档不替这些事项做架构决策。

- 玩家离桌、坐下、补充筹码、断线重连是否进入 MVP。
- 第一版 Web UI 是否需要移动端适配。
- 第一版是否只服务本机浏览器，还是需要局域网多人访问。
- 手牌结束后，历史记录是否公开所有玩家底牌。
- 后续持久化 Hand History 使用本地文件还是 SQLite。
- API 第一版是否需要认证。
- API 是否需要稳定版本路径，例如 `/api/v1`。
- 是否需要 OpenAPI 文档作为交付物。
- WebSocket 事件 schema 是否需要第一版完整冻结。
- 是否需要支持旁观者。
- 是否需要支持同一用户多客户端连接。
- Replay 第一版是后端能力、前端 UI 能力，还是两者都要。
- Replay 是否逐动作还原所有玩家可见视角。
- 自动播放是否需要速度控制。
- 后续数据库是否使用 ORM 或迁移工具。
- 是否要求测试覆盖率门槛。
- 是否要求 CI。
- 是否要求日志、调试模式和可复现实验 seed。
- 是否要求长期运行稳定性，还是第一版只作为本地开发原型。

## 9. 设计原则总结

- 规则归 PokerKit。
- 状态权威在后端。
- 牌桌生命周期归 Table Manager。
- 牌局推进归 Game Loop。
- 玩家输入归 Player Controller。
- 可见状态归 Observation System。
- 动作格式归 Action Model。
- 合法性防线由 Action Validator 和 PokerKit 共同保证。
- 前端只显示和提交。
- 数据系统、Replay、LLM、GTO、Coach 作为后续扩展，不阻塞 MVP。
