# MVP 任务进度

说明：当某个模块对应任务文件中的最小任务和测试验收项全部完成后，再勾选本文件中的模块完成状态。

## 模块完成状态

- [x] Action Model：`doc/tasks/action-model.md`
- [x] Action Validator：`doc/tasks/action-validator.md`
- [x] PokerKit Adapter：`doc/tasks/pokerkit-adapter.md`
- [x] Table Manager：`doc/tasks/table-manager.md`
- [x] Temporary Hand Event Log：`doc/tasks/temporary-hand-event-log.md`
- [x] Observation System：`doc/tasks/observation-system.md`
- [x] Player Controller：`doc/tasks/player-controller.md`
- [x] Game Loop：`doc/tasks/game-loop.md`
- [x] Backend API：`doc/tasks/backend-api.md`
- [x] WebSocket Gateway：`doc/tasks/websocket-gateway.md`
- [x] Frontend Poker Table UI：`doc/tasks/frontend-poker-table-ui.md`
- [x] Future Extension Interfaces：`doc/tasks/future-extension-interfaces.md`

## 建议实施顺序

- [x] 01 Action Model
- [x] 02 PokerKit Adapter
- [x] 03 Table Manager
- [x] 04 Temporary Hand Event Log
- [x] 05 Observation System
- [x] 06 Player Controller
- [x] 07 Action Validator
- [x] 08 Game Loop
- [x] 09 Backend API
- [x] 10 WebSocket Gateway
- [x] 11 Frontend Poker Table UI
- [x] 12 Future Extension Interfaces

## MVP 闭环验收

- [x] 可以初始化一张固定 6 座本地牌桌。
- [x] 可以让玩家入座并启动普通 No-Limit Texas Hold'em 现金桌。
- [x] PokerKit Adapter 可以创建手牌并读取当前 actor。
- [x] Game Loop 可以驱动一手牌到结束。
- [x] Table Manager 可以在一手结束后更新筹码并移动 Button。
- [x] Human Player 可以通过 Web UI 提交动作。
- [x] 至少一个 Bot Controller 可以通过同一 `Observation -> Action` 契约行动。
- [x] Observation 不泄露对手未公开底牌、未发出的牌或 PokerKit 内部状态。
- [x] Action Model 支持 `Fold`、`Check`、`Call`、`RaiseTo(amount)`、`AllIn`。
- [x] `RaiseTo(amount)` 的 amount 表示总下注额。
- [x] `AllIn` 是独立动作，不通过特殊金额表达。
- [x] 非法动作会报错，并让同一牌手重新选择。
- [x] 前端只展示后端状态，不计算规则、底池、胜负或行动玩家。
- [x] 临时事件日志能支持当前手牌 UI 展示和调试。
- [x] LLM、GTO、Coach 只保留接口边界，不阻塞 MVP。
