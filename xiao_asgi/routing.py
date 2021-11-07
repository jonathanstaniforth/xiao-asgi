"""Classes to handle routing requests to endpoints."""
from abc import ABC
from collections.abc import Coroutine

from xiao_asgi.connections import (
    Connection,
    HttpConnection,
    ProtocolMismatch,
    WebSocketConnection,
)
from xiao_asgi.requests import Request
from xiao_asgi.responses import AcceptResponse, BodyResponse, CloseResponse


class Route(ABC):
    """A generic route.

    Used as a base class for routes that involve a particular protocol.

    Props:
        protocol (str): the protocol for this route.
    """

    protocol: str

    def __init__(self, path: str) -> None:
        """Establish the path for this route.

        Args:
            path (str): the path for this route.

        Variables:
            path (str): the path for this route.
        """
        self.path = path

    async def get_endpoint(self, endpoint: str) -> Coroutine:
        """Return the Coroutine for this endpoint.

        Args:
            endpoint (str): the endpoint to retrieve.

        Returns:
            Coroutine: the Coroutine for the endoint.
        """
        return getattr(self, endpoint)

    async def __call__(self, connection: type[Connection]) -> None:
        """Pass the connection to the appropriate endpoint.

        Args:
            connection (type[Connection]): a :class:`Connection` instance with
            the connection information.

        Raises:
            ProtocolMismatch: if the connection's protocol does not match this
            route's protocol.
        """
        if connection.protocol != self.protocol:
            raise ProtocolMismatch()


class HttpRoute(Route):
    """A HTTP route.

    Props:
        protocol (str): the protocol for this route. Defaults to http.
    """

    protocol: str = "http"

    async def get(self, connection: HttpConnection, request: Request) -> None:
        """Endpoint for a GET request method.

        Override to implement this endpoint.

        Args:
            connection (HttpConnection): a :class:`Connection` instance with
            the connection information.
            request (Request): the received request.
        """
        await self.send_method_not_allowed(connection)

    async def head(self, connection: HttpConnection, request: Request) -> None:
        """Endpoint for a HEAD request method.

        Override to implement this endpoint.

        Args:
            connection (type[Connection]): a :class:`Connection` instance with
            the connection information.
            request (Request): the received request.
        """
        await self.send_method_not_allowed(connection)

    async def post(self, connection: HttpConnection, request: Request) -> None:
        """Endpoint for a POST request method.

        Override to implement this endpoint.

        Args:
            connection (type[Connection]): a :class:`Connection` instance with
            the connection information.
            request (Request): the received request.
        """
        await self.send_method_not_allowed(connection)

    async def put(self, connection: HttpConnection, request: Request) -> None:
        """Endpoint for a PUT request method.

        Override to implement this endpoint.

        Args:
            connection (type[Connection]): a :class:`Connection` instance with
            the connection information.
            request (Request): the received request.
        """
        await self.send_method_not_allowed(connection)

    async def delete(
        self, connection: HttpConnection, request: Request
    ) -> None:
        """Endpoint for a DELETE request method.

        Override to implement this endpoint.

        Args:
            connection (type[Connection]): a :class:`Connection` instance with
            the connection information.
            request (Request): the received request.
        """
        await self.send_method_not_allowed(connection)

    async def connect(
        self, connection: HttpConnection, request: Request
    ) -> None:
        """Endpoint for a CONNECT request method.

        Override to implement this endpoint.

        Args:
            connection (type[Connection]): a :class:`Connection` instance with
            the connection information.
            request (Request): the received request.
        """
        await self.send_method_not_allowed(connection)

    async def options(
        self, connection: HttpConnection, request: Request
    ) -> None:
        """Endpoint for a OPTIONS request method.

        Override to implement this endpoint.

        Args:
            connection (type[Connection]): a :class:`Connection` instance with
            the connection information.
            request (Request): the received request.
        """
        await self.send_method_not_allowed(connection)

    async def trace(
        self, connection: HttpConnection, request: Request
    ) -> None:
        """Endpoint for a TRACE request method.

        Override to implement this endpoint.

        Args:
            connection (type[Connection]): a :class:`Connection` instance with
            the connection information.
            request (Request): the received request.
        """
        await self.send_method_not_allowed(connection)

    async def patch(
        self, connection: HttpConnection, request: Request
    ) -> None:
        """Endpoint for a PATCH request method.

        Override to implement this endpoint.

        Args:
            connection (type[Connection]): a :class:`Connection` instance with
            the connection information.
            request (Request): the received request.
        """
        await self.send_method_not_allowed(connection)

    async def send_internal_server_error(
        self, connection: HttpConnection
    ) -> None:
        """Send a 500 HTTP response.

        Override to change the response that is sent.

        Args:
            connection (HttpConnection): the connection to send the response
            to.
        """
        await connection.send_response(
            BodyResponse(status=500, body=b"Internal Server Error")
        )

    async def send_not_implemented(self, connection: HttpConnection) -> None:
        """Send a 501 HTTP response.

        Override to change the response that is sent.

        Args:
            connection (HttpConnection): the connection to send the response
            to.
        """
        await connection.send_response(
            BodyResponse(status=501, body=b"Not Implemented")
        )

    async def send_method_not_allowed(
        self, connection: HttpConnection
    ) -> None:
        """Send a 405 HTTP response.

        Override to change the response that is sent.

        Args:
            connection (HttpConnection): the connection to send the response
            to.
        """
        await connection.send_response(
            BodyResponse(status=405, body=b"Method Not Allowed")
        )

    async def __call__(self, connection: HttpConnection) -> None:
        """Pass the connection to the appropriate endpoint.

        Sends a 500 HTTP response if an exception is raised when receiving or
        processesing the request.

        Args:
            connection (HttpConnection): a :class:`Connection` instance with
            the connection information.

        Raises:
            Exception: re-raises any exception that is raised when receiving or
            processesing the request.
        """
        await super().__call__(connection)

        try:
            endpoint = await self.get_endpoint(connection.method.lower())
        except AttributeError:
            await self.send_not_implemented(connection)
            raise

        try:
            request = await connection.receive_request()
            await endpoint(connection, request)
        except Exception:
            await self.send_internal_server_error(connection)
            raise


class WebSocketRoute(Route):
    """A WebSocket route.

    Props:
        protocol (str): the protocol for this route. Defaults to websocket.
    """

    protocol: str = "websocket"

    async def connect(
        self, connection: WebSocketConnection, request: Request
    ) -> None:
        """Endpoint for a connect request type.

        Override to implement this endpoint.

        Args:
            connection (WebSocketConnection): a :class:`Connection` instance
            with the connection information.
            request (Request): the received request.
        """
        await connection.send_response(AcceptResponse())

    async def receive(
        self, connection: WebSocketConnection, request: Request
    ) -> None:
        """Endpoint for a receive request type.

        Override to implement this endpoint.

        Args:
            connection (WebSocketConnection): a :class:`Connection` instance
            with the connection information.
            request (Request): the received request.
        """
        pass

    async def disconnect(
        self, connection: WebSocketConnection, request: Request
    ) -> None:
        """Endpoint for a disconnect request type.

        Override to implement this endpoint.

        Args:
            connection (WebSocketConnection): a :class:`Connection` instance
            with the connection information.
            request (Request): the received request.
        """
        pass

    async def send_internal_error(
        self, connection: WebSocketConnection
    ) -> None:
        """Send a close response with a code of 1011 (Internal Error).

        Override to change how internal errors are handled.

        Args:
            connection (WebSocketConnection): the connection to send the
            reponse.
        """
        await connection.send_response(CloseResponse(code=1011))

    async def __call__(self, connection: WebSocketConnection) -> None:
        """Pass the connection to the appropriate endpoint.

        Sends a 1011 close response if an exception is raised when receiving or
        processesing the request.

        Args:
            connection (WebSocketConnection): a :class:`Connection` instance
            with the connection information.

        Raises:
            Exception: re-raises any exception that is raised when receiving or
            processesing the request.
        """
        await super().__call__(connection)

        try:
            request = await connection.receive_request()
            endpoint = await self.get_endpoint(request.type)
            await endpoint(connection, request)
        except Exception:
            await self.send_internal_error(connection)
            raise
