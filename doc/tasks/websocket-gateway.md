# WebSocket Gateway 任务列表

来源：`doc/detailed-design/delivery/websocket-gateway.md`

目标：向前端实时推送牌桌状态和行动事件，并接收 Human Player 的动作提交；Gateway 只做连接和消息形状校验，不做规则判定。

## 最小任务

- [x] WS-01 选择 WebSocket 实现方式，并与 Backend API 后端框架保持一致或清晰集成。
- [x] WS-02 定义连接状态，包含 `connection_id`、`player_id`、`seat_index`、`table_id`、`visibility_scope`。
- [x] WS-03 实现连接建立和连接关闭管理。
- [x] WS-04 实现 Human 连接绑定到 player/seat 的流程。
- [x] WS-05 实现 `request_snapshot` 客户端事件。
- [x] WS-06 实现 `submit_action` 客户端事件 shape 校验。
- [x] WS-07 校验提交连接是否绑定到对应 player/seat。
- [x] WS-08 将合法形状的 `submit_action` 转交 Human Player Controller。
- [x] WS-09 过期 `turn_id` 或非当前玩家动作返回 `action_rejected`。
- [x] WS-10 实现广播 `table_snapshot`。
- [x] WS-11 实现广播 `hand_started`。
- [x] WS-12 实现私有 `hole_cards_dealt`。
- [x] WS-13 实现广播 `board_updated`。
- [x] WS-14 实现私有 `action_requested`，包含玩家视角 Observation。
- [x] WS-15 实现广播 `player_acted`。
- [x] WS-16 实现私有 `action_rejected`。
- [x] WS-17 实现广播 `hand_ended`。
- [x] WS-18 实现广播 `table_paused`、`table_resumed`、`table_reset`。
- [x] WS-19 区分广播事件和私有事件，避免通过广播泄露底牌。
- [x] WS-20 所有事件 payload 使用平台层 DTO，不包含 PokerKit 对象。
- [x] WS-21 将 Gateway 错误映射为 `invalid_message`、`unknown_event_type`、`connection_not_bound_to_player`、`stale_turn`、`not_current_actor`、`action_rejected`、`table_unavailable`。
- [x] WS-22 支持 fake Human Controller 测试，不依赖真实 Game Loop。
- [x] WS-23 确保 Gateway 不 import PokerKit。

## 测试与验收

- [x] WS-T01 收到 `action_requested` 时只有对应连接获得私有 Observation。
- [x] WS-T02 广播 `table_snapshot` 不包含隐藏底牌。
- [x] WS-T03 `submit_action` 缺字段被拒绝。
- [x] WS-T04 过期 `turn_id` 被拒绝。
- [x] WS-T05 非绑定 player 的连接不能替其他玩家行动。
- [x] WS-T06 Action Validator 返回非法动作时 Gateway 向原连接发送错误。
- [x] WS-T07 私有 `hole_cards_dealt` 不会广播给其他连接。
- [x] WS-T08 fake Human Controller 可独立测试 Gateway。

## 不进入本模块

- [ ] WS-X01 不判断动作是否合法。
- [ ] WS-X02 不直接调用 PokerKit。
- [ ] WS-X03 不实现旁观者，除非后续确认。
- [ ] WS-X04 不支持同一用户多客户端特殊语义，除非后续确认。
- [ ] WS-X05 不冻结长期公共事件 schema。
