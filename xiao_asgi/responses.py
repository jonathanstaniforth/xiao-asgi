"""HTTP responses.

A set of classes for creating response classes that can render for sending to
the connection.

Classes:
    Response: abstract base class for creating HTTP responses.
    TextResponse: base class for text media responses.
    PlainTextResponse: plain text media type responses.
    HtmlResponse: HTML media type responses.
"""
from abc import ABC, abstractmethod
from typing import Any, Union


class Response(ABC):
    """Base class for responses.

    Attributes:
        body (Union[bytes, Generator[bytes, None, None]]): the body content of
            the response.
        media_type (str): the media type of the response.
        headers (list[bytes, bytes]): the headers of the response.
        status (int): a HTTP status code.
    """

    media_type: str

    def __init__(
        self,
        status: int = 200,
        headers: dict[str, Any] = {},
        body: Union[str, bytes] = b"",
    ) -> None:
        """Establish the response information.

        Args:
            status (int, optional): a HTTP status code. Defaults to
                200.
            headers (dict[str, Any], optional): the headers of the response.
                Defaults to {}.
            body (Union[str, bytes], optional): the body content of the
                response. Defaults to b"".
        """
        self.status = status
        self.headers = headers
        self.body = body

    @abstractmethod
    def render_body(self) -> bytes:
        """Return the response body as ``bytes``.

        Returns:
            bytes: the response body.
        """

    def render_headers(self) -> list[tuple[bytes, bytes]]:
        """Return the response headers as ``bytes``.

        Returns:
            list[tuple[bytes, bytes]]: the response headers.
        """
        rendered_headers = [
            (header.lower().encode("latin-1"), value.encode("latin-1"))
            for header, value in self.headers.items()
        ]

        content_length = str(len(self.body))
        rendered_headers.append(
            (b"content-length", content_length.encode("latin-1"))
        )

        rendered_headers.append(
            (b"content-type", self.media_type.encode("latin-1"))
        )

        return rendered_headers

    def render_response(self) -> dict[str, Any]:
        """Return the response with all content rendered.

        Returns:
            dict[str, Any]: the rendered response.
        """
        return {
            "status": self.status,
            "headers": self.render_headers(),
            "body": self.render_body(),
            "more_body": False,
        }


class TextResponse(Response):
    """A text response.

    This class should be inherited and the child class' ``media_type`` should
    start with text/.

    Attributes:
        charset (str): the charset of the response's body. Defaults to utf-8.
    """

    def __init__(self, charset: str = "utf-8", **kwargs) -> None:
        """Establish the charset of the response.

        Args:
            charset (str, optional): the charset of the response body.
                Defaults to "utf-8".
        """
        super().__init__(**kwargs)

        self.charset = charset

    def render_body(self) -> bytes:
        """Return the response body as ``bytes``.

        The body is encoded using ``self.charset``.

        Returns:
            bytes: the response body.
        """
        if isinstance(self.body, bytes):
            return self.body
        return self.body.encode(self.charset)

    def render_headers(self) -> list[tuple[bytes, bytes]]:
        """Return the response headers as ``bytes``.

        The headers are encoded using latin-1. The content-type header is
        changed to include the charset statement using the value in
        ``self.charset``.

        Returns:
            list[tuple[bytes, bytes]]: rendered headers.
        """
        rendered_headers = super().render_headers()

        for key, header in enumerate(rendered_headers):
            if header[0] == b"content-type":
                rendered_headers[key] = (
                    b"content-type",
                    header[1] + b"; charset=" + self.charset.encode("latin-1"),
                )
                break

        return rendered_headers


class PlainTextResponse(TextResponse):
    """A plain text response.

    Attributes:
        media_type (str): the media type of the response. Defaults to
            text/plain.

    Examples:
        Creating a plain text response::

            >>> response = PlainTextResponse(body="Hello, World!")
    """

    media_type: str = "text/plain"


class HtmlResponse(TextResponse):
    """A HTML response.

    Attributes:
        media_type (str): the media type of the response. Defaults to
            text/html.

    Examples:
        Creating a HTML response::

            >>> response = HtmlResponse(body="<html>...</html>")
    """

    media_type: str = "text/html"
