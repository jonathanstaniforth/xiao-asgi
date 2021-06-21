"""Test the `xiao_asgi.responses` module."""
from http.cookies import SimpleCookie
from json import dumps
from unittest.mock import AsyncMock, call

from pytest import fixture, mark

from xiao_asgi.responses import (
    HtmlResponse,
    JsonResponse,
    PlainTextResponse,
    Response,
)


@fixture
def headers():
    return {
        "Server": "TestServer",
        "Cache-Control": "max-age=3600, public",
        "Etag": "pub1259380237;gz",
    }


class TestResponse:
    """Test the `xiao_asgi.responses.Response` class."""

    def test_create_new_response_with_defaults(self):
        response = Response()

        assert response.body == b""
        assert response.headers == []
        assert response.media_type is None
        assert response.status_code == 200

    def test_create_new_response(self, headers):
        body = '{"message": "Created"}'
        status_code = 201

        response = Response(
            body=body,
            status_code=status_code,
            headers=headers,
        )

        assert response.body == body.encode("utf-8")
        assert response.headers == [
            (b"server", b"TestServer"),
            (b"cache-control", b"max-age=3600, public"),
            (b"etag", b"pub1259380237;gz"),
            (b"content-length", b"22"),
        ]
        assert response.media_type is None
        assert response.status_code == status_code

    def test_add_cookie(self):
        response = Response()
        cookie = SimpleCookie()
        cookie["test"] = "test-cookie"

        response.add_cookie(cookie)

        cookie_value = cookie.output(header="").strip()
        assert response.headers == [
            (b"set-cookie", cookie_value.encode("latin-1"))
        ]

    @mark.parametrize("content", [b"", b"Hello, World!", "", "Hello, World!"])
    def test_render_content(self, content):
        rendered_content = Response._render_content(content)

        expected_content = (
            content if isinstance(content, bytes) else content.encode()
        )

        assert rendered_content == expected_content

    def test_render_header(self, headers):
        for name, value in headers.items():
            rendered_header = Response._render_header(name, value)

            assert rendered_header == (
                name.lower().encode("latin-1"),
                value.encode("latin-1"),
            )

    def test_render_headers_without_content_headers(self, headers):
        rendered_headers = Response._render_headers(headers)

        assert rendered_headers == [
            (b"server", b"TestServer"),
            (b"cache-control", b"max-age=3600, public"),
            (b"etag", b"pub1259380237;gz"),
        ]

    @mark.parametrize(
        "media_type",
        [
            ("text/plain", b"text/plain; charset=utf-8"),
            ("application/json", b"application/json"),
        ],
    )
    def test_render_headers_with_content_headers(self, headers, media_type):
        body = "Hello, World!"

        rendered_headers = Response._render_headers(
            headers, len(body), media_type[0]
        )

        assert rendered_headers == [
            (b"server", b"TestServer"),
            (b"cache-control", b"max-age=3600, public"),
            (b"etag", b"pub1259380237;gz"),
            (b"content-length", b"13"),
            (b"content-type", media_type[1]),
        ]

    @mark.asyncio
    async def test_call(self, headers):
        status_code = 201
        body = "Hello, World!"
        send_event = AsyncMock()

        response = Response(
            body="Hello, World!",
            status_code=201,
            headers=headers,
        )

        await response(send_event)

        send_event.assert_has_awaits(
            [
                call(
                    {
                        "type": "http.response.start",
                        "status": status_code,
                        "headers": response.headers,
                    }
                ),
                call({"type": "http.response.body", "body": body.encode()}),
            ]
        )


class TestHtmlResponse:
    """Test the `xiao_asgi.responses.HtmlResponse` class."""

    def test_create_with_defaults(self):
        response = HtmlResponse()

        assert response.body == b""
        assert response.headers == [
            (b"content-type", b"text/html; charset=utf-8")
        ]
        assert response.media_type == "text/html"
        assert response.status_code == 200

    def test_create_without_defaults(self, headers):
        body = '{"message": "Created"}'
        status_code = 201

        response = HtmlResponse(
            body=body,
            status_code=status_code,
            headers=headers,
        )

        assert response.body == body.encode("utf-8")
        assert response.headers == [
            (b"server", b"TestServer"),
            (b"cache-control", b"max-age=3600, public"),
            (b"etag", b"pub1259380237;gz"),
            (b"content-length", b"22"),
            (b"content-type", b"text/html; charset=utf-8"),
        ]
        assert response.media_type == "text/html"
        assert response.status_code == status_code


class TestJsonResponse:
    """Test the `xiao_asgi.responses.JsonResponse` class."""

    def test_create_with_defaults(self):
        response = JsonResponse()

        assert response.body == b""
        assert response.headers == [(b"content-type", b"application/json")]
        assert response.media_type == "application/json"
        assert response.status_code == 200

    def test_create_without_defaults(self, headers):
        body = {"message": "Created"}
        status_code = 201

        response = JsonResponse(
            body=body,
            status_code=status_code,
            headers=headers,
        )

        assert (
            response.body
            == dumps(
                body,
                ensure_ascii=False,
                allow_nan=False,
                indent=None,
                separators=(",", ":"),
            ).encode("utf-8")
        )
        assert response.headers == [
            (b"server", b"TestServer"),
            (b"cache-control", b"max-age=3600, public"),
            (b"etag", b"pub1259380237;gz"),
            (b"content-length", b"21"),
            (b"content-type", b"application/json"),
        ]
        assert response.media_type == "application/json"
        assert response.status_code == status_code

    def test_render_content_without_bytes(self):
        content = {"message": "Created"}

        rendered_content = JsonResponse._render_content(content)

        assert (
            rendered_content
            == dumps(
                content,
                ensure_ascii=False,
                allow_nan=False,
                indent=None,
                separators=(",", ":"),
            ).encode("utf-8")
        )

    def test_render_content_with_bytes(self):
        content = b"message: Created"

        rendered_content = JsonResponse._render_content(content)

        assert rendered_content == content


class TestPlainTextResponse:
    """Test the `xiao_asgi.responses.PlainTextResponse` class."""

    def test_create_with_defaults(self):
        response = PlainTextResponse()

        assert response.body == b""
        assert response.headers == [
            (b"content-type", b"text/plain; charset=utf-8")
        ]
        assert response.media_type == "text/plain"
        assert response.status_code == 200

    def test_create_without_defaults(self, headers):
        body = '{"message": "Created"}'
        status_code = 201

        response = PlainTextResponse(
            body=body,
            status_code=status_code,
            headers=headers,
        )

        assert response.body == body.encode("utf-8")
        assert response.headers == [
            (b"server", b"TestServer"),
            (b"cache-control", b"max-age=3600, public"),
            (b"etag", b"pub1259380237;gz"),
            (b"content-length", b"22"),
            (b"content-type", b"text/plain; charset=utf-8"),
        ]
        assert response.media_type == "text/plain"
        assert response.status_code == status_code
