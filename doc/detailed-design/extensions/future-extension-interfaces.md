# Future Extension Interfaces 详细设计

## 1. 模块目标

Future Extension Interfaces 为 LLM、GTO、Coach 等后续能力保留边界，防止未来扩展侵入 Game Loop、PokerKit Adapter 和核心牌桌生命周期。

MVP 只保留接口方向，不实现：

- 真实 LLM 玩家。
- 真实 GTO Solver。
- Coach 系统。
- 统计数据库。
- Replay 完整 UI。

## 2. 设计原则

- 扩展能力只能消费平台层 DTO。
- 扩展能力不能直接调用 PokerKit。
- 扩展能力不能修改 Game Loop 主流程。
- 扩展能力不能读取 Observation 不允许暴露的隐藏信息。
- 扩展能力失败时不能阻塞 MVP 本地可玩闭环。

## 3. LLM Harness 预留接口

未来流程：

```text
PlayerObservation
↓
Prompt or structured input
↓
LLM
↓
Parser
↓
PlayerAction
```

预留组件：

| 组件 | 说明 |
| --- | --- |
| `LLMInputBuilder` | 将 Observation 转为结构化输入或 prompt |
| `LLMClient` | 调用本地或远程 LLM |
| `LLMActionParser` | 将模型输出解析为 PlayerAction |
| `LLMPlayerController` | 实现 Player Controller 契约 |

MVP 不定义 LLM prompt 模板目录，不引入 API key，不实现模型调用。

## 4. GTO Layer 预留接口

未来流程：

```text
Game State or Hand History
↓
Strategy Query
↓
Solver or lookup
↓
GTO Result
```

预留组件：

| 组件 | 说明 |
| --- | --- |
| `StrategyQueryBuilder` | 从平台层状态构造策略查询 |
| `SolverClient` | 封装外部 solver 或本地查表 |
| `StrategyResult` | 返回推荐动作、频率和 EV 等信息 |
| `GTOPlayerController` | 可选地把策略结果转为 PlayerAction |

MVP 不引入 solver 依赖，不保证 Game Loop 能同步等待 solver。

## 5. Analysis / Coach 预留接口

未来流程：

```text
Hand History
↓
Decision extraction
↓
Analysis
↓
Leak detection
↓
Training advice
```

预留组件：

| 组件 | 说明 |
| --- | --- |
| `HandReviewInput` | 从 Hand History 或临时事件构造分析输入 |
| `DecisionAnalyzer` | 分析关键决策点 |
| `LeakDetector` | 识别稳定错误模式 |
| `CoachFeedback` | 输出训练建议 |

MVP 不实现 Coach 页面或训练建议生成。

## 6. Replay 预留关系

Replay 依赖持久化 Hand History。MVP 的 Temporary Hand Event Log 只作为未来演进基础。

未来 Replay 能力可能包含：

- 上一动作。
- 下一动作。
- 自动播放。
- 按玩家视角还原。

这些能力是否第一版进入后端、前端或两者都进入，当前需求未确认。

## 7. 接口输入限制

扩展接口默认只能读取：

- `PlayerObservation`
- `TableSnapshot`
- 公开 `HandEvent`
- 后续已确认可持久化的 Hand History

扩展接口不能读取：

- PokerKit `State`。
- 未发出的牌。
- 对手未公开底牌，除非未来需求明确允许在赛后分析中使用。
- Controller 私有状态。

## 8. 测试策略

MVP 阶段只测试边界：

- Future Controller 可以以 fake 形式实现 `Observation -> Action`。
- fake LLM Controller 不需要 LLM 依赖即可接入 Game Loop。
- fake Solver 不影响 Game Loop 正常运行。
- 扩展接口不能 import PokerKit。
- 扩展接口输入不包含隐藏信息。

## 9. 开放问题

- 是否需要在第一版中定义 LLM Observation 的 JSON schema。
- 是否需要预留 prompt 模板目录。
- GTO 查询输入是否基于 Game State、Hand History，还是二者都支持。
- Coach 是否允许在赛后使用完整底牌信息。
- Replay 第一版是后端能力、前端 UI 能力，还是两者都要。
- Replay 是否逐动作还原所有玩家可见视角。
- 自动播放是否需要速度控制。

