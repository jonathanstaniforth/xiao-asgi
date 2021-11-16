from unittest.mock import AsyncMock, Mock, call

from pytest import mark, raises, fixture

from xiao_asgi.connections import (
    Connection,
    HttpConnection,
    InvalidConnectionState,
    ProtocolMismatch,
    ProtocolUnknown,
    TypeMismatch,
    WebSocketConnection,
    make_connection,
)
from xiao_asgi.requests import Request
from xiao_asgi.responses import BodyResponse


@mark.asyncio
class TestConnection:
    class MockConnection(Connection):
        protocol = "test"

        async def receive_request(self) -> None:
            pass

        async def send_response(self) -> None:
            pass

    def test_create_instance(self):
        scope = Mock()
        receive = AsyncMock()
        send = AsyncMock()

        connection = self.MockConnection(scope, receive, send)

        assert connection.scope is scope
        assert connection._receive is receive
        assert connection._send is send

    def test_empty_headers(self):
        scope = {"headers": []}

        connection = self.MockConnection(scope, AsyncMock(), AsyncMock())

        assert connection.headers == {}

    def test_full_headers(self):
        scope = {
            "headers": [
                (b"content-type", b"text/plain"),
                (b"user-agent", b"PostmanRuntime/7.26.8"),
                (b"accept", b"*/*"),
                (b"host", b"localhost:8000"),
                (b"accept-encoding", b"gzip, deflate, br"),
                (b"connection", b"keep-alive"),
                (b"content-length", b"5"),
            ]
        }

        connection = self.MockConnection(scope, AsyncMock(), AsyncMock())

        assert connection.headers == {
            "content-type": "text/plain",
            "user-agent": "PostmanRuntime/7.26.8",
            "accept": "*/*",
            "host": "localhost:8000",
            "accept-encoding": "gzip, deflate, br",
            "connection": "keep-alive",
            "content-length": "5",
        }

    def test_url(self):
        scope = {
            "scheme": "http",
            "server": ("127.0.0.1", 8000),
            "root_path": "",
            "path": "/",
            "query_string": b"chips=ahoy&vienna=finger",
        }

        connection = self.MockConnection(scope, AsyncMock(), AsyncMock())

        assert connection.url == {
            "scheme": "http",
            "server": ("127.0.0.1", 8000),
            "root_path": "",
            "path": "/",
            "query_string": b"chips=ahoy&vienna=finger",
        }

    async def test_receive_with_same_protocol(self):
        request = {"type": "test.request", "body": b"", "more_body": False}
        receive = AsyncMock(return_value=request)

        connection = self.MockConnection({}, receive, AsyncMock())

        assert await connection.receive() == request
        receive.assert_called_once()

    async def test_receive_with_different_protocol(self):
        receive = AsyncMock(
            return_value={
                "type": "invalid.request",
                "body": b"",
                "more_body": False,
            }
        )

        connection = self.MockConnection({}, receive, AsyncMock())

        with raises(
            ProtocolMismatch,
            match="Received request protocol \\(invalid\\) does not match this connection protocol \\(test\\).",
        ):
            await connection.receive()

        receive.assert_awaited_once()

    async def test_send_with_same_protocol(self):
        response = {
            "type": "test.response.start",
            "status": 200,
            "headers": [],
        }
        send = AsyncMock()

        connection = self.MockConnection({}, AsyncMock(), send)
        await connection.send(response)

        send.assert_awaited_once_with(response)

    async def test_send_with_different_protocol(self):
        response = {
            "type": "invalid.response.start",
            "status": 200,
            "headers": [],
        }
        send = AsyncMock()

        connection = self.MockConnection({}, AsyncMock(), send)

        with raises(
            ProtocolMismatch,
            match="Response protocol \\(invalid\\) does not match this connection protocol \\(test\\).",
        ):
            await connection.send(response)

        send.assert_not_awaited()


@mark.asyncio
class TestHttpConnection:
    def test_creating_instance(self):
        scope = Mock()
        receive = AsyncMock()
        send = AsyncMock()

        http_connection = HttpConnection(scope, receive, send)

        assert isinstance(http_connection, Connection)
        assert http_connection.protocol == "http"
        assert http_connection.scope is scope
        assert http_connection._receive is receive
        assert http_connection._send is send

    @mark.parametrize(
        "method",
        [
            "GET",
            "HEAD",
            "POST",
            "PUT",
            "PATCH",
            "DELETE",
            "CONNECT",
            "OPTIONS",
            "TRACE",
        ],
    )
    def test_method(self, method):
        http_connection = HttpConnection(
            {"method": method}, AsyncMock(), AsyncMock()
        )

        assert http_connection.method == method

    async def test_get_requests_body(self):
        request_1 = {
            "type": "http.request",
            "body": b"Hello ",
            "more_body": True,
        }
        request_2 = {
            "type": "http.request",
            "body": b"World!",
            "more_body": False,
        }
        receive = AsyncMock(side_effect=[request_1, request_2])

        http_connection = HttpConnection({}, receive, AsyncMock())
        received_request = await http_connection.get_requests_body()

        assert received_request == Request(
            protocol="http",
            type="request",
            data={"body": b"Hello World!", "more_body": False},
        )
        receive.assert_has_awaits == [call(), call()]

    async def test_receive_request_with_required_type(self):
        request = {"type": "http.request", "body": b"", "more_body": False}
        receive = AsyncMock(return_value=request)

        http_connection = HttpConnection({}, receive, AsyncMock())
        received_request = await http_connection.receive_request()

        assert isinstance(received_request, Request)
        assert received_request.protocol == "http"
        assert received_request.type == "request"
        assert received_request.data == {"body": b"", "more_body": False}
        receive.assert_awaited_once()

    async def test_receive_request_without_required_type(self):
        request = {"type": "http.invalid", "body": b"", "more_body": False}
        receive = AsyncMock(return_value=request)

        http_connection = HttpConnection({}, receive, AsyncMock())

        with raises(
            TypeMismatch,
            match="Request type \\(invalid\\) does not match the expected type \\(request\\).",
        ):
            await http_connection.receive_request()

    async def test_send_response(self):
        send = AsyncMock()
        response = BodyResponse()

        http_connection = HttpConnection({}, AsyncMock(), send)
        await http_connection.send_response(response)

        send.assert_has_awaits(
            [
                call(
                    {
                        "type": "http.response.start",
                        "status": 200,
                        "headers": [],
                    }
                ),
                call(
                    {
                        "type": "http.response.body",
                        "body": b"",
                        "more_body": False,
                    }
                ),
            ]
        )

    async def test_stream_requests(self):
        request_1 = {
            "type": "http.request",
            "body": b"First request",
            "more_body": True,
        }
        request_2 = {
            "type": "http.request",
            "body": b"Second request",
            "more_body": False,
        }
        receive = AsyncMock(side_effect=[request_1, request_2])

        http_connection = HttpConnection({}, receive, AsyncMock())

        received_requests = []

        async for received_request in http_connection.stream_requests():
            received_requests.append(received_request)

        assert received_requests[0] == Request(
            protocol="http",
            type="request",
            data={"body": b"First request", "more_body": True},
        )
        assert received_requests[1] == Request(
            protocol="http",
            type="request",
            data={"body": b"Second request", "more_body": False},
        )
        receive.assert_has_awaits == [call(), call()]


@mark.asyncio
class TestWebSocketConnection:
    @fixture
    def websocket_connection(self):
        return WebSocketConnection(
            {"type": "websocket"}, AsyncMock(), AsyncMock()
        )

    def test_create_instance(self):
        scope = {"type": "websocket"}
        receive = AsyncMock()
        send = AsyncMock()

        websocket_connection = WebSocketConnection(scope, receive, send)

        assert isinstance(websocket_connection, Connection)
        assert websocket_connection.protocol == "websocket"
        assert websocket_connection.scope is scope
        assert websocket_connection._receive is receive
        assert websocket_connection._send is send
        assert websocket_connection.connection_state == "connecting"

    async def test_accept_connection(self, websocket_connection):
        await websocket_connection.accept_connection()

        websocket_connection._send.assert_awaited_once_with(
            {"type": "websocket.accept", "subprotocol": None, "headers": []}
        )

    async def test_accept_connection_with_subprotocol(
        self, websocket_connection
    ):
        await websocket_connection.accept_connection(
            subprotocol="test-subprotocol"
        )

        websocket_connection._send.assert_awaited_once_with(
            {
                "type": "websocket.accept",
                "subprotocol": "test-subprotocol",
                "headers": [],
            }
        )

    @mark.parametrize(
        "headers",
        [
            [
                (b"content-type", b"text/plain"),
                (b"user-agent", b"PostmanRuntime/7.26.8"),
                (b"accept", b"*/*"),
                (b"host", b"localhost:8000"),
                (b"accept-encoding", b"gzip, deflate, br"),
                (b"connection", b"keep-alive"),
                (b"content-length", b"5"),
            ],
            (
                [b"content-type", b"text/plain"],
                [b"user-agent", b"PostmanRuntime/7.26.8"],
                [b"accept", b"*/*"],
                [b"host", b"localhost:8000"],
                [b"accept-encoding", b"gzip, deflate, br"],
                [b"connection", b"keep-alive"],
                [b"content-length", b"5"],
            ),
            {
                (b"content-type", b"text/plain"),
                (b"user-agent", b"PostmanRuntime/7.26.8"),
                (b"accept", b"*/*"),
                (b"host", b"localhost:8000"),
                (b"accept-encoding", b"gzip, deflate, br"),
                (b"connection", b"keep-alive"),
                (b"content-length", b"5"),
            },
            [],
        ],
    )
    async def test_accept_connection_with_headers(
        self, websocket_connection, headers
    ):
        await websocket_connection.accept_connection(headers=headers)

        websocket_connection._send.assert_awaited_once_with(
            {
                "type": "websocket.accept",
                "subprotocol": None,
                "headers": headers,
            }
        )

    async def test_close_connection(self, websocket_connection):
        await websocket_connection.close_connection()

        websocket_connection._send.assert_awaited_once_with(
            {"type": "websocket.close", "code": 1000}
        )

    async def test_close_connection_with_code(self, websocket_connection):
        await websocket_connection.close_connection(code=1011)

        websocket_connection._send.assert_awaited_once_with(
            {"type": "websocket.close", "code": 1011}
        )

    async def test_receive_request_with_connect_message_type(
        self, websocket_connection
    ):
        websocket_connection._receive.return_value = {
            "type": "websocket.connect"
        }

        received_request = await websocket_connection.receive_request()

        assert websocket_connection.connection_state == "connected"
        assert isinstance(received_request, Request)
        assert received_request.protocol == "websocket"
        assert received_request.type == "connect"
        assert received_request.data == {}

    async def test_receive_request_with_receive_message_type(
        self, websocket_connection
    ):
        websocket_connection.connection_state = "connected"
        websocket_connection._receive.return_value = {
            "type": "websocket.receive",
            "text": "Hello World!",
        }

        received_request = await websocket_connection.receive_request()

        assert websocket_connection.connection_state == "connected"
        assert isinstance(received_request, Request)
        assert received_request.protocol == "websocket"
        assert received_request.type == "receive"
        assert received_request.data == {"text": "Hello World!"}

    async def test_receive_request_with_disconnect_message_type(
        self, websocket_connection
    ):
        websocket_connection.connection_state = "connected"
        websocket_connection._receive.return_value = {
            "type": "websocket.disconnect"
        }

        received_request = await websocket_connection.receive_request()

        assert websocket_connection.connection_state == "disconnected"
        assert isinstance(received_request, Request)
        assert received_request.protocol == "websocket"
        assert received_request.type == "disconnect"
        assert received_request.data == {}

    async def test_receive_request_with_disconnected_connection(
        self, websocket_connection
    ):
        websocket_connection.connection_state = "disconnected"

        with raises(
            InvalidConnectionState,
            match="Cannot receive a request from a disconnected connection.",
        ):
            await websocket_connection.receive_request()

    async def test_send_bytes(self, websocket_connection):
        await websocket_connection.send_bytes(b"Hello, World!")

        websocket_connection._send.assert_awaited_once_with(
            {"type": "websocket.send", "bytes": b"Hello, World!"}
        )

    async def test_send_text(self, websocket_connection):
        await websocket_connection.send_text("Hello, World!")

        websocket_connection._send.assert_awaited_once_with(
            {"type": "websocket.send", "text": "Hello, World!"}
        )


class TestMakeConnection:
    @mark.parametrize(
        "protocol,connection_class",
        [("http", HttpConnection), ("websocket", WebSocketConnection)],
    )
    def test_create_connection(self, protocol, connection_class):
        receive = AsyncMock()
        send = AsyncMock()

        connection = make_connection({"type": protocol}, receive, send)

        assert isinstance(connection, connection_class)
        assert connection.scope == {"type": protocol}
        assert connection._receive is receive
        assert connection._send is send

    def test_unknown_protocol(self):
        with raises(ProtocolUnknown):
            make_connection({"type": "unknown"}, AsyncMock(), AsyncMock())
