"""A set of classes that can render responses to a client."""
from abc import ABC, abstractmethod
from typing import Any, Optional, Union, Generator


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
        pass


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

    def __init__(self, status: Optional[int] = 200, headers: Optional[list[bytes, bytes]] = [], body: Optional[Union[bytes, Generator[bytes, None, None]]] = b"") -> None:
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
            "headers": self.headers
        }

        yield {
            "type": f"{self.protocol}.response.body",
            "body": self.body,
            "more_body": False
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
            "headers": self.headers
        }

        response_type = f"{self.protocol}.response.body"

        for chunk in self.body:
            yield {
                "type": response_type,
                "body": chunk,
                "more_body": True
            }

        yield {
            "type": response_type,
            "body": b"",
            "more_body": False
        }











