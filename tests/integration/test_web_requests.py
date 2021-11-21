from unittest.mock import AsyncMock, call

from pytest import fixture, mark

from xiao_asgi.applications import Xiao
from xiao_asgi.routing import HttpRoute, WebSocketRoute


@mark.asyncio
class TestHttpRequest:
    @fixture
    def app(self):
        return Xiao([HttpRoute("/")])

    async def test_http_request(self, app):
        receive = AsyncMock(
            return_value={
                "type": "http.request",
                "body": b"",
                "more_body": False,
            }
        )
        send = AsyncMock()

        await app(
            {
                "type": "http",
                "method": "GET",
                "scheme": "http",
                "path": "/",
            },
            receive,
            send,
        )

        send.assert_has_awaits(
            [
                call(
                    {
                        "type": "http.response.start",
                        "status": 405,
                        "headers": [
                            (b"content-length", b"18"),
                            (b"content-type", b"text/plain; charset=utf-8"),
                        ],
                    }
                ),
                call(
                    {
                        "type": "http.response.body",
                        "body": b"Method Not Allowed",
                        "more_body": False,
                    }
                ),
            ]
        )


@mark.asyncio
class TestWebSocketRequest:
    @fixture
    def app(self):
        return Xiao([WebSocketRoute("/")])

    async def test_websocket_request(self, app):
        scope = {
            "type": "websocket",
            "scheme": "ws",
            "path": "/",
        }
        send = AsyncMock()

        await app(
            scope,
            AsyncMock(
                return_value={
                    "type": "websocket.connect",
                }
            ),
            send,
        )

        await app(
            scope,
            AsyncMock(
                return_value={
                    "type": "websocket.receive",
                    "text": b"",
                    "bytes": None,
                }
            ),
            send,
        )

        await app(
            scope,
            AsyncMock(
                return_value={"type": "websocket.disconnect", "code": 1005}
            ),
            send,
        )

        send.assert_has_awaits(
            [
                call(
                    {
                        "type": "websocket.accept",
                        "subprotocol": None,
                        "headers": [],
                    }
                )
            ]
        )
