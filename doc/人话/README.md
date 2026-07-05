# mcx-poker 源码人话文档索引

这个目录按 `/src` 的结构重排。想看哪个源码文件，就在这里找同路径的 `.py.md` 讲解文件。

例如源码：

```text
src/mcx_poker/engine/validator.py
```

对应讲解：

```text
doc/人话/mcx_poker/engine/validator.py.md
```

## 文件列表

- [`mcx_poker/__init__.py.md`](mcx_poker/__init__.py.md)：对应 `src/mcx_poker/__init__.py`
- [`mcx_poker/delivery/__init__.py.md`](mcx_poker/delivery/__init__.py.md)：对应 `src/mcx_poker/delivery/__init__.py`
- [`mcx_poker/delivery/api.py.md`](mcx_poker/delivery/api.py.md)：对应 `src/mcx_poker/delivery/api.py`
- [`mcx_poker/delivery/local.py.md`](mcx_poker/delivery/local.py.md)：对应 `src/mcx_poker/delivery/local.py`
- [`mcx_poker/delivery/websocket.py.md`](mcx_poker/delivery/websocket.py.md)：对应 `src/mcx_poker/delivery/websocket.py`
- [`mcx_poker/engine/__init__.py.md`](mcx_poker/engine/__init__.py.md)：对应 `src/mcx_poker/engine/__init__.py`
- [`mcx_poker/engine/actions.py.md`](mcx_poker/engine/actions.py.md)：对应 `src/mcx_poker/engine/actions.py`
- [`mcx_poker/engine/game_loop.py.md`](mcx_poker/engine/game_loop.py.md)：对应 `src/mcx_poker/engine/game_loop.py`
- [`mcx_poker/engine/pokerkit_adapter.py.md`](mcx_poker/engine/pokerkit_adapter.py.md)：对应 `src/mcx_poker/engine/pokerkit_adapter.py`
- [`mcx_poker/engine/validator.py.md`](mcx_poker/engine/validator.py.md)：对应 `src/mcx_poker/engine/validator.py`
- [`mcx_poker/extensions/__init__.py.md`](mcx_poker/extensions/__init__.py.md)：对应 `src/mcx_poker/extensions/__init__.py`
- [`mcx_poker/extensions/interfaces.py.md`](mcx_poker/extensions/interfaces.py.md)：对应 `src/mcx_poker/extensions/interfaces.py`
- [`mcx_poker/history/__init__.py.md`](mcx_poker/history/__init__.py.md)：对应 `src/mcx_poker/history/__init__.py`
- [`mcx_poker/history/events.py.md`](mcx_poker/history/events.py.md)：对应 `src/mcx_poker/history/events.py`
- [`mcx_poker/observation/__init__.py.md`](mcx_poker/observation/__init__.py.md)：对应 `src/mcx_poker/observation/__init__.py`
- [`mcx_poker/observation/builder.py.md`](mcx_poker/observation/builder.py.md)：对应 `src/mcx_poker/observation/builder.py`
- [`mcx_poker/players/__init__.py.md`](mcx_poker/players/__init__.py.md)：对应 `src/mcx_poker/players/__init__.py`
- [`mcx_poker/players/controllers.py.md`](mcx_poker/players/controllers.py.md)：对应 `src/mcx_poker/players/controllers.py`
- [`mcx_poker/table/__init__.py.md`](mcx_poker/table/__init__.py.md)：对应 `src/mcx_poker/table/__init__.py`
- [`mcx_poker/table/manager.py.md`](mcx_poker/table/manager.py.md)：对应 `src/mcx_poker/table/manager.py`

## 建议阅读顺序

1. `mcx_poker/engine/actions.py.md`：先理解动作数据格式。
2. `mcx_poker/engine/validator.py.md`：再看动作如何被校验。
3. `mcx_poker/engine/pokerkit_adapter.py.md`：理解项目如何和 PokerKit 对接。
4. `mcx_poker/engine/game_loop.py.md`：看一手牌如何被串起来推进。
5. `mcx_poker/table/manager.py.md`：看牌桌、座位和筹码如何管理。
6. `mcx_poker/delivery/*.py.md`：最后看 API、WebSocket 和本地运行如何接入外部世界。
