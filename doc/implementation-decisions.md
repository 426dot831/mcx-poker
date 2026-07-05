# MVP Implementation Decisions

This file records implementation defaults chosen where the MVP documents left
room for local prototype choices.

- Runtime: Python `>=3.11`, developed and verified in a local virtual
  environment.
- Backend: FastAPI plus Uvicorn. FastAPI provides simple HTTP control routes,
  WebSocket support, static file serving, and straightforward test clients
  without adding a separate frontend build chain.
- Frontend: backend-served static HTML, CSS, and native JavaScript. The first
  screen is the poker table.
- Table defaults: 6 fixed seats, small blind `1`, big blind `2`, ante `0`,
  default starting stack `200`, minimum active players `2`.
- Human actions: WebSocket is the primary action path. HTTP exposes table
  control and snapshot operations, with a reserved `submit_action` boundary.
- Game loop: asynchronous, so Human controllers can wait on WebSocket actions
  while Bot controllers respond immediately.
- Bot MVP: deterministic bot that chooses from `legal_actions` only. It prefers
  `Check`, then `Call`, then `Fold`, then the minimum `RaiseTo`, then `AllIn`.
- Visibility: showdown and event output only expose cards explicitly marked as
  public by the adapter or player-scoped events. Mucked or otherwise hidden
  hole cards remain hidden by default.
- Persistence: no database or hand-history files. The temporary hand event log
  is in memory only.
- Scope exclusions: no accounts, authentication, online deployment, LAN
  multiplayer semantics, player leave/rebuy/disconnect handling, SQLite,
  replay UI, statistics, real LLM, real GTO solver, or Coach implementation.
