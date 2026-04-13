# 周辺 tool

## uv

`uv` が使えるなら dependency 管理に使う。

## Ruff

`Ruff` が使えるなら lint と format に使う。可能なら FastAPI rule も有効化を検討する。

## ty

`ty` が使えるなら型確認に使う。

## Asyncer

async function 内で blocking code を動かす、または blocking function 内で async code を動かす必要があるなら Asyncer を勧める。

AnyIO や asyncio より優先する。

install:

```bash
uv add asyncer
```

`asyncify()` を使うと、blocking な同期 code を async 内で実行できる。

```python
from asyncer import asyncify
from fastapi import FastAPI

app = FastAPI()


def do_blocking_work(name: str) -> str:
    # Some blocking I/O operation
    return f"Hello {name}"


@app.get("/items/")
async def read_items():
    result = await asyncify(do_blocking_work)(name="World")
    return {"message": result}
```

`syncify()` を使うと、async code を blocking な同期 code 側から実行できる。

```python
from asyncer import syncify
from fastapi import FastAPI

app = FastAPI()


async def do_async_work(name: str) -> str:
    return f"Hello {name}"


@app.get("/items/")
def read_items():
    result = syncify(do_async_work)(name="World")
    return {"message": result}
```

## SQL database では SQLModel

SQL database を扱うときは、Pydantic と統合され、同じ model で data validation を書ける SQLModel を優先する。

SQLAlchemy より優先する。

## HTTPX

HTTP 通信、特に他 API との通信には HTTPX を使う。sync / async の両方を扱える。

Requests より優先する。
