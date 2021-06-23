"""ASGI applications that setup the app."""
from collections.abc import Coroutine

from xiao_asgi.routing import Router


class Xiao:
    """Creates an ASGI application."""

    def __init__(self, routes: Router) -> None:
        """Establish the routes available to the application.

        Args:
            routes (Router): a Router instance with the available routes.
        """
        self._routes = routes

    async def __call__(
        self, scope: dict, receive: Coroutine, send: Coroutine
    ) -> None:
        """Pass a request to the router for routing to an endpoint.

        Args:
            scope (dict): the request information.
            receive (Coroutine): the coroutine function to call to receive a
                client message.
            send (Coroutine): the coroutine function to call to send the
                response to the client.
        """
        await self._routes(scope, receive, send)
