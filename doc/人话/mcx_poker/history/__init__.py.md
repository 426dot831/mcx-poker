# `mcx_poker/history/__init__.py` 人话讲解

源文件：`/Users/machengqi/Documents/mcx-poker/src/mcx_poker/history/__init__.py`

## 这个文件是干什么的

源码说明：Hand history and replay support.

人话概括：

负责记录和查询牌局事件历史，让系统知道之前发生过什么。

## 导入区

- 第 3-15 行：从 `mcx_poker.history.events` 导入 `EventType, EventVisibility, HandEvent, HandEventLog, JSONValue, TemporaryHandEventLog, append, clear_hand, get_last_sequence, list_player_events, list_public_events`。

人话：导入区是在声明“这个文件需要哪些外部工具”。标准库通常提供基础能力，项目内导入则说明它依赖哪些业务模块。

## 顶层常量和类型

- 第 17-29 行：`__all__` = `['EventType', 'EventVisibility', 'HandEvent', 'HandEventLog', 'JSONValue', 'TemporaryHandEventLog', 'append', 'clear_hand', 'get_last_sequence', 'list_player_events', 'list_public_events']`。人话：在模块级别准备一个后面会反复使用的值。

## 对外公开接口

`__all__` 声明这个模块希望别人主要使用这些名字：

- `EventType`
- `EventVisibility`
- `HandEvent`
- `HandEventLog`
- `JSONValue`
- `TemporaryHandEventLog`
- `append`
- `clear_hand`
- `get_last_sequence`
- `list_player_events`
- `list_public_events`

## 初学者阅读建议

先看“这个文件是干什么的”，再看类和函数标题。遇到以下划线开头的函数，可以先理解成内部工具；遇到 `to_dict/from_dict/to_json/from_json`，重点记住它们是在对象、字典和 JSON 之间转换。
