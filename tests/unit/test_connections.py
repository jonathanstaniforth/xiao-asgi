from unittest.mock import AsyncMock, call

from pytest import fixture, mark, raises

from xiao_asgi.connections import (
    Connection,
    HttpConnection,
    InvalidConnectionState,
    ProtocolUnknown,
    WebSocketConnection,
    make_connection,
)
from xiao_asgi.requests import Request
from xiao_asgi.responses import PlainTextResponse


@fixture
def headers():
    return [
        (b"content-type", b"text/plain"),
        (b"user-agent", b"PostmanRuntime/7.26.8"),
        (b"accept", b"*/*"),
        (b"host", b"localhost:8000"),
        (b"accept-encoding", b"gzip, deflate, br"),
        (b"connection", b"keep-alive"),
        (b"content-length", b"5"),
    ]


@mark.asyncio
class TestConnection:
    class MockConnection(Connection):
        protocol = "test"

        async def receive_request(self) -> None:
            pass

        async def send_response(self) -> None:
            pass

    def test_create_instance(self):
        scope = {"type": "test"}
        receive = AsyncMock()
        send = AsyncMock()

        connection = self.MockConnection(scope, receive, send)

        assert connection.path_parameters is None
        assert connection.scope is scope
        assert connection._receive is receive
        assert connection._send is send

    def test_create_instance_with_different_protocol(self):
        with raises(
            ValueError,
            match="The type of the connection must be test, not http.",
        ):
            self.MockConnection({"type": "http"}, AsyncMock(), AsyncMock())

    def test_empty_headers(self):
        scope = {"type": "test", "headers": []}

        connection = self.MockConnection(scope, AsyncMock(), AsyncMock())

        assert connection.headers == {}

    def test_full_headers(self, headers):
        scope = {"type": "test", "headers": headers}

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
            "type": "test",
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


@mark.asyncio
class TestHttpConnection:
    @fixture
    def http_connection(self):
        return HttpConnection({"type": "http"}, AsyncMock(), AsyncMock())

    @fixture
    def temporary_file(self, tmp_path):
        file = tmp_path / "test.txt"
        file.touch()
        return file

    def test_create_instance(self):
        scope = {"type": "http"}
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
            {"type": "http", "method": method}, AsyncMock(), AsyncMock()
        )

        assert http_connection.method == method

    async def test_receive_request_with_required_type(self):
        request = {"type": "http.request", "body": b"", "more_body": False}
        receive = AsyncMock(return_value=request)

        http_connection = HttpConnection(
            {"type": "http"}, receive, AsyncMock()
        )
        received_request = await http_connection.receive_request()

        assert isinstance(received_request, Request)
        assert received_request.protocol == "http"
        assert received_request.type == "request"
        assert received_request.data == {"body": b"", "more_body": False}
        receive.assert_awaited_once()

    async def test_send_response(self):
        send = AsyncMock()
        response = PlainTextResponse()

        http_connection = HttpConnection({"type": "http"}, AsyncMock(), send)
        await http_connection.send_response(response)

        send.assert_has_awaits(
            [
                call(
                    {
                        "type": "http.response.start",
                        "status": 200,
                        "headers": [
                            (b"content-length", b"0"),
                            (b"content-type", b"text/plain; charset=utf-8"),
                        ],
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

    async def test_sending_start_response_with_defaults(self, http_connection):
        await http_connection.send_start()

        http_connection._send.assert_awaited_once_with(
            {"type": "http.response.start", "status": 200, "headers": []}
        )

    @mark.parametrize(
        "status,headers",
        [
            (
                200,
                [
                    (b"content-type", b"text/plain"),
                    (b"user-agent", b"PostmanRuntime/7.26.8"),
                    (b"accept", b"*/*"),
                    (b"host", b"localhost:8000"),
                    (b"accept-encoding", b"gzip, deflate, br"),
                    (b"connection", b"keep-alive"),
                    (b"content-length", b"5"),
                ],
            ),
            (
                401,
                (
                    [b"content-type", b"text/plain"],
                    [b"user-agent", b"PostmanRuntime/7.26.8"],
                    [b"accept", b"*/*"],
                    [b"host", b"localhost:8000"],
                    [b"accept-encoding", b"gzip, deflate, br"],
                    [b"connection", b"keep-alive"],
                    [b"content-length", b"5"],
                ),
            ),
            (
                403,
                {
                    (b"content-type", b"text/plain"),
                    (b"user-agent", b"PostmanRuntime/7.26.8"),
                    (b"accept", b"*/*"),
                    (b"host", b"localhost:8000"),
                    (b"accept-encoding", b"gzip, deflate, br"),
                    (b"connection", b"keep-alive"),
                    (b"content-length", b"5"),
                },
            ),
            (404, []),
        ],
    )
    async def test_sending_start_response(
        self, http_connection, status, headers
    ):
        await http_connection.send_start(status, headers)

        http_connection._send.assert_awaited_once_with(
            {
                "type": "http.response.start",
                "status": status,
                "headers": headers,
            }
        )

    async def test_sending_body_response_with_defaults(self, http_connection):
        await http_connection.send_body()

        http_connection._send.assert_awaited_once_with(
            {"type": "http.response.body", "body": b"", "more_body": False}
        )

    @mark.parametrize(
        "body,more_body",
        [
            (b"", False),
            (b"", True),
            (b"Hello, World!", False),
            (b"Hello, World!", True),
        ],
    )
    async def test_sending_body_response(
        self, http_connection, body, more_body
    ):
        await http_connection.send_body(body, more_body)

        http_connection._send.assert_awaited_once_with(
            {
                "type": "http.response.body",
                "body": body,
                "more_body": more_body,
            }
        )

    async def test_sending_push_response(self, http_connection):
        await http_connection.send_push("test/path")

        http_connection._send.assert_awaited_once_with(
            {"type": "http.response.push", "path": "test/path", "headers": []}
        )

    async def test_sending_push_response_with_headers(
        self, http_connection, headers
    ):
        await http_connection.send_push("test/path", headers=headers)

        http_connection._send.assert_awaited_once_with(
            {
                "type": "http.response.push",
                "path": "test/path",
                "headers": headers,
            }
        )

    async def test_sending_zero_copy(self, http_connection, temporary_file):
        with open(temporary_file) as test_file:
            await http_connection.send_zero_copy(test_file)

            http_connection._send.assert_awaited_once_with(
                {
                    "type": "http.response.zerocopysend",
                    "file": test_file,
                    "more_body": False,
                }
            )

    async def test_sending_zero_copy_with_offset(
        self, http_connection, temporary_file
    ):
        with open(temporary_file) as test_file:
            await http_connection.send_zero_copy(test_file, offset=1)

            http_connection._send.assert_awaited_once_with(
                {
                    "type": "http.response.zerocopysend",
                    "file": test_file,
                    "offset": 1,
                    "more_body": False,
                }
            )

    async def test_sending_zero_copy_with_count(
        self, http_connection, temporary_file
    ):
        with open(temporary_file) as test_file:
            await http_connection.send_zero_copy(test_file, count=1)

            http_connection._send.assert_awaited_once_with(
                {
                    "type": "http.response.zerocopysend",
                    "file": test_file,
                    "count": 1,
                    "more_body": False,
                }
            )

    async def test_sending_zero_copy_with_more_body(
        self, http_connection, temporary_file
    ):
        with open(temporary_file) as test_file:
            await http_connection.send_zero_copy(test_file, more_body=True)

            http_connection._send.assert_awaited_once_with(
                {
                    "type": "http.response.zerocopysend",
                    "file": test_file,
                    "more_body": True,
                }
            )


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

        assert isinstance(websocket_connection, HttpConnection)
        assert websocket_connection.protocol == "websocket"
        assert websocket_connection.scope is scope
        assert websocket_connection._receive is receive
        assert websocket_connection._send is send
        assert websocket_connection.connection_state == "connecting"

    def test_method(self, websocket_connection):
        assert websocket_connection.method is None

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

    async def test_send_start(self, websocket_connection):
        await websocket_connection.send_start()

        assert websocket_connection.protocol == "websocket.http"
        websocket_connection._send.assert_awaited_once_with(
            {
                "type": "websocket.http.response.start",
                "headers": [],
                "status": 200,
            }
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
