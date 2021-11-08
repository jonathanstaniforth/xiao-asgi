from pytest import raises

from xiao_asgi.responses import (
    AcceptResponse,
    BodyResponse,
    CloseResponse,
    Http,
    MessageResponse,
    Response,
    StreamResponse,
    WebSocket,
)


class TestResponse:
    def test_render_method(self):
        with raises(
            TypeError,
            match="Can't instantiate abstract class Response with abstract method render_messages",
        ):
            Response()


class TestHttp:
    class MockHttp(Http):
        def render_messages(self):
            pass

    def test_create_instance_with_defaults(self):
        response = self.MockHttp()

        assert isinstance(response, Response)
        assert response.protocol == "http"
        assert response.status == 200
        assert response.headers == []
        assert response.body == b""

    def test_create_instance_with_customs(self):
        status = 201
        headers = [
            (b"content-type", b"text/plain"),
            (b"user-agent", b"PostmanRuntime/7.26.8"),
            (b"accept", b"*/*"),
            (b"host", b"localhost:8000"),
            (b"accept-encoding", b"gzip, deflate, br"),
            (b"connection", b"keep-alive"),
            (b"content-length", b"5"),
        ]
        body = b"Hello World!"

        response = self.MockHttp(status, headers, body)

        assert isinstance(response, Response)
        assert response.protocol == "http"
        assert response.status == status
        assert response.headers == [
            (b"content-type", b"text/plain"),
            (b"user-agent", b"PostmanRuntime/7.26.8"),
            (b"accept", b"*/*"),
            (b"host", b"localhost:8000"),
            (b"accept-encoding", b"gzip, deflate, br"),
            (b"connection", b"keep-alive"),
            (b"content-length", b"5"),
        ]
        assert response.body == body


class TestBodyResponse:
    def test_create_instance(self):
        response = BodyResponse()

        assert isinstance(response, Http)

    def test_render_messages_with_defaults(self):
        response = BodyResponse()

        messages = [message for message in response.render_messages()]

        assert messages == [
            {"type": "http.response.start", "status": 200, "headers": []},
            {"type": "http.response.body", "body": b"", "more_body": False},
        ]

    def test_render_messages_with_customs(self):
        status = 201
        headers = [
            (b"content-type", b"text/plain"),
            (b"user-agent", b"PostmanRuntime/7.26.8"),
            (b"accept", b"*/*"),
            (b"host", b"localhost:8000"),
            (b"accept-encoding", b"gzip, deflate, br"),
            (b"connection", b"keep-alive"),
            (b"content-length", b"5"),
        ]
        body = b"Hello World!"

        response = BodyResponse(status, headers, body)

        messages = [message for message in response.render_messages()]

        assert messages == [
            {
                "type": "http.response.start",
                "status": status,
                "headers": headers,
            },
            {"type": "http.response.body", "body": body, "more_body": False},
        ]


class TestStreamResponse:
    def test_create_instance(self):
        response = StreamResponse()

        assert isinstance(response, Http)

    def test_render_messages(self):
        status = 201
        headers = [
            (b"content-type", b"text/plain"),
            (b"user-agent", b"PostmanRuntime/7.26.8"),
            (b"accept", b"*/*"),
            (b"host", b"localhost:8000"),
            (b"accept-encoding", b"gzip, deflate, br"),
            (b"connection", b"keep-alive"),
            (b"content-length", b"5"),
        ]
        body = [b"Hello ", b"World!"]

        response = StreamResponse(status, headers, body)

        messages = [message for message in response.render_messages()]

        assert messages == [
            {
                "type": "http.response.start",
                "status": status,
                "headers": headers,
            },
            {
                "type": "http.response.body",
                "body": b"Hello ",
                "more_body": True,
            },
            {
                "type": "http.response.body",
                "body": b"World!",
                "more_body": True,
            },
            {"type": "http.response.body", "body": b"", "more_body": False},
        ]


class TestWebSocket:
    class MockWebSocket(WebSocket):
        def render_messages(self):
            pass

    def test_create_instance(self):
        response = self.MockWebSocket()

        assert response.protocol == "websocket"


class TestAcceptResponse:
    def test_create_instance_with_defaults(self):
        response = AcceptResponse()

        assert isinstance(response, WebSocket)
        assert response.headers == []
        assert response.subprotocol == None

    def test_create_instance_with_customs(self):
        response = AcceptResponse(
            "protocol-v1",
            [
                (b"content-type", b"text/plain"),
                (b"user-agent", b"PostmanRuntime/7.26.8"),
                (b"accept", b"*/*"),
                (b"host", b"localhost:8000"),
                (b"accept-encoding", b"gzip, deflate, br"),
                (b"connection", b"keep-alive"),
                (b"content-length", b"5"),
            ],
        )

        assert response.headers == [
            (b"content-type", b"text/plain"),
            (b"user-agent", b"PostmanRuntime/7.26.8"),
            (b"accept", b"*/*"),
            (b"host", b"localhost:8000"),
            (b"accept-encoding", b"gzip, deflate, br"),
            (b"connection", b"keep-alive"),
            (b"content-length", b"5"),
        ]
        assert response.subprotocol == "protocol-v1"

    def test_render_messages_with_defaults(self):
        response = AcceptResponse()

        messages = [message for message in response.render_messages()]

        assert messages[0] == {
            "type": "websocket.accept",
            "subprotocol": None,
            "headers": [],
        }

    def test_render_messages_with_customs(self):
        response = AcceptResponse(
            "protocol-v1",
            [
                (b"content-type", b"text/plain"),
                (b"user-agent", b"PostmanRuntime/7.26.8"),
                (b"accept", b"*/*"),
                (b"host", b"localhost:8000"),
                (b"accept-encoding", b"gzip, deflate, br"),
                (b"connection", b"keep-alive"),
                (b"content-length", b"5"),
            ],
        )

        messages = [message for message in response.render_messages()]

        assert messages[0] == {
            "type": "websocket.accept",
            "subprotocol": "protocol-v1",
            "headers": [
                (b"content-type", b"text/plain"),
                (b"user-agent", b"PostmanRuntime/7.26.8"),
                (b"accept", b"*/*"),
                (b"host", b"localhost:8000"),
                (b"accept-encoding", b"gzip, deflate, br"),
                (b"connection", b"keep-alive"),
                (b"content-length", b"5"),
            ],
        }


class TestMessageResponse:
    def test_create_instance_with_defaults(self):
        response = MessageResponse()

        assert response.bytes == None
        assert response.text == None

    def test_create_instance_with_customs(self):
        response = MessageResponse(b"Hello World!", "Hello World!")

        assert response.bytes == b"Hello World!"
        assert response.text == "Hello World!"

    def test_render_messages_with_defaults(self):
        response = MessageResponse()

        messages = [message for message in response.render_messages()]

        assert messages[0] == {
            "type": "websocket.send",
            "bytes": None,
            "text": None,
        }

    def test_render_messages_with_customs(self):
        response = MessageResponse(b"Hello World!", "Hello World!")

        messages = [message for message in response.render_messages()]

        assert messages[0] == {
            "type": "websocket.send",
            "bytes": b"Hello World!",
            "text": "Hello World!",
        }


class TestCloseResponse:
    def test_create_instance_with_defaults(self):
        response = CloseResponse()

        assert response.code == 1000

    def test_create_instance_with_customs(self):
        response = CloseResponse(1001)

        assert response.code == 1001

    def test_render_messages_with_defaults(self):
        response = CloseResponse()

        messages = [message for message in response.render_messages()]

        assert messages[0] == {"type": "websocket.close", "code": 1000}

    def test_render_messages_with_defaults(self):
        response = CloseResponse(1001)

        messages = [message for message in response.render_messages()]

        assert messages[0] == {"type": "websocket.close", "code": 1001}
