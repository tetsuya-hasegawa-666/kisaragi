# Streaming

## JSON Lines を stream する

JSON Lines を stream するときは、return type を宣言し、`yield` で data を返す。

```python
@app.get("/items/stream")
async def stream_items() -> AsyncIterable[Item]:
    for item in items:
        yield item
```

## Server-Sent Events（SSE）

Server-Sent Events を stream するときは、`response_class=EventSourceResponse` を使い、endpoint から item を `yield` する。

通常 object は `data:` field として自動的に JSON serialize される。serialize を Pydantic に任せるため、return type を宣言する。

```python
from collections.abc import AsyncIterable

from fastapi import FastAPI
from fastapi.sse import EventSourceResponse
from pydantic import BaseModel

app = FastAPI()


class Item(BaseModel):
    name: str
    price: float


@app.get("/items/stream", response_class=EventSourceResponse)
async def stream_items() -> AsyncIterable[Item]:
    yield Item(name="Plumbus", price=32.99)
    yield Item(name="Portal Gun", price=999.99)
```

`event`、`id`、`retry`、`comment` を細かく制御したい場合は、`ServerSentEvent` instance を `yield` する。

```python
from collections.abc import AsyncIterable

from fastapi import FastAPI
from fastapi.sse import EventSourceResponse, ServerSentEvent

app = FastAPI()


@app.get("/events", response_class=EventSourceResponse)
async def stream_events() -> AsyncIterable[ServerSentEvent]:
    yield ServerSentEvent(data={"status": "started"}, event="status", id="1")
    yield ServerSentEvent(data={"progress": 50}, event="progress", id="2")
```

JSON encoding せず、整形済み文字列をそのまま送るときは `data` ではなく `raw_data` を使う。

```python
yield ServerSentEvent(raw_data="plain text line", event="log")
```

## bytes を stream する

bytes を stream するときは、`StreamingResponse` またはその subclass を `response_class=` に指定し、`yield` で data を返す。

```python
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from app.utils import read_image

app = FastAPI()


class PNGStreamingResponse(StreamingResponse):
    media_type = "image/png"

@app.get("/image", response_class=PNGStreamingResponse)
def stream_image_no_async_no_annotation():
    with read_image() as image_file:
        yield from image_file
```

`StreamingResponse` を直接 return するより、この形を優先する。

```python
# DO NOT DO THIS

import anyio
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from app.utils import read_image

app = FastAPI()


class PNGStreamingResponse(StreamingResponse):
    media_type = "image/png"


@app.get("/")
async def main():
    return PNGStreamingResponse(read_image())
```
