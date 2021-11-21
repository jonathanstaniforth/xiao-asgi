from pytest import fixture

from xiao_asgi.responses import (
    HtmlResponse,
    PlainTextResponse,
    Response,
    TextResponse,
)


@fixture
def headers():
    return {
        "user-agent": "PostmanRuntime/7.26.8",
        "accept": "*/*",
        "host": "localhost:8000",
        "accept-encoding": "gzip, deflate, br",
        "connection": "keep-alive",
    }


class BasicResponse(Response):
    media_type = "text/basic"

    def render_body(self):
        if isinstance(self.body, bytes):
            return self.body
        return self.body.encode("utf-8")


class TestResponse:
    def test_create(self):
        response = BasicResponse()

        assert isinstance(response, Response)
        assert response.status == 200
        assert response.body == b""
        assert response.headers == {}

    def test_create_with_values(self, headers):
        response = BasicResponse(
            status=201, body="Hello, World!", headers=headers
        )

        assert response.status == 201
        assert response.body == "Hello, World!"
        assert response.headers == headers

    def test_render_headers(self, headers):
        response = BasicResponse(headers=headers, body=b"Hello, World!")

        assert response.render_headers() == [
            (b"user-agent", b"PostmanRuntime/7.26.8"),
            (b"accept", b"*/*"),
            (b"host", b"localhost:8000"),
            (b"accept-encoding", b"gzip, deflate, br"),
            (b"connection", b"keep-alive"),
            (b"content-length", b"13"),
            (b"content-type", b"text/basic"),
        ]

    def test_render_response(self, headers):
        response = BasicResponse(
            status=201, headers=headers, body="Hello, World!"
        )

        assert response.render_response() == {
            "status": 201,
            "more_body": False,
            "body": "Hello, World!".encode("utf-8"),
            "headers": [
                (b"user-agent", b"PostmanRuntime/7.26.8"),
                (b"accept", b"*/*"),
                (b"host", b"localhost:8000"),
                (b"accept-encoding", b"gzip, deflate, br"),
                (b"connection", b"keep-alive"),
                (b"content-length", b"13"),
                (b"content-type", b"text/basic"),
            ],
        }


class TestTextResponse:
    def test_create(self):
        text_response = TextResponse()

        assert isinstance(text_response, Response)
        assert text_response.status == 200
        assert text_response.headers == {}
        assert text_response.body == b""
        assert text_response.charset == "utf-8"

    def test_create_with_values(self):
        text_response = TextResponse(charset="ascii")

        assert text_response.charset == "ascii"

    def test_render_body_with_bytes(self):
        response = TextResponse(body=b"Hello, World!")

        assert response.render_body() == b"Hello, World!"

    def test_render_body_with_string(self):
        response = TextResponse(body="Hello, World!")

        assert response.render_body() == "Hello, World!".encode("utf-8")

    def test_render_headers(self, headers):
        text_response = TextResponse(headers=headers, body=b"Hello, World!")
        text_response.media_type = "text/plain"
        rendered_headers = text_response.render_headers()

        assert rendered_headers == [
            (b"user-agent", b"PostmanRuntime/7.26.8"),
            (b"accept", b"*/*"),
            (b"host", b"localhost:8000"),
            (b"accept-encoding", b"gzip, deflate, br"),
            (b"connection", b"keep-alive"),
            (b"content-length", b"13"),
            (b"content-type", b"text/plain; charset=utf-8"),
        ]


class TestPlainResponse:
    def test_create(self):
        plain_response = PlainTextResponse()

        assert isinstance(plain_response, TextResponse)
        assert plain_response.media_type == "text/plain"


class TestHtmlResponse:
    def test_create(self):
        html_response = HtmlResponse()

        assert isinstance(html_response, TextResponse)
        assert html_response.media_type == "text/html"
