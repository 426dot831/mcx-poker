# Future Extension Interfaces 任务列表

来源：`doc/detailed-design/extensions/future-extension-interfaces.md`

目标：为 LLM、GTO、Coach、Replay 等后续能力保留接口边界，避免未来扩展侵入 Game Loop、PokerKit Adapter 和核心牌桌生命周期。

## 最小任务

- [x] EXT-01 创建扩展接口模块入口，避免核心模块直接依赖具体扩展实现。
- [x] EXT-02 定义扩展模块只能消费平台层 DTO 的约束。
- [x] EXT-03 定义 `LLMInputBuilder` 接口草案，输入为 `PlayerObservation`。
- [x] EXT-04 定义 `LLMClient` 接口草案，但不引入 API key、模型 SDK 或网络调用。
- [x] EXT-05 定义 `LLMActionParser` 接口草案，输出为 `PlayerAction`。
- [x] EXT-06 定义 fake `LLMPlayerController`，用于验证 Controller 插拔边界。
- [x] EXT-07 定义 `StrategyQueryBuilder` 接口草案，只消费平台层状态或未来 Hand History。
- [x] EXT-08 定义 `SolverClient` 接口草案，但不引入 solver 依赖。
- [x] EXT-09 定义 `StrategyResult` 数据结构草案，包含推荐动作、频率、EV 等可选字段。
- [x] EXT-10 定义 fake `GTOPlayerController`，用于验证不会阻塞 Game Loop。
- [x] EXT-11 定义 `HandReviewInput` 接口草案，输入来自 Hand History 或临时事件。
- [x] EXT-12 定义 `DecisionAnalyzer` 接口草案。
- [x] EXT-13 定义 `LeakDetector` 接口草案。
- [x] EXT-14 定义 `CoachFeedback` 数据结构草案。
- [x] EXT-15 定义 Replay 未来依赖关系说明：依赖持久化 Hand History，不依赖当前临时事件日志的跨重启保留。
- [x] EXT-16 确保扩展接口不能读取 PokerKit `State`、未发出的牌、对手未公开底牌或 Controller 私有状态。
- [x] EXT-17 确保扩展接口失败不会阻塞 MVP 本地可玩闭环。
- [x] EXT-18 在文档或代码注释中明确真实 LLM、solver、Coach 页面均不属于 MVP。

## 测试与验收

- [x] EXT-T01 测试 fake Future Controller 可以实现 `Observation -> Action` 并接入 Controller Registry。
- [x] EXT-T02 测试 fake LLM Controller 不需要 LLM 依赖即可初始化。
- [x] EXT-T03 测试 fake Solver 接口失败不会影响普通 Game Loop。
- [x] EXT-T04 测试扩展接口模块不 import PokerKit。
- [x] EXT-T05 测试扩展接口输入序列化后不包含隐藏信息。

## 不进入本模块

- [ ] EXT-X01 不实现真实 LLM 玩家。
- [ ] EXT-X02 不实现真实 GTO Solver。
- [ ] EXT-X03 不实现 Coach 分析系统。
- [ ] EXT-X04 不实现 Replay UI。
- [ ] EXT-X05 不引入外部模型、solver 或数据库依赖。
