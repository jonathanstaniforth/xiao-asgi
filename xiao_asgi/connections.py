"""Handling HTTP and WebSocket connection.

Several classes for handling HTTP and WebSocket connections including
receiving and send messages, along with exceptions for connection errors.

Classes:
    ProtocolUnknown: an unknown protocol is being used.
    ProtocolMismatch: protocols between two objects do not match.
    InvalidConnectionState: connection state of a client/application is not
        appropriate for the request/response.
    Connection: abstract base class from which connection classes can be built
        for a protocol.
    HttpConnection: for handling HTTP connections.
    WebSocketConnection: for handling WebSocket connections.

Functions:
    make_connection: factory function for creating a connection instance for a
        protocol.

Variables:
    protocols: list of known protocols and their associated connection class.
"""
from abc import ABC, abstractmethod
from collections.abc import Coroutine, Iterable
from typing import Optional

from xiao_asgi.requests import Request
from xiao_asgi.responses import Response


class ProtocolUnknown(Exception):
    """The protocol used is unknown.

    The list of known protocols is set in the ``protocols`` module variable.

    Example:
        When this exception is raised::

            >>> if scope["type"] != connection.protocol:
            >>>     raise ProtocolUnknown()
    """


class ProtocolMismatch(Exception):
    """The protocols used by two objects do not match.

    Example:
        When this exception is raised::

            >>> if request["type"].split(".")[0] != connection.protocol:
            >>>     raise ProtocolMismatch()
    """


class InvalidConnectionState(Exception):
    """A connection state is not valid for the type of request/response.

    Example:
        When this exception is raised::

            >>> if self.application_connection_state == "disconnected":
            >>>     raise InvalidConnectionState((
            >>>         f"Cannot send a response when the application has "
            >>>         f"disconnected."
            >>>     ))
    """


class Connection(ABC):
    """A base connection class for handling messages to and from a connection.

    Can be extended for a specific protocol.

    Attributes:
        protocol (str): name of the connection protocol.
        scope (dict[str, Any]): the connection information.
        _receive (Coroutine): coroutine for receiving requests.
        _send (Coroutine): coroutine for sending responses.
    """

    protocol: str

    def __init__(
        self,
        scope: dict,
        receive: Coroutine[dict, None, None],
        send: Coroutine[dict, None, None],
    ):
        """Establish the connection information.

        Args:
            scope (dict[str, Any]): the connection information.
            receive (Coroutine): coroutine for receiving requests.
            send (Coroutine): coroutine for sending responses.
        """
        if scope["type"] != self.protocol:
            raise ValueError(
                (
                    f"The type of the connection must be {self.protocol}, not "
                    f"{scope['type']}."
                )
            )

        self.scope = scope
        self._receive = receive
        self._send = send

    @property
    def headers(self) -> dict[str, str]:
        """Return the headers provided in the connection.

        Returns:
            dict[str, str]: the connection's headers.
        """
        return {
            key.decode("latin-1"): value.decode("latin-1")
            for key, value in self.scope.get("headers", [])
        }

    @property
    def url(self) -> dict[str, str]:
        """Return the URL information provided in the connection.

        The URL is split in to its separate components.

        Returns:
            dict[str, str]: the URL information.
        """
        return {
            "scheme": self.scope.get("scheme"),
            "server": self.scope.get("server"),
            "root_path": self.scope.get("root_path"),
            "path": self.scope.get("path"),
            "query_string": self.scope.get("query_string"),
        }

    @abstractmethod
    async def receive_request(self) -> Request:
        """Receive a request from the client.

        Returns:
            Request: the received request.
        """


class HttpConnection(Connection):
    """A HTTP connection.

    This Connection class is capable of receiving requests and sending
    responses that use the protocol http.

    Attributes:
        protocol (str): name of the connection protocol, defaults to http.
        connection_status (bool): the current status of the connection
            response.
    """

    protocol: str = "http"

    def __init__(self, *args) -> None:
        """Establish the response status of the connection."""
        super().__init__(*args)

        self.connection_status = "open"

    @property
    def method(self) -> str:
        """Return the method provided in the connection.

        Returns:
            str: the connection's method.
        """
        return self.scope["method"]

    async def receive_request(self) -> Request:
        """Receive a request from the client.

        Returns:
            Request: the received request.
        """
        request = await self._receive()
        protocol, type = request["type"].split(".")

        del request["type"]

        return Request(protocol=protocol, type=type, data=request)

    async def send_body(
        self, data: bytes = b"", more_body: bool = False
    ) -> None:
        """Send a HTTP body response to the client.

        A HTTP start response must be sent to the client before a body
        response (``HttpConnection.send_start_response()``).

        Args:
            data (bytes, optional): the content of the response. Defaults to
                bytes.
            more_body (bool, optional): whether any additional body responses
                will be sent after this message. A value of ``False`` will
                result in the connection being closed. Defaults to False.
        """
        if self.connection_status != "closing":
            raise InvalidConnectionState(
                f"The connection_status must be closing not "
                f"{self.connection_status}"
            )

        await self._send(
            {
                "type": f"{self.protocol}.response.body",
                "body": data,
                "more_body": more_body,
            }
        )

        if not more_body:
            self.connection_status = "closed"

    async def send_response(self, response: type[Response]) -> None:
        """Send a response to the client.

        Args:
            response (type[Response]): the response to send.
        """
        rendered_response = response.render_response()

        await self.send_start(
            rendered_response["status"], rendered_response["headers"]
        )
        await self.send_body(
            rendered_response["body"], rendered_response["more_body"]
        )

    async def send_start(
        self,
        status_code: int = 200,
        headers: Iterable[Iterable[bytes, bytes]] = [],
    ) -> None:
        """Send a HTTP start response to the client.

        Args:
            status_code (int, optional): a HTTP status code for the response.
                Defaults to 200.
            headers (Iterable[Iterable[bytes, bytes]], optional): headers for
                the response. Defaults to [].
        """
        if self.connection_status != "open":
            raise InvalidConnectionState(
                "Cannot send start response as the response has "
                "already been started."
            )

        await self._send(
            {
                "type": f"{self.protocol}.response.start",
                "status": status_code,
                "headers": headers,
            }
        )

        self.connection_status = "closing"


class WebSocketConnection(Connection):
    """A WebSocket connection.

    This connection class is capable of receiving requests and sending
    responses that have the type websocket.

    Attributes:
        protocol (str): name of the connection protocol, defaults to websocket.
        connection_state (str): the current state of the connection. Defaults
            to connecting.
    """

    protocol: str = "websocket"

    def __init__(self, *args):
        """Set the connection state for the application and client."""
        super().__init__(*args)

        self.connection_state = "connecting"

    async def accept_connection(
        self,
        subprotocol: Optional[str] = None,
        headers: Iterable[Iterable[bytes, bytes]] = [],
    ) -> None:
        """Accept the WebSocket connection.

        Sends an accept response to the client.

        Args:
            subprotocol (Optional[str], optional): the subprotocol selected by
                the application. Defaults to None.
            headers (Iterable[Iterable[bytes, bytes]], optional): the headers
                of the response. Defaults to [].
        """
        await self._send(
            {
                "type": f"{self.protocol}.accept",
                "subprotocol": subprotocol,
                "headers": headers,
            }
        )
        self.connection_state = "accepted"

    async def close_connection(self, code: Optional[int] = 1000) -> None:
        """Close the WebSocket connection.

        Sends a close response to the client.

        Args:
            code (Optional[int], optional): the close code. Defaults to 1000.
        """
        await self._send({"type": f"{self.protocol}.close", "code": code})
        self.connection_state = "closed"

    async def receive_request(self) -> Request:
        """Receive a request from the client.

        Raises:
            InvalidConnectionState: ``self.connection_state`` is disconnected.

        Returns:
            Request: the received request.
        """
        if self.connection_state == "disconnected":
            raise InvalidConnectionState(
                "Cannot receive a request from a disconnected connection."
            )

        request = await self._receive()
        protocol, type = request["type"].split(".")

        if type == "connect":
            self.connection_state = "connected"
        elif type == "disconnect":
            self.connection_state = "disconnected"

        del request["type"]

        return Request(protocol=protocol, type=type, data=request)

    async def send_bytes(self, data: bytes) -> None:
        """Send a message containing bytes data to the client.

        Args:
            data (bytes): the contents of the message.
        """
        await self._send(
            {
                "type": f"{self.protocol}.send",
                "bytes": data,
            }
        )

    async def send_text(self, data: str) -> None:
        """Send a message containing string data to the client.

        Args:
            data (str): the contents of the message.
        """
        await self._send(
            {
                "type": f"{self.protocol}.send",
                "text": data,
            }
        )


protocols = {"http": HttpConnection, "websocket": WebSocketConnection}
"""dict[str, type[Connection]]: maps protocol names to connection classes."""


def make_connection(scope, receive, send) -> type[Connection]:
    """Return a ``Connection`` instance for a protocol.

    Args:
        scope (dict): the request information.
        receive (Coroutine): the coroutine function to call to receive a
            client request.
        send (Coroutine): the coroutine function to call to send the
            response to the client.

    Raises:
        Exception: if the scope protocol is not available in protocols.

    Returns:
        type[Connection]: a ``Connection`` instance for the protocol.
    """
    try:
        return protocols[scope["type"]](scope, receive, send)
    except KeyError:
        raise ProtocolUnknown()
