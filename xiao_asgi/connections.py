from abc import ABC, abstractmethod, abstractproperty
from collections.abc import Coroutine
from typing import AsyncIterable

from xiao_asgi.send_events.interfaces import SendEventInterface


class IncorrectConnectionType(Exception):
    pass


class ConnectionDisconnected(Exception):
    pass


class ConnectionInterface(ABC):
    protocol: str

    def __init__(
        self,
        scope: dict,
        receive: Coroutine[dict, None, None],
        send: Coroutine[dict, None, None],
    ):
        self.scope = scope
        self.receive = receive
        self.send = send

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
                "scheme": self.scope.get("scheme"),
                "server": self.scope.get("server"),
                "root_path": self.scope.get("root_path"),
                "path": self.scope.get("path"),
                "query_string": self.scope.get("query_string"),
            }

        return self._url

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
                for key, value in self.scope.get("headers", [])
            }

        return self._headers

    async def receive_event(self) -> dict:
        message = await self.receive()

        if not message["type"].startswith(self.protocol):
            raise IncorrectConnectionType()

        return message

    async def send_event(self, response: SendEventInterface) -> None:
        rendered_response = response.render()

        if not rendered_response["type"].startswith(self.protocol):
            raise IncorrectConnectionType()

        await self.send(rendered_response)


class HttpConnection(ConnectionInterface):
    protocol: str = "http"

    async def stream(self) -> bytes:
        body = b""

        async for chunk in self.receive_event():
            body += chunk["body"]

            if not chunk["more_body"]:
                break

        return body


class WebSocketConnection(ConnectionInterface):
    protocol: str = "websocket"
