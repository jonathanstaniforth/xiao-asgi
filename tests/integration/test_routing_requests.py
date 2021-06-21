from unittest.mock import AsyncMock, call

from pytest import fixture, mark

from xiao_asgi.responses import PlainTextResponse
from xiao_asgi.routing import Route, Router


@mark.asyncio
class TestRouting:
    @fixture
    def routes(self):
        async def endpoint(request):
            return PlainTextResponse("Hello World!")

        return [
            Route("/", endpoint),
            Route("/create", endpoint, methods=["POST"]),
            Route("/update", endpoint, methods=["PUT"]),
        ]

    @fixture
    def scope(self):
        return {
            "type": "http",
            "asgi": {"version": "3.0", "spec_version": "2.1"},
            "http_version": "1.1",
            "server": ("127.0.0.1", 8000),
            "client": ("127.0.0.1", 62412),
            "scheme": "http",
            "method": "GET",
            "root_path": "",
            "path": "/",
            "raw_path": b"/",
            "query_string": b"",
            "headers": [
                (b"content-type", b"text/plain"),
                (b"user-agent", b"PostmanRuntime/7.26.8"),
                (b"accept", b"*/*"),
                (b"postman-token", b"9f00cb32-d59b-4586-bd94-ad6d7f804996"),
                (b"host", b"localhost:8000"),
                (b"accept-encoding", b"gzip, deflate, br"),
                (b"connection", b"keep-alive"),
                (b"content-length", b"5"),
            ],
        }

    async def test_unknown_type(self, scope, routes):
        scope["type"] = "websocket"
        scope["scheme"] = "ws"
        scope["path"] = "/ws"
        scope["raw_path"] = b"/ws"

        mock_send = AsyncMock()

        router = Router(routes)
        await router(scope, AsyncMock(), mock_send)

        mock_send.assert_has_awaits(
            [
                call(
                    {
                        "type": "http.response.start",
                        "status": 404,
                        "headers": [
                            (b"content-length", b"9"),
                            (b"content-type", b"text/plain; charset=utf-8"),
                        ],
                    }
                ),
                call({"type": "http.response.body", "body": b"Not Found"}),
            ]
        )

    async def test_unknown_route(self, scope, routes):
        scope["path"] = "/unknown"
        scope["raw_path"] = b"/unknown"

        mock_send = AsyncMock()

        router = Router(routes)
        await router(scope, AsyncMock(), mock_send)

        mock_send.assert_has_awaits(
            [
                call(
                    {
                        "type": "http.response.start",
                        "status": 404,
                        "headers": [
                            (b"content-length", b"9"),
                            (b"content-type", b"text/plain; charset=utf-8"),
                        ],
                    }
                ),
                call({"type": "http.response.body", "body": b"Not Found"}),
            ]
        )

    async def test_known_route(self, scope, routes):
        mock_send = AsyncMock()

        router = Router(routes)
        await router(scope, AsyncMock(), mock_send)

        mock_send.assert_has_awaits(
            [
                call(
                    {
                        "type": "http.response.start",
                        "status": 200,
                        "headers": [
                            (b"content-length", b"12"),
                            (b"content-type", b"text/plain; charset=utf-8"),
                        ],
                    }
                ),
                call({"type": "http.response.body", "body": b"Hello World!"}),
            ]
        )
