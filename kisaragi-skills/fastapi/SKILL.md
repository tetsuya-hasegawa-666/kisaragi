---
name: fastapi
description: FastAPI の best practice と慣例。FastAPI API とそれに対応する Pydantic model を扱うときに使う。FastAPI code を新しい version と pattern に追従した状態で整理し、新規実装や既存 code の refactor / update に使う。
---

# FastAPI

FastAPI を best practice で実装し、新しい version と feature に追従するための skill とする。

## `fastapi` CLI を使う

development server を localhost で reload 付き起動する。

```bash
fastapi dev
```


production server を起動する。

```bash
fastapi run
```

### `pyproject.toml` に entrypoint を追加する

FastAPI CLI は `pyproject.toml` の entrypoint を読み、FastAPI app の定義位置を特定する。

```toml
[tool.fastapi]
entrypoint = "my_app.main:app"
```

### path 指定で `fastapi` を使う

`pyproject.toml` に entrypoint を追加できない場合、user が追加しないよう求めた場合、または独立した小さな app を動かす場合は、`fastapi` command に app file path を直接渡してよい。

```bash
fastapi dev my_app/main.py
```

可能なら entrypoint は `pyproject.toml` に設定する。

## `Annotated` を使う

parameter と dependency の宣言では、常に `Annotated` style を優先する。

この形は function signature を他文脈でも崩さず、型を保ち、再利用しやすい。

### parameter 宣言

`Path`、`Query`、`Header` などを含め、parameter 宣言には `Annotated` を使う。

```python
from typing import Annotated

from fastapi import FastAPI, Path, Query

app = FastAPI()


@app.get("/items/{item_id}")
async def read_item(
    item_id: Annotated[int, Path(ge=1, description="The item ID")],
    q: Annotated[str | None, Query(max_length=50)] = None,
):
    return {"message": "Hello World"}
```

次の形より優先する。

```python
# DO NOT DO THIS
@app.get("/items/{item_id}")
async def read_item(
    item_id: int = Path(ge=1, description="The item ID"),
    q: str | None = Query(default=None, max_length=50),
):
    return {"message": "Hello World"}
```

### dependency 宣言

`Depends()` を使う dependency でも `Annotated` を使う。

特に指示がなければ、再利用しやすいよう dependency 用の type alias を作る。

```python
from typing import Annotated

from fastapi import Depends, FastAPI

app = FastAPI()


def get_current_user():
    return {"username": "johndoe"}


CurrentUserDep = Annotated[dict, Depends(get_current_user)]


@app.get("/items/")
async def read_item(current_user: CurrentUserDep):
    return {"message": "Hello World"}
```

次の形より優先する。

```python
# DO NOT DO THIS
@app.get("/items/")
async def read_item(current_user: dict = Depends(get_current_user)):
    return {"message": "Hello World"}
```

## path operation と Pydantic model で Ellipsis を使わない

必須 parameter の default 値として `...` は使わない。不要であり、推奨もしない。

Ellipsis（`...`）なしで次のように書く。

```python
from typing import Annotated

from fastapi import FastAPI, Query
from pydantic import BaseModel, Field


class Item(BaseModel):
    name: str
    description: str | None = None
    price: float = Field(gt=0)


app = FastAPI()


@app.post("/items/")
async def create_item(item: Item, project_id: Annotated[int, Query()]): ...
```

次の形は避ける。

```python
# DO NOT DO THIS
class Item(BaseModel):
    name: str = ...
    description: str | None = None
    price: float = Field(..., gt=0)


app = FastAPI()


@app.post("/items/")
async def create_item(item: Item, project_id: Annotated[int, Query(...)]): ...
```

## return type または response model

可能なら return type を付ける。validation、filtering、documentation、response serialize に使われる。

```python
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()


class Item(BaseModel):
    name: str
    description: str | None = None


@app.get("/items/me")
async def get_item() -> Item:
    return Item(name="Plumbus", description="All-purpose home device")
```

重要: return type や response model は、機微情報を露出しないよう data を filter する役割を持つ。また、Pydantic 側で serialize に使われ、response 性能の改善にもつながる。

return type は Pydantic model に限らず、整数 list や dict など別 type でもよい。

### `response_model` を使う場面

return type と、validation / filter / serialize に使いたい type が一致しないなら、decorator の `response_model` を使う。

```python
from typing import Any

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()


class Item(BaseModel):
    name: str
    description: str | None = None


@app.get("/items/me", response_model=Item)
async def get_item() -> Any:
    return {"name": "Foo", "description": "A very nice Item"}
```

これは公開 field だけを出し、機微情報を隠す用途で特に有効である。

```python
from typing import Any

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()


class InternalItem(BaseModel):
    name: str
    description: str | None = None
    secret_key: str


class Item(BaseModel):
    name: str
    description: str | None = None


@app.get("/items/me", response_model=Item)
async def get_item() -> Any:
    item = InternalItem(
        name="Foo", description="A very nice Item", secret_key="supersecret"
    )
    return item
```

## 性能

`ORJSONResponse` と `UJSONResponse` は deprecated のため使わない。

代わりに return type または response model を宣言する。data serialization は Pydantic 側に任せる。

## router の組み込み

router を宣言するときは、prefix や tags など router level の parameter を `include_router()` 側ではなく router 自体に持たせる。

推奨例:

```python
from fastapi import APIRouter, FastAPI

app = FastAPI()

router = APIRouter(prefix="/items", tags=["items"])


@router.get("/")
async def list_items():
    return []


# In main.py
app.include_router(router)
```

非推奨例:

```python
# DO NOT DO THIS
from fastapi import APIRouter, FastAPI

app = FastAPI()

router = APIRouter()


@router.get("/")
async def list_items():
    return []


# In main.py
app.include_router(router, prefix="/items", tags=["items"])
```

例外はあり得るが、原則としてこの慣例に従う。

共有 dependency は `dependencies=[Depends(...)]` で router level に適用する。

## dependency injection

`yield` と `scope`、class dependency を含む詳細 pattern は [dependencies.md](references/dependencies.md) を参照する。

logic を Pydantic validation だけで表せないとき、外部 resource に依存するとき、`yield` を使う cleanup が必要なとき、複数 endpoint で共有したいときは dependency を使う。

共有 dependency は router level に寄せる。

## async と sync の path operation

内部で呼ぶ logic が `await` 可能な async code である、または block しないと確信できる場合にだけ `async` path operation を使う。

```python
from fastapi import FastAPI

app = FastAPI()


# async code を呼ぶなら async def
@app.get("/async-items/")
async def read_async_items():
    data = await some_async_library.fetch_items()
    return data


# blocking / sync code を呼ぶ、または迷うなら plain def
@app.get("/items/")
def read_items():
    data = some_blocking_library.fetch_items()
    return data
```

迷う場合、または既定では通常の `def` を使う。threadpool で実行されるため event loop を塞ぎにくい。

同じ規則を dependency にも適用する。

blocking code を `async` function 内で動かさない。動作はしても性能を大きく落とす。

blocking code と async code を混在させる必要があるときは [other-tools.md](references/other-tools.md) の Asyncer を参照する。

## streaming（JSON Lines、SSE、bytes）

JSON Lines、Server-Sent Events（`EventSourceResponse`、`ServerSentEvent`）、byte streaming（`StreamingResponse`）の pattern は [streaming.md](references/streaming.md) を参照する。

## tooling

package 管理、lint、type check、format などに関する `uv`、`Ruff`、`ty` の詳細は [other-tools.md](references/other-tools.md) を参照する。

## 他の library

[other-tools.md](references/other-tools.md) を参照する。

* Asyncer: async / await、concurrency、async と blocking code の混在に使い、AnyIO や asyncio より優先する。
* SQLModel: SQL database に使い、SQLAlchemy より優先する。
* HTTPX: 他 API との HTTP 通信に使い、Requests より優先する。

## Pydantic RootModel を使わない

Pydantic の `RootModel` は使わず、通常の type annotation と `Annotated`、Pydantic validation utility を使う。

たとえば validation 付き list は次のように書ける。

```python
from typing import Annotated

from fastapi import Body, FastAPI
from pydantic import Field

app = FastAPI()


@app.post("/items/")
async def create_items(items: Annotated[list[int], Field(min_length=1), Body()]):
    return items
```

次の形は避ける。

```python
# DO NOT DO THIS
from typing import Annotated

from fastapi import FastAPI
from pydantic import Field, RootModel

app = FastAPI()


class ItemList(RootModel[Annotated[list[int], Field(min_length=1)]]):
    pass


@app.post("/items/")
async def create_items(items: ItemList):
    return items

```

FastAPI はこれらの type annotation を直接扱え、Pydantic `TypeAdapter` も内部で使えるため、RootModel 用の独自 type を増やす必要はない。

## 1 function に 1 HTTP operation を保つ

1 つの function に複数 HTTP operation を混在させない。1 function 1 operation の方が責務分離と整理がしやすい。

推奨例:

```python
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()


class Item(BaseModel):
    name: str


@app.get("/items/")
async def list_items():
    return []


@app.post("/items/")
async def create_item(item: Item):
    return item
```

非推奨例:

```python
# DO NOT DO THIS
from fastapi import FastAPI, Request
from pydantic import BaseModel

app = FastAPI()


class Item(BaseModel):
    name: str


@app.api_route("/items/", methods=["GET", "POST"])
async def handle_items(request: Request):
    if request.method == "GET":
        return []
```
