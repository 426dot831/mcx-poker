# Table Manager 详细设计

## 1. 模块目标

Table Manager 管理唯一一张本地长期存在的牌桌，负责座位、玩家、筹码、Button、一手接一手的生命周期，以及暂停、继续、重开等牌桌级控制。

Table Manager 不负责：

- 扑克规则判定。
- 当前行动玩家判定。
- 玩家策略。
- 前端展示。
- 直接调用 PokerKit 内部对象。

## 2. 拥有状态

Table Manager 拥有长期牌桌状态。

`TableState` 字段概念：

| 字段 | 说明 |
| --- | --- |
| `table_id` | 本地唯一牌桌标识 |
| `seat_count` | 固定为 6 |
| `status` | `idle`、`running`、`paused`、`resetting` |
| `seats` | 固定长度 6 的座位列表 |
| `button_seat_index` | 当前 Button 所在座位 |
| `current_hand_id` | 当前手牌标识，可为空 |
| `hand_context` | 当前手牌上下文，可为空 |

`SeatState` 字段概念：

| 字段 | 说明 |
| --- | --- |
| `seat_index` | 0 到 5 |
| `player_id` | 座位上的玩家，可为空 |
| `player_name` | 展示名 |
| `controller_type` | `human`、`bot`、`future_agent` |
| `stack` | 当前筹码 |
| `status` | `empty`、`seated`、`sitting_out`、`in_hand` |

`HandContext` 字段概念：

| 字段 | 说明 |
| --- | --- |
| `hand_id` | 当前手牌标识 |
| `button_seat_index` | 本手 Button |
| `active_seat_indexes` | 参与本手的座位 |
| `starting_stacks` | 本手开始时筹码快照 |
| `adapter_hand_ref` | PokerKit Adapter 内部手牌引用，不暴露给其他模块 |

## 3. 对外命令

Table Manager 提供牌桌级命令。命令返回结果应是平台层快照或错误，不暴露 PokerKit 对象。

| 命令 | 说明 |
| --- | --- |
| `initialize_table` | 初始化本地固定 6 座牌桌 |
| `seat_player` | 将玩家放到指定座位 |
| `start_table` | 从可开始状态进入运行状态 |
| `pause_table` | 暂停新的推进动作 |
| `resume_table` | 从暂停恢复 |
| `reset_table` | 重开本地牌桌 |
| `create_next_hand` | 根据当前座位和 Button 创建下一手上下文 |
| `apply_hand_settlement` | 接收一手结算结果并更新筹码 |
| `get_table_snapshot` | 读取当前牌桌快照 |

玩家离桌、补充筹码和断线重连是否进入 MVP 尚未确认，因此不在命令集内作为必须实现项。

## 4. 快照输出

`TableSnapshot` 面向 API、WebSocket、Observation System 和 Frontend 使用。

快照应包含：

- `table_id`
- `status`
- 6 个座位的公开状态
- 每个已入座玩家的公开展示名和筹码
- 当前 Button
- 当前手牌 id
- 当前手牌公开摘要

快照不得包含：

- 对手未公开底牌。
- 未发出的牌。
- PokerKit 内部对象。
- 可还原牌堆顺序的信息。

## 5. 状态流

牌桌启动：

```text
initialize_table
↓
seat_player until table can start
↓
start_table
↓
create_next_hand
↓
Game Loop drives hand
```

一手结束：

```text
Game Loop receives hand completed
↓
PokerKit Adapter returns settlement
↓
apply_hand_settlement
↓
move button
↓
create_next_hand if status is running
```

暂停：

```text
pause_table
↓
status = paused
↓
Game Loop stops requesting new actions at a safe boundary
```

## 6. 不变量

- `seat_count` 必须始终为 6。
- `seat_index` 不能超出 0 到 5。
- 同一玩家不能同时占用多个座位。
- Table Manager 只能通过 PokerKit Adapter 创建手牌或读取结算。
- 筹码生命周期由 Table Manager 维护，但单手内下注合法性和结算金额来自 PokerKit。
- 非法动作不能触发 `apply_hand_settlement` 或筹码变更。
- Button 移动只发生在一手正式结束后。

## 7. 错误处理

Table Manager 应返回平台错误，至少覆盖：

- 牌桌状态不允许执行该命令。
- 座位不存在。
- 座位已被占用。
- 玩家已在其他座位。
- 筹码状态无效。
- 当前没有可结算手牌。
- 结算结果与当前手牌不匹配。

## 8. 测试策略

Table Manager 单元测试使用 fake PokerKit Adapter 和 fake settlement：

- 初始化后固定 6 个座位。
- 玩家入座成功和重复入座失败。
- 已占用座位不能重复入座。
- `start_table` 只在满足最小开局条件时成功。
- 一手结算后筹码按 settlement 更新。
- Button 在一手结束后移动。
- 暂停状态不创建下一手。
- 快照不包含隐藏牌或 PokerKit 对象。

## 9. 开放问题

- 玩家离桌、坐下、补充筹码、断线重连是否进入 MVP。
- 开局最少需要几个已入座且有筹码玩家，需求文档未明确。
- 初始筹码、大小盲注和座位默认玩家配置未在当前需求中固定。

