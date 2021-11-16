"""HTTP responses.

A set of classes for creating response classes that can render for sending to
the connection.

Classes:
    Response: abstract base class for creating responses.
    Http: base class for HTTP responses.
    BodyResponse: a single HTTP response.
    StreamResponse: multiple chunked HTTP responses.
"""
from abc import ABC, abstractmethod
from typing import Any, Generator, Optional, Union


class Response(ABC):
    """Base class for responses.

    Attributes:
        protocol (str): the protocol to use for sending the response.
    """

    protocol: str

    @abstractmethod
    def render_messages(self) -> Generator[dict[str, Any], None, None]:
        """Yield rendered messages.

        The response is converted to a series of dictionary messages.

        Yields:
            Generator[dict[str, Any], None, None]: a dictionary message.
        """


class Http(Response):
    """Base class for HTTP responses.

    Attributes:
        body (Union[bytes, Generator[bytes, None, None]]): the body content of
            the response.
        headers (list[bytes, bytes]): the headers of the response.
        protocol (str, optional): the protocol to use to send the response.
            Defaults to http.
        status (int): a HTTP status code.
    """

    protocol: str = "http"

    def __init__(
        self,
        status: Optional[int] = 200,
        headers: Optional[list[bytes, bytes]] = [],
        body: Optional[Union[bytes, Generator[bytes, None, None]]] = b"",
    ) -> None:
        """Establish the response information.

        Args:
            body (Union[bytes, Generator[bytes, None, None]], optional): the
                body content of the response. Defaults to an empty bytes
                string.
            headers (list[bytes, bytes], optional): the headers of the
                response. Defaults to an empty list.
            status (int, optional): a HTTP status code. Defaults to 200.
        """
        self.status = status
        self.headers = headers
        self.body = body


class BodyResponse(Http):
    """A single HTTP response.

    Produces two messages in total:
        first is to start the response.
        second is to send the body content.
    """

    def render_messages(self) -> Generator[dict[str, Any], None, None]:
        """Yield rendered messages.

        The response is converted to a series of dictionary messages.

        Yields:
            Generator[dict[str, Any], None, None]: a dictionary message.
        """
        yield {
            "type": f"{self.protocol}.response.start",
            "status": self.status,
            "headers": self.headers,
        }

        yield {
            "type": f"{self.protocol}.response.body",
            "body": self.body,
            "more_body": False,
        }


class StreamResponse(Http):
    """A streamed HTTP response.

    Produces two or more messages, rendering the body content in separate
    messages.
    """

    def render_messages(self) -> Generator[dict[str, Any], None, None]:
        """Yield rendered messages.

        The response is converted to a series of dictionary messages, based on
        the iterable provided for the response's ``body``.

        Yields:
            Generator[dict[str, Any], None, None]: a dictionary message.
        """
        yield {
            "type": f"{self.protocol}.response.start",
            "status": self.status,
            "headers": self.headers,
        }

        response_type = f"{self.protocol}.response.body"

        for chunk in self.body:
            yield {"type": response_type, "body": chunk, "more_body": True}

        yield {"type": response_type, "body": b"", "more_body": False}
