# Dependency Injection

dependencies は次のような場合に使う。

* Pydantic validation だけでは表現できず、追加ロジックが必要なとき
* 外部 resource に依存する、または別の意味で block しうるとき
* 他の dependency がその結果を必要とする sub-dependency のとき
* 複数 endpoint で共有し、早期 error、認証などに使えるとき
* `yield` を使って cleanup が必要なとき
* header、query parameter など request 入力を必要とするとき

## `yield` と `scope` を使う dependency

`yield` を使う dependency では、終了処理をいつ実行するかを `scope` で定義できる。

既定の `"request"` scope は、response を返した後に終了処理を走らせる。

```python
from typing import Annotated

from fastapi import Depends, FastAPI

app = FastAPI()


def get_db():
    db = DBSession()
    try:
        yield db
    finally:
        db.close()


DBDep = Annotated[DBSession, Depends(get_db)]


@app.get("/items/")
async def read_items(db: DBDep):
    return db.query(Item).all()
```

`"function"` scope は、response data を生成した後かつ client へ返す前に終了処理を走らせたいときに使う。

```python
from typing import Annotated

from fastapi import Depends, FastAPI

app = FastAPI()


def get_username():
    try:
        yield "Rick"
    finally:
        print("Cleanup up before response is sent")

UserNameDep = Annotated[str, Depends(get_username, scope="function")]

@app.get("/users/me")
def get_user_me(username: UserNameDep):
    return username
```

## class dependency

可能なら class dependency は作らない。

class が必要でも、まずは class instance を返す通常の function dependency を優先する。

推奨例:

```python
from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, FastAPI

app = FastAPI()


@dataclass
class DatabasePaginator:
    offset: int = 0
    limit: int = 100
    q: str | None = None

    def get_page(self) -> dict:
        # Simulate a page of data
        return {
            "offset": self.offset,
            "limit": self.limit,
            "q": self.q,
            "items": [],
        }


def get_db_paginator(
    offset: int = 0, limit: int = 100, q: str | None = None
) -> DatabasePaginator:
    return DatabasePaginator(offset=offset, limit=limit, q=q)


PaginatorDep = Annotated[DatabasePaginator, Depends(get_db_paginator)]


@app.get("/items/")
async def read_items(paginator: PaginatorDep):
    return paginator.get_page()
```

非推奨例:

```python
# DO NOT DO THIS
from typing import Annotated

from fastapi import Depends, FastAPI

app = FastAPI()


class DatabasePaginator:
    def __init__(self, offset: int = 0, limit: int = 100, q: str | None = None):
        self.offset = offset
        self.limit = limit
        self.q = q

    def get_page(self) -> dict:
        # Simulate a page of data
        return {
            "offset": self.offset,
            "limit": self.limit,
            "q": self.q,
            "items": [],
        }


@app.get("/items/")
async def read_items(paginator: Annotated[DatabasePaginator, Depends()]):
    return paginator.get_page()
```
