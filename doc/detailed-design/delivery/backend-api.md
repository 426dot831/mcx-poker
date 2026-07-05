# Backend API 详细设计

## 1. 模块目标

Backend API 提供本地牌桌的基础控制能力和查询能力，并接收 Human Player 所需的控制请求。

MVP API 面向“本地可玩”闭环，不承担：

- 账号体系。
- 认证授权。
- 多桌大厅。
- 线上部署。
- 历史手牌查询。
- OpenAPI 交付物。

认证、版本路径和 OpenAPI 是否进入第一版仍未确认。

## 2. 模块职责

Backend API 负责：

- 接收牌桌初始化、开始、暂停、继续、重开等控制命令。
- 接收玩家加入座位请求。
- 查询当前牌桌快照。
- 将请求转换为 Table Manager 命令。
- 返回平台层错误，不暴露内部异常。

Backend API 不负责：

- 扑克规则校验。
- 直接调用 PokerKit。
- 直接修改 Game Loop 状态。
- 生成玩家 Observation 的隐藏信息。

## 3. 操作契约

本设计先定义操作，不冻结 HTTP 路径。

| 操作 | 输入 | 输出 |
| --- | --- | --- |
| `initialize_table` | 可选牌桌配置 | `TableSnapshot` |
| `seat_player` | `seat_index`、`player_name`、`controller_type`、`stack` | `TableSnapshot` |
| `start_table` | `table_id` | `TableSnapshot` |
| `pause_table` | `table_id` | `TableSnapshot` |
| `resume_table` | `table_id` | `TableSnapshot` |
| `reset_table` | `table_id` | `TableSnapshot` |
| `get_table` | `table_id` | `TableSnapshot` |

是否通过 API 提交 Human Player 动作，或只通过 WebSocket 提交，需求未明确。概要设计允许 WebSocket 或 API 提交 Action Model，因此 API 层可以预留 `submit_action` 操作，但不作为必须冻结的 HTTP 接口。

## 4. 请求模型

`SeatPlayerRequest` 字段概念：

| 字段 | 说明 |
| --- | --- |
| `seat_index` | 0 到 5 |
| `player_name` | 展示名 |
| `controller_type` | `human` 或 `bot`；未来可扩展 |
| `starting_stack` | 入座筹码 |

`TableControlRequest` 字段概念：

| 字段 | 说明 |
| --- | --- |
| `table_id` | 当前本地牌桌 |
| `command` | start、pause、resume、reset |

初始筹码、大小盲和 Bot 类型是否由 API 入参决定仍未确认。若未确认，API 不应在文档中承诺默认值。

## 5. 响应模型

`ApiResponse` 字段概念：

| 字段 | 说明 |
| --- | --- |
| `ok` | 是否成功 |
| `data` | 成功时的平台层 DTO |
| `error` | 失败时的平台错误 |

`TableSnapshot` 应来自 Table Manager，包含公开牌桌状态，不包含：

- 对手未公开底牌。
- 未发出的牌。
- PokerKit 原始对象。
- Controller 内部等待对象。

玩家自己的底牌应通过玩家视角 Observation 提供，而不是通过通用 `get_table` 泄露。

## 6. 错误处理

API 错误码至少覆盖：

- `invalid_request`
- `table_not_initialized`
- `table_state_conflict`
- `seat_not_found`
- `seat_occupied`
- `player_already_seated`
- `unknown_controller_type`
- `game_not_started`
- `internal_error`

API 层应把模块错误映射为稳定平台错误，不向前端返回 Python traceback 或 PokerKit 异常。

## 7. 并发与一致性

即使 MVP 是本地应用，API 也必须遵守后端权威原则：

- 同一命令只由 Table Manager 修改状态。
- 控制命令和 Game Loop 行动提交不能交叉破坏当前手牌。
- `reset_table` 必须让当前 pending Human 动作失效。
- `pause_table` 必须在 Game Loop 安全边界生效。

具体锁、队列或事件循环机制取决于后端框架和同步/异步选择，当前需求未确认。

## 8. 测试策略

API 层测试使用 fake Table Manager：

- 初始化牌桌返回固定 6 座快照。
- 入座请求参数校验。
- 已占座位返回错误。
- 开始牌桌调用 Table Manager 命令。
- 暂停、继续、重开返回最新快照。
- 通用 `get_table` 不包含隐藏底牌。
- Table Manager 错误被转换成 API 错误。

## 9. 开放问题

- 第一版 API 是否需要认证。
- API 是否需要稳定版本路径，例如 `/api/v1`。
- 是否需要 OpenAPI 文档作为交付物。
- Human Player 动作是否也需要 HTTP 提交通道，还是只走 WebSocket。
- 初始筹码、大小盲、Bot 类型是否由 API 入参配置。

