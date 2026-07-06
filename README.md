# mcx-poker

`mcx-poker` is the platform layer around PokerKit.

PokerKit owns poker rules, state transitions, betting legality, showdown,
and pot settlement. This project owns tables, players, observations, actions,
history, and later API/UI layers.

## Local MVP

The default app starts one local 6-seat No-Limit Texas Hold'em cash table:

- seat 0: Human player `hero`
- seats 1-5: deterministic bots
- blinds: 1/2
- starting stack: 200

Run it locally:

```bash
python -m venv .venv
.venv/bin/python -m pip install -e '.[dev]'
PYTHONPATH=src .venv/bin/uvicorn mcx_poker.delivery.api:app --host 127.0.0.1 --port 8000
```

Open <http://127.0.0.1:8000/>. The page connects as `hero` by default and uses
WebSocket `/ws/table` for actions.

Useful API endpoints:

```bash
curl http://127.0.0.1:8000/api/table
curl -X POST http://127.0.0.1:8000/api/table/control \
  -H 'content-type: application/json' \
  -d '{"table_id":"local-table","command":"start"}'
```

## Verification

```bash
.venv/bin/python -m pytest
.venv/bin/python -m mypy src tests
.venv/bin/python -m ruff check .
.venv/bin/python -m ruff format --check .
rg "from pokerkit|import pokerkit" src tests
```

PokerKit imports are intentionally limited to
`src/mcx_poker/engine/pokerkit_adapter.py` and its adapter tests.

## Authorship

This project was primarily written with OpenAI Codex.
