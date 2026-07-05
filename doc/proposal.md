# mcx-poker 需求文档

状态：MVP 需求已确认，实施前草案  
版本：v0.3  
来源：

- `/Users/machengqi/Library/Mobile Documents/iCloud~md~obsidian/Documents/psnl_hbts/mcxPoker/Todolist.md`
- 当前项目根目录 `/Users/machengqi/Documents/mcx-poker`
- 当前仓库已存在 `pyproject.toml`，项目依赖 `pokerkit==0.7.4`
- 用户第一轮确认：先做 MVP、单张本地牌桌、Human Player 使用 Web UI、前端技术栈不指定且越简单越好、All-in 作为独立动作、非法动作严格拦截、LLM/GTO/Coach 第一版只留接口
- 用户第二轮确认：MVP 做普通 No-Limit Texas Hold'em 现金桌、不做锦标赛、固定 6 个座位、先能玩不要求保存每一手牌、加注语义为“加注到总下注额 X”、非法动作统一返回报错并让同一牌手重新选择

## 1. 项目定位

`mcx-poker` 不是从零实现德州扑克规则引擎，而是在 PokerKit 之上实现牌桌平台层。

PokerKit 负责：

- 规则
- 状态转移
- 下注合法性
- 胜负判定
- 边池结算

`mcx-poker` 负责：

- 长期存在的牌桌
- 座位与玩家管理
- 筹码与一手接一手的牌局生命周期
- Player Controller 抽象
- Observation 与 Action 模型
- PokerKit Adapter
- 手牌历史记录
- 回放
- 后端 API
- WebSocket 实时通信
- 前端牌桌 UI
- 未来 LLM、GTO、教练分析扩展接口

## 2. 当前确认范围

当前已明确的第一目标是先做 MVP，而不是一次性实现完整平台。

MVP 的方向：

- 使用 PokerKit 作为规则内核。
- 只支持一张本地长期存在的牌桌。
- 固定 6 个座位。
- 只做普通 No-Limit Texas Hold'em 现金桌，不做锦标赛。
- Human Player 通过 Web UI 操作。
- 前端和后端技术栈不做用户侧指定，由实现时选择简单、可维护、适合 PokerKit/Python 项目的方案。
- 先把牌局闭环、玩家接口、Observation、Action、非法动作拦截和最小 UI 跑通。
- Hand History 持久化、Replay、SQLite、统计、GTO、LLM、Coach 等能力不作为第一阶段必须完整交付的内容，除非后续需求确认改变。

推荐开发顺序来自 Todolist：

1. PokerKit 跑通一手牌
2. Table Manager 实现连续打牌
3. Player Controller 先接 Random Bot
4. Observation + Action
5. Game Loop 完整闭环
6. Human Player
7. WebSocket
8. 最小前端牌桌
9. Hand History
10. Replay + SQLite

本次需求确认后的实际目标是“越简单越好”的可玩 MVP：优先达到第 8 步，即有最小 Web UI 的本地可玩版本。第 9、10 步可以作为紧随 MVP 后的增强项。

## 3. 总体架构

系统边界：

```text
Player Controller
  ↓ Observation -> Action
Game Loop
  ↓ PlayerAction
PokerKit Adapter
  ↓ PokerKit operation
PokerKit
  ↓ authoritative game state
Table Manager
  ↓ hand lifecycle, chips, seats
Hand History / Replay / API / WebSocket / UI
```

核心原则：

- 后端是唯一权威。
- 前端只展示后端状态，不自行判断动作是否合法、谁该行动、谁赢、Pot 如何计算。
- Player Controller 只实现 `Observation -> Action`。
- Game Loop 不关心玩家是人、Bot、LLM、GTO 还是外部 API。
- 前端和未来 Agent 不直接调用 PokerKit。
- Observation 不暴露对手底牌、未发出的牌或完整 PokerKit 内部状态。

## 4. Phase 1：最小可运行后端

### 4.1 Table Manager

Table Manager 管理一张长期存在的牌桌。

应覆盖：

- 座位
- 玩家
- 筹码
- Button 移动
- 一手接一手开始
- 暂停
- 继续
- 重开

生命周期：

```text
Table
  ↓
创建一手牌
  ↓
交给 PokerKit
  ↓
一手结束
  ↓
更新筹码
  ↓
开始下一手
```

已确认：

- 第一版只支持一张本地牌桌。
- 第一版固定 6 个座位。
- 第一版只做普通 No-Limit Texas Hold'em 现金桌，不做锦标赛、盲注升级、淘汰、报名等机制。

待确认：

- 玩家离桌、坐下、补充筹码、断线重连是否进入第一版。

### 4.2 Game Loop

Game Loop 是平台核心循环。

流程：

```text
读取当前牌局状态
↓
找到当前行动玩家
↓
生成该玩家可见信息
↓
向玩家请求动作
↓
把动作交给 PokerKit
↓
更新状态
↓
循环
```

已确认：

- Human Player 第一阶段使用 Web UI，不做 CLI 作为主要交互形态。

待确认：

- 第一版 Game Loop 是否从一开始就异步化以适配 WebSocket 和 Web UI，还是先实现同步核心再包一层 Web 交互。
- Bot 行动是否需要可配置延迟，还是即时行动即可。

### 4.3 Player Controller

统一玩家接口：

```text
Observation -> Action
```

第一版候选实现：

- Human Player
- Random Bot
- 简单规则 Bot

未来扩展：

- LLM Player
- GTO Player
- API Player

已确认：

- Human Player 第一交互形态是 Web UI。
- Bot 逻辑独立于平台，后续单独实现和迭代。
- 平台只负责向 Bot 提供 Observation、接收 Action、校验合法性、返回结果或错误。

待确认：

- MVP 必须实现哪些 Bot：Random、Always Call、Nit、Aggressive 是否都进入 MVP。
- Player Controller 是否需要支持超时、自动弃牌、断线托管。

### 4.4 Observation System

Observation 负责把 PokerKit 的完整状态转换成某个玩家实际可见的信息。

应包含：

- 自己的底牌
- 公共牌
- 各玩家筹码
- 底池
- 当前下注
- 历史动作
- 合法动作

不得暴露：

- 对手底牌
- 未发出的牌
- 完整 PokerKit 内部状态

待确认：

- Observation 是否需要区分 Bot 版、Human UI 版、LLM 版三种 schema？
- 历史动作需要保留到什么粒度：街、下注轮、每个动作、动作前后筹码变化？
- 是否需要在 Observation 中包含最小加注额、可 call 金额、有效筹码等派生字段？

### 4.5 Action Model

统一动作格式候选：

```text
Fold
Check
Call
Raise to X  # 加注到总下注额 X
All-in
```

动作路径：

```text
PlayerAction
↓
mcx-poker Adapter
↓
PokerKit
```

已确认：

- All-in 作为独立 `PlayerAction`。
- Raise 语义为 `Raise to X`，即加注到总下注额 X，不是额外再加 X。
- 非法动作必须严格拦截；例如人类玩家下注超过筹码量时，系统报错且不提交动作。
- 非人类玩家同样严格限制，不能提交超出合法动作集合的动作。
- 非法动作报错后，同一牌手重新选择动作；Bot 也遵循相同规则。
- Bot 逻辑独立于平台，平台不替 Bot 决定 fallback 动作。

建议实现约束：

- Observation 中提供当前玩家的合法动作集合。
- Web UI 只展示当前合法动作。
- 后端 Action 接收层再次校验提交动作是否在合法动作集合内。
- PokerKit Adapter 调用 PokerKit 前做平台层校验。
- PokerKit 作为最终规则内核，如果 PokerKit 判定非法，则该动作不落盘、不推进状态，并返回错误。
- Bot 和 Human Player 使用同一套校验路径，避免为 Bot 单独开后门。
- Game Loop 收到非法动作错误后，继续向同一 Player Controller 请求动作，直到收到合法动作或外部中止。

## 5. Phase 2：后端 API 与 WebSocket

### 5.1 Backend API

基础控制能力：

- 创建牌桌
- 加入座位
- 开始游戏
- 暂停
- 查询牌桌

MVP 不要求提供持久化历史手牌查询。查询历史手牌作为 Hand History 持久化后的后续能力。

已确认：

- 用户不指定后端框架；实现时选择简单、适合本项目的方案。

待确认：

- 第一版 API 是否需要认证。
- API 返回格式是否需要稳定版本号，例如 `/api/v1`。
- 是否需要 OpenAPI 文档作为交付物。

### 5.2 WebSocket

后端发送事件：

- 新手牌开始
- 发牌
- 玩家行动
- 公共牌更新
- 轮到你行动
- 手牌结束

前端发送事件：

- Fold
- Call
- Raise
- All-in

待确认：

- WebSocket 事件 schema 是否需要在第一版需求文档中完整定义？
- 是否需要支持旁观者？
- 是否需要支持同一用户多客户端连接？

## 6. Phase 3：前端

### 6.1 Poker Table UI

第一版 UI 来自 Todolist：

- 圆桌或椭圆牌桌
- 6 个座位
- 玩家名
- 筹码
- 底牌
- 公共牌
- 底池
- 操作按钮

当前不追求动画和美术。

已确认：

- 前端技术栈不指定，越简单越好。
- Human Player 通过 Web UI 操作。
- 不追求动画和美术。

待确认：

- 是否需要移动端适配。
- 第一版是否只服务本机浏览器，还是需要局域网多人访问。
- 牌面素材是否使用文本/Unicode/简单 CSS，还是需要图片素材。

### 6.2 Frontend State

前端只负责：

```text
收到后端状态
↓
显示
```

前端不负责：

- 判断谁行动
- 判断动作是否合法
- 判断谁赢
- 计算 Pot

## 7. Phase 4：数据系统

### 7.1 Hand History

MVP 先以能玩为目标，不要求把每一手牌保存到本地文件或数据库。为了 UI 展示、调试和后续扩展，系统内部仍应保留当前手牌的临时事件记录。

后续持久化 Hand History 时，应记录：

- 手牌编号
- 座位
- 初始筹码
- 底牌
- 公共牌
- 所有动作
- 最终结果

未来用途：

- Replay
- 统计
- GTO 分析
- LLM 记忆
- 玩家画像

已确认：

- 用户不指定 Hand History 的底层存储方案，要求实现侧选择简单方案。
- MVP 先能玩，不要求保存每一手牌到本地文件或数据库。

待确认：

- 手牌历史是否允许在手牌结束后公开所有玩家底牌。
- 是否需要兼容 PokerStars/通用 HH 文本格式，还是只定义项目内部 JSON schema。

### 7.2 Replay System

能力：

```text
上一动作
下一动作
自动播放
```

Replay 本质是根据 Hand History 重建牌局。

待确认：

- Replay 第一版是后端能力、前端 UI 能力，还是两者都要？
- Replay 是否需要逐动作还原所有玩家可见视角？
- 自动播放是否需要速度控制？

### 7.3 Database

完整数据库不作为最小可玩 MVP 的硬性要求。后续需要持久化牌桌、玩家、手牌历史和统计时，SQLite 足够作为第一版数据库。

保存：

- 玩家
- 牌桌设置
- Hand History
- Session
- 统计数据

已确认：

- MVP 先能玩，不要求引入数据库。

待确认：

- 后续引入数据库时，是否需要 ORM，例如 SQLAlchemy。
- 后续引入数据库时，是否需要 schema 迁移工具，例如 Alembic。
- 统计数据是否只留表结构，还是需要实现基础统计。

## 8. Phase 5：简单 Bot 验证架构

目标不是做强 AI，而是验证不同 Player Controller 可以随意插拔。

候选 Bot：

- Random Bot
- Always Call Bot
- Nit Bot
- Aggressive Bot

验收示例：

```text
Human
vs Random
vs Nit
vs Aggressive
```

待确认：

- 第一版验收是否必须包含 Human vs 多 Bot 的完整一局牌？
- 是否需要可重复随机种子，便于测试和回放？

## 9. Phase 6：未来扩展接口

此阶段只留位置，暂不实现。

已确认：

- LLM、GTO、Coach 第一版只保留接口，不实现具体能力。

### 9.1 LLM Harness

未来流程：

```text
Observation
↓
Prompt / Structured Input
↓
Local LLM 或 API
↓
Parser
↓
PlayerAction
```

后续待确认：

- 是否需要在第一版中定义 LLM Observation 的 JSON schema？
- 是否需要预留 prompt 模板目录？

### 9.2 GTO Layer

未来流程：

```text
Game State
↓
Strategy Query
↓
GTO Result
```

用途：

- GTO Bot
- 赛后分析
- 教练系统

要求：

- 不与主 Game Loop 强绑定。

已确认：

- 第一版只定义接口，不实现 GTO 能力，不引入 solver 依赖。

### 9.3 Analysis / Coach

未来流程：

```text
Hand History
↓
分析关键决策
↓
发现 Leak
↓
生成训练建议
```

已确认：

- Analysis / Coach 完全排除在 MVP 外，只保留未来扩展方向。

## 10. 非功能需求

已确认：

- 第一版以 MVP 为目标，越简单越好。

待确认：

- 第一版支持的 Python 版本是否沿用 `pyproject.toml` 中的 `>=3.11`。
- 是否要求跨平台运行：macOS、Linux、Windows。
- 是否要求测试覆盖率门槛。
- 是否要求 CI。
- 是否要求日志、调试模式、可复现实验 seed。
- 是否要求长期运行稳定性，还是第一版只作为本地开发原型。

## 11. MVP 边界

已确认的 MVP 边界：

- 先做 MVP，不一次性做完整平台。
- 使用 PokerKit 跑通普通 No-Limit Texas Hold'em 现金桌的一手牌和连续手牌。
- 只支持一张本地牌桌。
- 固定 6 个座位。
- 不做锦标赛。
- Human Player 使用 Web UI。
- 前端技术栈不指定，越简单越好。
- Bot 通过统一 Player Controller 插拔。
- Bot 逻辑独立于平台，之后单独写 Bot 逻辑。
- Observation 不泄露隐藏信息。
- Action Model 不暴露 PokerKit 细节。
- All-in 是独立 `PlayerAction`。
- Raise 是“加注到总下注额 X”。
- 非法动作严格拦截，报错且不提交动作，然后让同一牌手重新选择。
- MVP 先能玩，不要求持久化保存每一手牌。
- 后端是唯一权威。
- LLM/GTO/Coach 第一版只留接口，不实现具体能力。

MVP 后续增强项：

- 持久化 Hand History。
- Replay。
- SQLite。
- 统计。
- 更复杂 Bot。

## 12. 仍需确认的问题

P0 需求已确认，不再阻塞 MVP 实施。

以下问题可以在实现过程中或 MVP 之后再确认：

1. 玩家离桌、坐下、补充筹码、断线重连是否进入 MVP。
2. Web UI 是否需要移动端适配。
3. 第一版是否只服务本机浏览器，还是需要局域网多人访问。
4. 手牌结束后，历史记录是否公开所有玩家底牌。
5. 后续持久化 Hand History 时使用本地文件还是 SQLite。

## 13. 暂不进入第一版的内容

除非需求确认后改变，以下内容暂不作为第一版实现目标：

- 高质量牌桌动画
- 美术级扑克牌素材
- 复杂 AI 策略
- 真实 GTO Solver 接入
- LLM 玩家实装
- 教练系统实装
- 多桌大厅
- 账号体系
- 线上部署
- 锦标赛模式
- 现金充值或真实货币系统
