# Temporary Hand Event Log 详细设计

## 1. 模块目标

Temporary Hand Event Log 在 MVP 中记录当前手牌的临时事件，用于 UI 展示、调试和后续 Hand History 演进。

本模块不负责：

- 持久化每一手牌。
- SQLite 存储。
- Replay 完整实现。
- 统计系统。
- 兼容 PokerStars 或通用 Hand History 文本格式。

MVP 不要求保存每一手牌到本地文件或数据库。

## 2. 事件范围

MVP 临时事件可包含：

- 手牌开始。
- 座位和初始筹码快照。
- 盲注和前注公开摘要。
- 发牌事件的公开部分。
- 公共牌更新。
- 玩家成功动作。
- 非法动作错误。
- 手牌结束。
- 结算摘要。

事件只保证当前运行期间可用，不承诺跨进程或跨重启可查询。

## 3. 数据结构

`HandEvent` 字段概念：

| 字段 | 说明 |
| --- | --- |
| `hand_id` | 事件所属手牌 |
| `sequence_number` | 当前手牌内单调递增序号 |
| `event_type` | 事件类型 |
| `actor_player_id` | 动作玩家，可为空 |
| `actor_seat_index` | 动作座位，可为空 |
| `public_payload` | 可广播或可展示的公开数据 |
| `private_payload` | 只允许发给特定玩家的数据，可为空 |
| `visibility` | public 或 player-scoped |
| `created_at` | 事件创建时间，或仅使用 sequence number |

是否必须记录真实 timestamp 未确认。MVP 可只依赖 `sequence_number` 保证顺序。

## 4. 事件类型

建议事件类型：

| 类型 | 说明 |
| --- | --- |
| `hand_started` | 新手牌开始 |
| `seat_snapshot` | 本手座位和初始筹码 |
| `hole_cards_dealt` | 玩家私有底牌事件 |
| `board_dealt` | 公共牌更新 |
| `action_succeeded` | 玩家成功动作 |
| `action_rejected` | 非法动作错误 |
| `pot_updated` | 底池摘要更新 |
| `showdown` | 摊牌公开信息 |
| `settlement` | 结算摘要 |
| `hand_ended` | 手牌结束 |

`hole_cards_dealt` 必须是 player-scoped 私有事件，不能作为公开事件广播。

## 5. 写入来源

写入模块：

- Game Loop：写入行动请求、成功动作、非法动作、手牌结束。
- Table Manager：写入本手座位和初始筹码快照、结算摘要。
- PokerKit Adapter：提供公共牌、动作结果和结算数据摘要。

Temporary Hand Event Log 不主动读取 PokerKit。

## 6. 读取用途

读取方：

- WebSocket Gateway：将事件转换为前端通知。
- Observation System：提供当前手牌公开动作历史。
- 调试工具：查看当前手牌发生了什么。
- 未来 Hand History：迁移或扩展为持久化事件模型。

读取接口字段概念：

| 接口 | 说明 |
| --- | --- |
| `append(event)` | 追加事件 |
| `list_public_events(hand_id)` | 读取公开事件 |
| `list_player_events(hand_id, player_id)` | 读取指定玩家可见事件 |
| `clear_hand(hand_id)` | 清理当前手牌事件 |
| `get_last_sequence(hand_id)` | 获取最后事件序号 |

## 7. 隐私规则

事件日志内部即使包含私有 payload，也必须在读取时按可见性过滤。

公开事件不得包含：

- 对手未公开底牌。
- 未发出的牌。
- 牌堆顺序。
- PokerKit 原始对象。

私有事件只能发给目标玩家：

- 自己底牌。
- 自己动作错误。
- 自己行动请求。

手牌结束后是否公开所有玩家底牌未确认，因此默认仍按“只公开已摊牌或已明确公开的信息”处理。

## 8. 生命周期

MVP 生命周期：

```text
hand_started
↓
append events during hand
↓
hand_ended
↓
events remain available until next hand cleanup policy runs
```

是否保留上一手供 UI 短暂展示、是否保留 N 手牌，需求未确认。MVP 可只保证当前手牌和刚结束摘要可用。

## 9. 测试策略

- sequence number 单调递增。
- 公开事件读取不包含私有底牌。
- 指定玩家读取能看到自己的私有底牌事件。
- 非法动作事件不记录为成功动作。
- hand ended 后能读取结算摘要。
- clear hand 后事件不可再读取。
- 事件 payload 不包含 PokerKit 原始对象。

## 10. 开放问题

- 手牌结束后是否公开所有玩家底牌。
- 是否兼容 PokerStars 或通用 HH 文本格式。
- 是否保留上一手或最近 N 手牌用于 UI。
- 后续持久化 Hand History 使用本地文件还是 SQLite。
- 是否需要真实 timestamp，还是 sequence number 足够。

