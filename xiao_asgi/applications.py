"""ASGI applications that setup the app."""
from collections.abc import Coroutine
from logging import getLogger

from xiao_asgi.connections import make_connection
from xiao_asgi.responses import BodyResponse
from xiao_asgi.routing import Route


class Xiao:
    """Creates an ASGI application.

    Attributes:
        logger (Logger): a :class`Logger` instance for logging application
        exceptions.
        routes (list[Route]): a :class:`Router` instance with the available
        routes.
    """

    def __init__(self, routes: list[Route]) -> None:
        """Establish the routes available to the application.

        Args:
            routes (list[Route]): a Router instance with the available routes.
        """
        self.logger = getLogger(name="xiao-asgi")
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
        connection = make_connection(scope, receive, send)

        for route in self._routes:
            if connection.url["path"] == route.path:
                try:
                    await route(connection)
                except Exception as exception:
                    self.logger.exception("EXCEPTION", exc_info=exception)
                finally:
                    return

        not_found_response = BodyResponse(status=404, body=b"Not Found")

        for message in not_found_response.render_messages():
            await send(message)
