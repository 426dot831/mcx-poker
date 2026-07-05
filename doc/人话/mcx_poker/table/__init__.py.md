# `mcx_poker/table/__init__.py` 人话讲解

源文件：`/Users/machengqi/Documents/mcx-poker/src/mcx_poker/table/__init__.py`

## 这个文件是干什么的

源码说明：Table and seat management.

人话概括：

负责牌桌生命周期、座位、筹码、手牌推进和广播。

## 导入区

- 第 3-34 行：从 `mcx_poker.table.manager` 导入 `DEFAULT_ANTE, DEFAULT_BIG_BLIND, DEFAULT_MIN_ACTIVE_PLAYERS, DEFAULT_SMALL_BLIND, DEFAULT_STARTING_STACK, DEFAULT_TABLE_ID, SEAT_COUNT, AdapterUnavailableError, ControllerType, CreateHandRequest, HandAdapter, HandContext, HandSettlement, HandSettlementMismatchError, HandSnapshot, InvalidStackError, NoCurrentHandError, PlayerAlreadySeatedError, SeatNotFoundError, SeatOccupiedError, SeatSnapshot, SeatState, SeatStatus, TableManager, TableManagerError, TableNotInitializedError, TableSnapshot, TableState, TableStateConflictError, TableStatus`。

人话：导入区是在声明“这个文件需要哪些外部工具”。标准库通常提供基础能力，项目内导入则说明它依赖哪些业务模块。

## 顶层常量和类型

- 第 36-67 行：`__all__` = `['AdapterUnavailableError', 'ControllerType', 'CreateHandRequest', 'DEFAULT_ANTE', 'DEFAULT_BIG_BLIND', 'DEFAULT_MIN_ACTIVE_PLAYERS', 'DEFAULT_SMALL_BLIND', 'DEFAULT_STARTING_STACK', 'DEFAULT_TABLE_ID', 'HandAdapter', 'HandContext', 'HandSettlement', 'HandSettlementMismatchError', 'HandSnapshot', 'InvalidStackError', 'NoCurrentHandError', 'PlayerAlreadySeatedError', 'SEAT_COUNT', 'SeatNotFoundError', 'SeatOccupiedError', 'SeatSnapshot', 'SeatState', 'SeatStatus', 'TableManager', 'TableManagerError', 'TableNotInitializedError', 'TableSnapshot', 'TableState', 'TableStateConflictError', 'TableStatus']`。人话：在模块级别准备一个后面会反复使用的值。

## 对外公开接口

`__all__` 声明这个模块希望别人主要使用这些名字：

- `AdapterUnavailableError`
- `ControllerType`
- `CreateHandRequest`
- `DEFAULT_ANTE`
- `DEFAULT_BIG_BLIND`
- `DEFAULT_MIN_ACTIVE_PLAYERS`
- `DEFAULT_SMALL_BLIND`
- `DEFAULT_STARTING_STACK`
- `DEFAULT_TABLE_ID`
- `HandAdapter`
- `HandContext`
- `HandSettlement`
- `HandSettlementMismatchError`
- `HandSnapshot`
- `InvalidStackError`
- `NoCurrentHandError`
- `PlayerAlreadySeatedError`
- `SEAT_COUNT`
- `SeatNotFoundError`
- `SeatOccupiedError`
- `SeatSnapshot`
- `SeatState`
- `SeatStatus`
- `TableManager`
- `TableManagerError`
- `TableNotInitializedError`
- `TableSnapshot`
- `TableState`
- `TableStateConflictError`
- `TableStatus`

## 初学者阅读建议

先看“这个文件是干什么的”，再看类和函数标题。遇到以下划线开头的函数，可以先理解成内部工具；遇到 `to_dict/from_dict/to_json/from_json`，重点记住它们是在对象、字典和 JSON 之间转换。
