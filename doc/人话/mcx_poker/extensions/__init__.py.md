# `mcx_poker/extensions/__init__.py` 人话讲解

源文件：`/Users/machengqi/Documents/mcx-poker/src/mcx_poker/extensions/__init__.py`

## 这个文件是干什么的

源码说明：Future extension interface exports.

人话概括：

定义扩展接口，让外部策略、LLM 或未来插件能按统一格式接入。

## 导入区

- 第 3-46 行：从 `mcx_poker.extensions.interfaces` 导入 `ALLOWED_EXTENSION_INPUT_TYPES, MVP_EXCLUSIONS, REPLAY_HAND_HISTORY_REQUIREMENT, ActionRequestContext, ActionType, BaseFutureController, CoachFeedback, ControllerRegistry, DecisionAnalyzer, DecisionAssessment, DeterministicLLMClient, ExtensionInputRejected, ExtensionInterfaceError, GTOPlayerController, HandEvent, HandReviewInput, LeakDetector, LegalAction, LLMActionParser, LLMClient, LLMInputBuilder, LLMPlayerController, NoLegalActionAvailable, NoopSolverClient, ObservationLLMInputBuilder, ObservationStrategyQueryBuilder, PlatformDTO, PlayerAction, PlayerController, PlayerObservation, SimpleLLMActionParser, SolverClient, StrategyQuery, StrategyQueryBuilder, StrategyResult, TableSnapshot, VisibleSeat, action_from_observation, first_enabled_legal_action, normalize_action_type, parse_action_text, validate_extension_input`。

人话：导入区是在声明“这个文件需要哪些外部工具”。标准库通常提供基础能力，项目内导入则说明它依赖哪些业务模块。

## 顶层常量和类型

- 第 48-91 行：`__all__` = `['ALLOWED_EXTENSION_INPUT_TYPES', 'MVP_EXCLUSIONS', 'REPLAY_HAND_HISTORY_REQUIREMENT', 'ActionRequestContext', 'ActionType', 'BaseFutureController', 'CoachFeedback', 'ControllerRegistry', 'DecisionAnalyzer', 'DecisionAssessment', 'DeterministicLLMClient', 'ExtensionInputRejected', 'ExtensionInterfaceError', 'GTOPlayerController', 'HandEvent', 'HandReviewInput', 'LLMActionParser', 'LLMClient', 'LLMInputBuilder', 'LLMPlayerController', 'LeakDetector', 'LegalAction', 'NoLegalActionAvailable', 'NoopSolverClient', 'ObservationLLMInputBuilder', 'ObservationStrategyQueryBuilder', 'PlatformDTO', 'PlayerAction', 'PlayerController', 'PlayerObservation', 'SimpleLLMActionParser', 'SolverClient', 'StrategyQuery', 'StrategyQueryBuilder', 'StrategyResult', 'TableSnapshot', 'VisibleSeat', 'action_from_observation', 'first_enabled_legal_action', 'normalize_action_type', 'parse_action_text', 'validate_extension_input']`。人话：在模块级别准备一个后面会反复使用的值。

## 对外公开接口

`__all__` 声明这个模块希望别人主要使用这些名字：

- `ALLOWED_EXTENSION_INPUT_TYPES`
- `MVP_EXCLUSIONS`
- `REPLAY_HAND_HISTORY_REQUIREMENT`
- `ActionRequestContext`
- `ActionType`
- `BaseFutureController`
- `CoachFeedback`
- `ControllerRegistry`
- `DecisionAnalyzer`
- `DecisionAssessment`
- `DeterministicLLMClient`
- `ExtensionInputRejected`
- `ExtensionInterfaceError`
- `GTOPlayerController`
- `HandEvent`
- `HandReviewInput`
- `LLMActionParser`
- `LLMClient`
- `LLMInputBuilder`
- `LLMPlayerController`
- `LeakDetector`
- `LegalAction`
- `NoLegalActionAvailable`
- `NoopSolverClient`
- `ObservationLLMInputBuilder`
- `ObservationStrategyQueryBuilder`
- `PlatformDTO`
- `PlayerAction`
- `PlayerController`
- `PlayerObservation`
- `SimpleLLMActionParser`
- `SolverClient`
- `StrategyQuery`
- `StrategyQueryBuilder`
- `StrategyResult`
- `TableSnapshot`
- `VisibleSeat`
- `action_from_observation`
- `first_enabled_legal_action`
- `normalize_action_type`
- `parse_action_text`
- `validate_extension_input`

## 初学者阅读建议

先看“这个文件是干什么的”，再看类和函数标题。遇到以下划线开头的函数，可以先理解成内部工具；遇到 `to_dict/from_dict/to_json/from_json`，重点记住它们是在对象、字典和 JSON 之间转换。
