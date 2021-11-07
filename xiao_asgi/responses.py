"""A set of classes that can render responses to a client."""
from abc import ABC, abstractmethod
from typing import Any, Generator, Optional, Union


class Response(ABC):
    """Base class for responses.

    Attributes:
        protocol (str): the protocol used to send the response.
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

    Args:
        body (Union[bytes, Generator[bytes, None, None]], optional): the body content of the response.
        headers (list[bytes, bytes], optional): the headers of the response.
        status (int, optional): a HTTP status code. Defaults to 200.

    Attributes:
        body (Union[bytes, Generator[bytes, None, None]]): the body content of the response.
        headers (list[bytes, bytes]): the headers of the response.
        protocol (str): the protocol used to send the response. Defaults to http.
        status (int): a HTTP status code.
    """

    protocol: str = "http"

    def __init__(
        self,
        status: Optional[int] = 200,
        headers: Optional[list[bytes, bytes]] = [],
        body: Optional[Union[bytes, Generator[bytes, None, None]]] = b"",
    ) -> None:
        self.status = status
        self.headers = headers
        self.body = body


class BodyResponse(Http):
    """A body HTTP response.

    Produces two messages:
    * first is to start the response
    * second is to send the body content.
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

        The response is converted to a series of dictionary messages.

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


class WebSocket(Response):
    protocol: str = "websocket"


class AcceptResponse(WebSocket):
    def __init__(
        self,
        subprotocol: Optional[str] = None,
        headers: list[tuple[bytes, bytes]] = [],
    ) -> None:
        self.headers = headers
        self.subprotocol = subprotocol

    def render_messages(self) -> dict[str, Any]:
        yield {
            "type": f"{self.protocol}.accept",
            "subprotocol": self.subprotocol,
            "headers": self.headers,
        }


class MessageResponse(WebSocket):
    def __init__(
        self, bytes: Optional[bytes] = None, text: Optional[str] = None
    ) -> None:
        self.bytes = bytes
        self.text = text

    def render_messages(self) -> dict[str, Any]:
        yield {
            "type": f"{self.protocol}.send",
            "bytes": self.bytes,
            "text": self.text,
        }


class CloseResponse(WebSocket):
    def __init__(self, code: Optional[int] = 1000) -> None:
        self.code = code

    def render_messages(self) -> dict[str, Any]:
        yield {"type": f"{self.protocol}.close", "code": self.code}
