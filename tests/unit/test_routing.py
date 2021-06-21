from inspect import iscoroutinefunction
from unittest.mock import AsyncMock, Mock, call, patch

from pytest import fixture, mark

from xiao_asgi.requests import Request
from xiao_asgi.routing import Route, Router


class TestRoute:
    def test_create_with_defaults(self):
        path = "/test"
        endpoint = Mock()

        route = Route(path, endpoint)

        assert route.path == path
        assert iscoroutinefunction(route.endpoint)
        assert route.methods == ["GET"]

    def test_create_without_defaults(self):
        path = "/test"
        endpoint = Mock()
        methods = ["GET", "POST"]

        route = Route(path, endpoint, methods)

        assert route.path == path
        assert iscoroutinefunction(route.endpoint)
        assert route.methods == methods

    @patch("xiao_asgi.routing.Request", spec=Request)
    @patch("xiao_asgi.routing.is_coroutine")
    @mark.asyncio
    async def test_construct_endpoint_with_async_function(
        self, mock_is_coroutine, mock_request
    ):
        mock_is_coroutine.return_value = True
        func = AsyncMock()
        receive = AsyncMock()
        send = AsyncMock()
        scope = {}

        constructed_endpoint = Route._construct(func)
        await constructed_endpoint(scope, receive, send)

        mock_request.assert_called_once_with(scope, receive=receive, send=send)
        func.assert_awaited_once_with(mock_request.return_value)
        func.return_value.assert_awaited_once_with(send)

    @patch("xiao_asgi.routing.to_thread")
    @patch("xiao_asgi.routing.Request", spec=Request)
    @patch("xiao_asgi.routing.is_coroutine")
    @mark.asyncio
    async def test_construct_endpoint_with_sync_function(
        self, mock_is_coroutine, mock_request, mock_to_thread
    ):
        mock_is_coroutine.return_value = False
        func = AsyncMock()
        receive = AsyncMock()
        send = AsyncMock()
        scope = {}

        constructed_endpoint = Route._construct(func)
        await constructed_endpoint(scope, receive, send)

        mock_request.assert_called_once_with(scope, receive=receive, send=send)
        mock_to_thread.assert_awaited_once_with(
            func, mock_request.return_value
        )
        mock_to_thread.return_value.assert_awaited_once_with(send)

    @patch("xiao_asgi.routing.Route._construct", return_value=AsyncMock())
    @mark.asyncio
    async def test_handle_request_with_valid_method(self, mock_construct):
        mock_receive = AsyncMock()
        mock_send = AsyncMock()
        scope = {"method": "GET"}

        route = Route("/test", Mock())
        await route.handle(scope, mock_receive, mock_send)

        mock_construct.return_value.assert_awaited_once_with(
            scope, mock_receive, mock_send
        )

    @patch("xiao_asgi.routing.Route._construct")
    @mark.asyncio
    async def test_handle_request_with_invalid_method(self, mock_construct):
        mock_endpoint = AsyncMock()
        mock_construct.return_value = mock_endpoint
        mock_send = AsyncMock()
        scope = {"method": "POST"}

        route = Route("/test", Mock())
        await route.handle(scope, AsyncMock(), mock_send)

        mock_endpoint.assert_not_awaited()
        mock_send.assert_has_awaits = [
            call(
                {
                    "type": "http.response.start",
                    "status": 405,
                    "headers": [
                        (b"content-length", b""),
                        (b"content-type", b"text/plain; charset: utf-8"),
                    ],
                }
            ),
            call({"type": "http.response.body", "body": "Method not allowed"}),
        ]


class TestRouter:
    @fixture
    def routes(self):
        return [
            Route("/", AsyncMock()),
            Route("/test", AsyncMock(), ["GET", "POST"]),
        ]

    def test_create(self, routes):
        router = Router(routes)
        assert router.routes == routes

    @patch("xiao_asgi.routing.PlainTextResponse", return_value=AsyncMock())
    @mark.asyncio
    async def test_unknown_type(self, mock_response, routes):
        mock_send = AsyncMock()
        scope = {"type": "websocket"}

        router = Router(routes)
        await router(scope, AsyncMock(), mock_send)

        mock_response.assert_called_once_with("Not Found", status_code=404)
        mock_response.return_value.assert_awaited_once_with(mock_send)

    @patch("xiao_asgi.routing.PlainTextResponse", return_value=AsyncMock())
    @mark.asyncio
    async def test_unknown_route(self, mock_response, routes):
        mock_send = AsyncMock()
        scope = {"type": "http", "path": "/unknown"}

        router = Router(routes)
        await router(scope, AsyncMock(), mock_send)

        mock_response.assert_called_once_with("Not Found", status_code=404)
        mock_response.return_value.assert_awaited_once_with(mock_send)

    @patch("xiao_asgi.routing.PlainTextResponse", return_value=AsyncMock())
    @mark.asyncio
    async def test_known_route(self, mock_response, routes):
        route = Route("/known", AsyncMock())
        route.handle = AsyncMock()
        routes.append(route)
        mock_receive = AsyncMock()
        mock_send = AsyncMock()
        scope = {"type": "http", "path": "/known"}

        router = Router(routes)
        await router(scope, mock_receive, mock_send)

        mock_response.assert_not_called()
        route.handle.assert_awaited_once_with(scope, mock_receive, mock_send)
