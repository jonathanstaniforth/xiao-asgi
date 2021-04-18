"""The requests module can represent and process incoming client requests."""
from collections.abc import AsyncGenerator, Coroutine
from http.cookies import SimpleCookie
from json import loads
from typing import Any, Optional
from urllib.parse import parse_qs


class BodyStreamError(Exception):
    """Streaming request body error.

    An error occurred while trying to stream the body of a request.
    """

    pass


class Request:
    """A client request.

    Contains information about the request and methods to process the request.
    """

    def __init__(
        self,
        scope: dict,
        receive: Coroutine[dict, None, None],
        send: Coroutine,
    ) -> None:
        """
        Establish the Request instance.

        Args:
            scope (dict): request metadata.
            receive (Coroutine[dict, None, None]):
                incoming request body message.
            send (Coroutine): send a response to the client.
        """
        self._body = None
        self._body_streamed = False
        self._cookies = None
        self._form = None
        self._headers = None
        self._json = None
        self._query_params = None
        self._receive = receive
        self._send = send
        self._scope = scope
        self._url = None

    @property
    def client(self) -> tuple[Optional[str], Optional[str]]:
        """Return the client information.

        Returns:
            tuple[Optional[str], Optional[str]]:
                a tuple containing the host and port of the client.
        """
        return self._scope.get("client", (None, None))

    @property
    def cookies(self) -> SimpleCookie:
        """Return the request cookies.

        Returns:
            SimpleCookie:
                an instance of `SimpleCookie` containing the request cookies.
        """
        if self._cookies is None:
            self._cookies = SimpleCookie(self.headers.get("cookie"))

        return self._cookies

    @property
    def headers(self) -> dict[str, str]:
        """Return the request headers.

        The request headers are decoded using the 'latin-1' encoding.

        Returns:
            dict[str, str]: a dictionary of headers and their values.
        """
        if self._headers is None:
            self._headers = {
                key.decode("latin-1"): value.decode("latin-1")
                for key, value in self._scope.get("headers", [])
            }

        return self._headers

    @property
    def method(self) -> Optional[str]:
        """Return the request method.

        Returns:
            Optional[str]: the method.
        """
        return self._scope.get("method")

    @property
    def query_params(self) -> dict[str, list[str]]:
        """Return the query parameters of the request.

        Returns:
            dict[str, list[str]]: a dictionary containing the query params.
        """
        if self._query_params is None:
            self._query_params = parse_qs(self._scope.get("query_string", b""))

        return self._query_params

    @property
    def url(self) -> dict[str, str]:
        """Return the request URL.

        The URL is deconstructed into its separate parts:
        'scheme', 'server', 'path' and 'query_string'.

        Returns:
            dict[str, str]: the URL information.
        """
        if self._url is None:
            self._url = {
                "scheme": self._scope.get("scheme"),
                "server": self._scope.get("server"),
                "root_path": self._scope.get("root_path"),
                "path": self._scope.get("path"),
                "query_string": self._scope.get("query_string"),
            }

        return self._url

    async def body(self) -> bytes:
        """Stream the request body and store in bytes.

        Returns:
            bytes: the request body.
        """
        if self._body is None:
            self._body = b""

            async for chunk in self.stream_body():
                self._body += chunk

        return self._body

    async def json(self) -> Any:
        """Stream the request body and deserialise from JSON.

        Returns:
            Any: the request body as a Python object.
        """
        if self._json is None:
            self._json = loads(await self.body())

        return self._json

    async def stream_body(self) -> AsyncGenerator[bytes, None, None]:
        """Stream the request body.

        Raises:
            BodyStreamError: the request body has already been streamed.
            BodyStreamError: the client disconnects during streaming.

        Returns:
            AsyncGenerator[bytes, None, None]:
                generator for streaming the request body.

        Yields:
            Iterator[AsyncGenerator[bytes, None, None]]:
                the request body in chunks.
        """
        if self._body_streamed:
            raise BodyStreamError("Body already streamed")

        self._body_streamed = True

        while True:
            message = await self._receive()

            if message["type"] == "http.disconnect":
                raise BodyStreamError("Client disconnected")

            yield message.get("body")

            if not message.get("more_body", False):
                break
