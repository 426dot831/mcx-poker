# Backend API 任务列表

来源：`doc/detailed-design/delivery/backend-api.md`

目标：提供本地可玩 MVP 需要的牌桌控制和查询能力，把外部请求转换为 Table Manager 命令，并返回平台层 DTO。

## 最小任务

- [x] API-01 选择最小后端实现方式，并记录选择理由。
- [x] API-02 定义统一 `ApiResponse`，包含 `ok`、`data`、`error`。
- [x] API-03 定义 `SeatPlayerRequest`，包含 `seat_index`、`player_name`、`controller_type`、`starting_stack`。
- [x] API-04 定义 `TableControlRequest`，包含 `table_id` 和控制命令。
- [x] API-05 实现 `initialize_table` 操作，返回 `TableSnapshot`。
- [x] API-06 实现 `seat_player` 操作，调用 Table Manager 入座命令。
- [x] API-07 实现 `start_table` 操作，调用 Table Manager 开始牌桌。
- [x] API-08 实现 `pause_table` 操作，调用 Table Manager 暂停命令。
- [x] API-09 实现 `resume_table` 操作，调用 Table Manager 继续命令。
- [x] API-10 实现 `reset_table` 操作，调用 Table Manager 重开命令。
- [x] API-11 实现 `get_table` 操作，返回公开 `TableSnapshot`。
- [x] API-12 预留 `submit_action` 操作边界，但不强制冻结 HTTP 路径。
- [x] API-13 实现请求字段校验，拒绝缺字段、非法座位、非法 controller 类型和非法筹码。
- [x] API-14 将 Table Manager 错误映射为稳定 API 错误码。
- [x] API-15 捕获未知异常并返回 `internal_error`，不暴露 traceback。
- [x] API-16 确保通用 `get_table` 不返回任何玩家私有底牌。
- [x] API-17 确保 API 层不直接 import PokerKit。
- [x] API-18 处理 `reset_table` 后 pending Human action 失效的边界调用。
- [x] API-19 处理 `pause_table` 与 Game Loop 安全边界的协作调用。
- [x] API-20 提供本地开发启动入口或集成到应用启动流程。

## 测试与验收

- [x] API-T01 使用 fake Table Manager 测试初始化返回固定 6 座快照。
- [x] API-T02 测试入座请求参数缺失或非法时返回 `invalid_request`。
- [x] API-T03 测试已占座位返回 `seat_occupied`。
- [x] API-T04 测试重复玩家入座返回 `player_already_seated`。
- [x] API-T05 测试未知 controller 类型返回 `unknown_controller_type`。
- [x] API-T06 测试 start、pause、resume、reset 都调用正确 Table Manager 命令。
- [x] API-T07 测试 `get_table` 响应不包含隐藏底牌或 PokerKit 对象。
- [x] API-T08 测试 Table Manager 业务错误会转换成 API 错误结构。
- [x] API-T09 测试未知异常不会把 Python traceback 返回给前端。

## 不进入本模块

- [ ] API-X01 不实现账号体系。
- [ ] API-X02 不实现认证授权。
- [ ] API-X03 不实现多桌大厅。
- [ ] API-X04 不交付 OpenAPI，除非后续需求确认。
- [ ] API-X05 不提供持久化历史手牌查询。
