"""A set of classes that can be used to send HTTP responses to the client."""
from http.cookies import BaseCookie
from typing import Coroutine, Optional, Union


class Response:
    """A HTTP response representation that can be sent to the client.

    Attributes:
        charset (str): the character set of the body.
        media_type (str, optional): the content-type of the body.
    """

    charset: str = "utf-8"
    media_type: Optional[str] = None

    def __init__(
        self,
        body: Union[bytes, str] = b"",
        status_code: int = 200,
        headers: dict = {},
    ) -> None:
        """Establish the response information.

        The body and headers of the response will be rendered in preparation
        for sending to the client.

        Args:
            body (Union[bytes, str], optional): content of the response.
                Defaults to b"".
            status_code (int, optional): status code of the response.
                Defaults to 200.
            headers (dict, optional): headers of the response. Defaults to {}.
        """
        self.body = self._render_content(body)
        self.headers = self._render_headers(
            headers, len(self.body), self.media_type
        )
        self.status_code = status_code

    def add_cookie(self, cookie: BaseCookie) -> None:
        """Add a cookie to the response.

        Args:
            cookie (BaseCookie): a `BaseCookie` object to encode for a
                set-cookie header.
        """
        cookie_value = cookie.output(header="").strip()
        self.headers.append(self._render_header("set-cookie", cookie_value))

    @classmethod
    def _render_content(cls, content: Union[bytes, str]) -> bytes:
        """Encode content to bytes for use as a response body.

        Args:
            content (Union[bytes, str]): the content to render.

        Returns:
            bytes: the rendered content.
        """
        if isinstance(content, bytes):
            return content
        return content.encode(cls.charset)

    @staticmethod
    def _render_header(name: str, value: str) -> tuple[bytes, bytes]:
        """Render a header for use in a HTTP response.

        Args:
            name (str): the header name.
            value (str): the header value.

        Returns:
            tuple[bytes, bytes]: the rendered header.
        """
        return (name.lower().encode("latin-1"), value.encode("latin-1"))

    @classmethod
    def _render_headers(
        cls,
        headers: dict[str, str],
        content_length: int = 0,
        content_type: Optional[str] = None,
    ) -> list[tuple[bytes, bytes]]:
        """Render a set of headers that are usable for a HTTP response.

        The content-length and content-type headers will be rendered if the
        content_length and content_type parameters are provided.
        If content_type begins with 'text/' then the charset will be appended
        to the header's value.

        Args:
            headers (dict[str, str]): headers to render.
            content_length (int, optional): size of the response content.
                Defaults to None.
            content_type (str, optional): the MIME type of the response
                content. Defaults to None.

        Returns:
            list[tuple[bytes, bytes]]: list of headers rendered for a response.
        """
        headers = [
            cls._render_header(key, value) for key, value in headers.items()
        ]
        keys = [header[0] for header in headers]

        if content_length and b"content-length" not in keys:
            headers.append(
                cls._render_header("content-length", str(content_length))
            )

        if content_type is not None and b"content-type" not in keys:
            if content_type.startswith("text/"):
                content_type += f"; charset={cls.charset}"

            headers.append(cls._render_header("content-type", content_type))

        return headers

    async def __call__(self, send: Coroutine) -> None:
        """Send the response to the client.

        Args:
            send (Coroutine): the coroutine function to call to send the
                response to the client.
        """
        await send(
            {
                "type": "http.response.start",
                "status": self.status_code,
                "headers": self.headers,
            }
        )
        await send({"type": "http.response.body", "body": self.body})

class HtmlResponse(Response):
    """A HTTP response with a media type of text/html.

    Attributes:
        media_type (str, optional): the content-type of the body.
    """
    media_type: Optional[str] = "text/html"
