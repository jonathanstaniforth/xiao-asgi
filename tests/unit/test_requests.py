from json import loads
from unittest.mock import AsyncMock
from urllib.parse import parse_qs

from pytest import fixture, mark, raises

from xiao_asgi.requests import BodyStreamError, Request


@fixture
def scope():
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
        "query_string": b"chips=ahoy&vienna=finger",
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


@fixture
def receive_event():
    return AsyncMock(
        return_value={"type": "http.request", "body": b"", "more_body": False}
    )


@fixture
def send_event():
    return AsyncMock()


class TestRequest:
    def test_create_new_request(self, scope, receive_event, send_event):
        """Test creating a new `Request` instance."""
        request = Request(scope, receive_event, send_event)
        assert isinstance(request, Request)

    def test_get_client(self, scope, receive_event, send_event):
        """Test retrieving request client."""
        request = Request(scope, receive_event, send_event)
        assert request.client == scope["client"]

    def test_get_no_client(self, scope, receive_event, send_event):
        """Test retrieving non-existent request client."""
        del scope["client"]
        request = Request(scope, receive_event, send_event)
        assert request.client == (None, None)

    def test_get_cookies(self, scope, receive_event, send_event):
        """Test retrieving request cookies."""
        scope["headers"].append((b"cookie", b"chips=ahoy; vienna=finger"))
        request = Request(scope, receive_event, send_event)
        cookies = request.cookies

        assert cookies["chips"].value == "ahoy"
        assert cookies["vienna"].value == "finger"

    def test_get_headers(self, scope, receive_event, send_event):
        """Test retrieving request headers."""
        request = Request(scope, receive_event, send_event)
        assert request.headers == {
            key.decode("latin-1"): value.decode("latin-1")
            for key, value in scope["headers"]
        }

    def test_get_no_headers(self, scope, receive_event, send_event):
        """Test retrieving non-existent request headers."""
        del scope["headers"]
        request = Request(scope, receive_event, send_event)
        assert request.headers == {}

    @mark.parametrize(
        "method", ["GET", "HEAD", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"]
    )
    def test_get_method(self, method, scope, receive_event, send_event):
        """Test retrieving request method."""
        scope["method"] = method
        request = Request(scope, receive_event, send_event)
        assert request.method == method

    def test_get_no_method(self, scope, receive_event, send_event):
        """Test retrieving non-existent request method."""
        del scope["method"]
        request = Request(scope, receive_event, send_event)
        assert request.method is None

    @mark.parametrize(
        "query_string", [b"", b"chips=ahoy", b"chips=ahoy&vienna=finger"]
    )
    def test_get_query_params(
        self, scope, receive_event, send_event, query_string
    ):
        """Test retrieving request query parameters."""
        scope["query_string"] = query_string
        request = Request(scope, receive_event, send_event)
        assert request.query_params == parse_qs(query_string)

    def test_get_no_query_params(self, scope, receive_event, send_event):
        """Test retrieving non-existent request query parameters."""
        del scope["query_string"]
        request = Request(scope, receive_event, send_event)
        assert request.query_params == parse_qs(b"")

    def test_get_url(self, scope, receive_event, send_event):
        """Test retrieving request URL."""
        request = Request(scope, receive_event, send_event)

        assert request.url == {
            "scheme": scope["scheme"],
            "server": scope["server"],
            "root_path": scope["root_path"],
            "path": scope["path"],
            "query_string": scope["query_string"],
        }

    def test_get_no_url(self, scope, receive_event, send_event):
        """Test retrieving non-existent request URL."""
        del scope["scheme"]
        del scope["server"]
        del scope["root_path"]
        del scope["path"]
        del scope["query_string"]

        request = Request(scope, receive_event, send_event)

        assert request.url == {
            "scheme": None,
            "server": None,
            "root_path": None,
            "path": None,
            "query_string": None,
        }

    @mark.parametrize(
        "message",
        [
            [{"type": "http.request", "body": b"", "more_body": False}],
            [
                {
                    "type": "http.requset",
                    "body": b"Hello, ",
                    "more_body": True,
                },
                {
                    "type": "http.request",
                    "body": b"World!",
                    "more_body": False,
                },
            ],
        ],
    )
    @mark.asyncio
    async def test_get_body(self, message, scope, send_event):
        """Test retrieving request body."""
        receive_event = AsyncMock(side_effect=message)
        request = Request(scope, receive_event, send_event)

        body = await request.body()

        assert body == b"".join([chunk["body"] for chunk in message])

    @mark.asyncio
    async def test_get_already_streamed_body(
        self, scope, receive_event, send_event
    ):
        """Test retrieving the request body that has already been streamed."""
        request = Request(scope, receive_event, send_event)

        first_body_retrieve = await request.body()
        second_body_retrieve = await request.body()

        assert first_body_retrieve == second_body_retrieve

    @mark.parametrize(
        "message",
        [
            [
                {
                    "type": "http.request",
                    "body": b'{"message": "Hello, World!"}',
                    "more_body": False,
                }
            ],
            [
                {
                    "type": "http.requset",
                    "body": b'{"message":',
                    "more_body": True,
                },
                {
                    "type": "http.request",
                    "body": b' "Hello, World!"}',
                    "more_body": False,
                },
            ],
        ],
    )
    @mark.asyncio
    async def test_get_json(self, message, scope, send_event):
        """Test retrieving request as JSON."""
        receive_event = AsyncMock(side_effect=message)
        request = Request(scope, receive_event, send_event)

        json = await request.json()

        assert json == loads(b"".join([chunk["body"] for chunk in message]))

    @mark.parametrize(
        "message",
        [
            [{"type": "http.request", "body": b"", "more_body": False}],
            [
                {
                    "type": "http.requset",
                    "body": b"Hello, ",
                    "more_body": True,
                },
                {
                    "type": "http.request",
                    "body": b"World!",
                    "more_body": False,
                },
            ],
        ],
    )
    @mark.asyncio
    async def test_streaming_body(self, message, scope, send_event):
        """Test retrieving the request body."""
        receive_event = AsyncMock(side_effect=message)
        request = Request(scope, receive_event, send_event)

        chunks = [chunk async for chunk in request.stream_body()]

        assert chunks == [chunk["body"] for chunk in message]
        assert receive_event.call_count == len(message)

    @mark.asyncio
    async def test_cannot_streaming_body_multiple_times(
        self, scope, receive_event, send_event
    ):
        """Test streaming an already streamed request body ."""
        request = Request(scope, receive_event, send_event)

        [chunk async for chunk in request.stream_body()]

        with raises(BodyStreamError, match="Body already streamed"):
            [chunk async for chunk in request.stream_body()]

    @mark.asyncio
    async def test_client_disconnect_while_streaming_body(
        self, scope, send_event
    ):
        """Test streaming a request body from a disconnected client."""
        receive_event = AsyncMock(return_value={"type": "http.disconnect"})
        request = Request(scope, receive_event, send_event)

        with raises(BodyStreamError, match="Client disconnected"):
            [chunk async for chunk in request.stream_body()]
