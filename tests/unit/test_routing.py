from unittest.mock import AsyncMock, Mock, call

from pytest import fixture, mark, raises

from xiao_asgi.connections import (
    HttpConnection,
    ProtocolMismatch,
    WebSocketConnection,
)
from xiao_asgi.requests import Request
from xiao_asgi.routing import HttpRoute, Route, WebSocketRoute


@fixture
def http_connection():
    return HttpConnection({}, AsyncMock(), AsyncMock())


@fixture
def websocket_connection():
    return WebSocketConnection({}, AsyncMock(), AsyncMock())


@mark.asyncio
class TestRoute:
    @fixture
    def route(self):
        return Route("/test")

    def test_create_instance(self):
        route = Route("/test")

        assert isinstance(route, Route)
        assert route.path == "/test"

    async def test_get_endpoint_with_valid_endpoint(self, route):
        get_endpoint = Mock()
        route.get = get_endpoint

        assert await route.get_endpoint("get") is get_endpoint

    async def test_get_endpoint_with_invalid_endpoint(self, route):
        with raises(AttributeError):
            await route.get_endpoint("get")

    async def test_call_route_with_matching_protocol(
        self, route, http_connection
    ):
        route.protocol = "http"

        await route(http_connection)

    async def test_call_route_with_mismatched_protocol(
        self, route, http_connection
    ):
        route.protocol = "websocket"

        with raises(ProtocolMismatch):
            await route(http_connection)


@mark.asyncio
class TestHttpRoute:
    @fixture
    def http_route(self):
        return HttpRoute("/test")

    @fixture
    def http_request(self):
        return Request(data={}, protocol="http", type="request")

    @mark.parametrize(
        "method",
        [
            "get",
            "head",
            "post",
            "put",
            "delete",
            "connect",
            "options",
            "trace",
            "patch",
        ],
    )
    async def test_endpoints_send_method_not_allowed(
        self, method, http_route, http_connection, http_request
    ):
        http_route.send_method_not_allowed = AsyncMock()

        endpoint = getattr(http_route, method)
        await endpoint(http_connection, http_request)

        http_route.send_method_not_allowed.assert_awaited_once_with(
            http_connection
        )

    async def test_send_interval_server_error(
        self, http_route, http_connection
    ):
        await http_route.send_internal_server_error(http_connection)

        http_connection._send.assert_has_awaits(
            [
                call(
                    {
                        "type": "http.response.start",
                        "status": 500,
                        "headers": [],
                    }
                ),
                call(
                    {
                        "type": "http.response.body",
                        "body": b"Internal Server Error",
                        "more_body": False,
                    }
                ),
            ]
        )

    async def test_send_not_implemented(self, http_route, http_connection):
        await http_route.send_not_implemented(http_connection)

        http_connection._send.assert_has_awaits(
            [
                call(
                    {
                        "type": "http.response.start",
                        "status": 501,
                        "headers": [],
                    }
                ),
                call(
                    {
                        "type": "http.response.body",
                        "body": b"Not Implemented",
                        "more_body": False,
                    }
                ),
            ]
        )

    async def test_send_method_not_allowed(self, http_route, http_connection):
        await http_route.send_method_not_allowed(http_connection)

        http_connection._send.assert_has_awaits(
            [
                call(
                    {
                        "type": "http.response.start",
                        "status": 405,
                        "headers": [],
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

    async def test_call_with_mismatched_protocol(
        self, http_route, websocket_connection
    ):
        with raises(ProtocolMismatch):
            await http_route(websocket_connection)

    async def test_call_with_missing_endpoint(
        self, http_route, http_connection
    ):
        http_connection.scope["method"] = "invalid"

        with raises(AttributeError):
            await http_route(http_connection)

        http_connection._send.assert_has_awaits(
            [
                call(
                    {
                        "type": "http.response.start",
                        "status": 501,
                        "headers": [],
                    }
                ),
                call(
                    {
                        "type": "http.response.body",
                        "body": b"Not Implemented",
                        "more_body": False,
                    }
                ),
            ]
        )

    async def test_call_with_endpoint_error(self, http_route, http_connection):
        http_connection.scope["method"] = "get"
        http_route.get = AsyncMock(side_effect=Exception)

        with raises(Exception):
            await http_route(http_connection)

        http_connection._send.assert_has_awaits(
            [
                call(
                    {
                        "type": "http.response.start",
                        "status": 500,
                        "headers": [],
                    }
                ),
                call(
                    {
                        "type": "http.response.body",
                        "body": b"Internal Server Error",
                        "more_body": False,
                    }
                ),
            ]
        )

    async def test_call_with_no_error(
        self, http_route, http_connection, http_request
    ):
        http_connection.receive_request = AsyncMock(return_value=http_request)
        http_connection.scope["method"] = "get"
        http_route.get = AsyncMock()

        await http_route(http_connection)

        http_route.get.assert_awaited_once_with(http_connection, http_request)


@mark.asyncio
class TestWebSocketRoute:
    @fixture
    def websocket_route(self):
        return WebSocketRoute("/test")

    @fixture
    def websocket_request(self):
        return Request(data={}, protocol="websocket", type="receive")

    async def test_connect(
        self, websocket_route, websocket_connection, websocket_request
    ):
        await websocket_route.connect(websocket_connection, websocket_request)

        websocket_connection._send.assert_awaited_once_with(
            {"type": "websocket.accept", "subprotocol": None, "headers": []}
        )

    async def test_receive(
        self, websocket_route, websocket_connection, websocket_request
    ):
        await websocket_route.receive(websocket_connection, websocket_request)

    async def test_disconnect(
        self, websocket_route, websocket_connection, websocket_request
    ):
        await websocket_route.disconnect(
            websocket_connection, websocket_request
        )

    async def test_call_with_missing_endpoint(
        self, websocket_route, websocket_connection, websocket_request
    ):
        websocket_request.type = "invalid"
        websocket_connection.receive_request = AsyncMock(
            return_value=websocket_request
        )

        with raises(AttributeError):
            await websocket_route(websocket_connection)

        websocket_connection._send.assert_awaited_once_with(
            {"type": "websocket.close", "code": 1011}
        )

    async def test_call_with_endpoint_error(
        self, websocket_route, websocket_connection, websocket_request
    ):
        websocket_connection.receive = AsyncMock(
            return_value=websocket_request
        )

        with raises(Exception):
            await websocket_route(websocket_connection)

        websocket_connection._send.assert_awaited_once_with(
            {"type": "websocket.close", "code": 1011}
        )

    async def test_call_with_no_error(
        self, websocket_route, websocket_connection, websocket_request
    ):
        websocket_connection.receive_request = AsyncMock(
            return_value=websocket_request
        )
        websocket_route.receive = AsyncMock()

        await websocket_route(websocket_connection)

        websocket_route.receive.assert_awaited_once_with(
            websocket_connection, websocket_request
        )
