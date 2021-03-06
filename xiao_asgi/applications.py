"""Foundation for an ASGI application.

The ``Xiao`` class provides a base from which ASGI application can be built
for consumption by an ASGI webserver.
"""
from collections.abc import Coroutine
from logging import getLogger

from xiao_asgi.connections import make_connection
from xiao_asgi.responses import PlainTextResponse
from xiao_asgi.routing import Route


class Xiao:
    """A base ASGI application.

    It holds a list of routes and handles routing a received request to the
    appropriate route when called.

    Attributes:
        logger (Logger): a ``Logger`` instance for logging application
            exceptions.
        routes (list[Route]): a ``Router`` instance with the available
            routes.
    """

    def __init__(self, routes: list[Route] = []) -> None:
        """Establish the application's available routes.

        Args:
            routes (list[Route], optional): the available routes. Defaults to
                an empty list.

        Example:
            Creating an application::

                >>> app = Xiao(routes=[
                >>>    Route("/"),
                >>>    Route("/about)
                >>> ])
        """
        self.logger = getLogger(name="xiao-asgi")
        self._routes = routes

    async def __call__(
        self, scope: dict, receive: Coroutine, send: Coroutine
    ) -> None:
        """Pass a request to the appropriate application route.

        Args:
            scope (dict): the request information.
            receive (Coroutine): the coroutine function to call to receive a
                client request.
            send (Coroutine): the coroutine function to call to send the
                response to the client.

        Example:
            Passing the application to a webserver so that requests can be
            routed, e.g. hypercorn::

                $ hypercorn main:app
        """
        connection = make_connection(scope, receive, send)

        for route in self._routes:
            if match := route.path_regex.match(scope["path"]):
                connection.path_parameters = match.groupdict()

                try:
                    await route(connection)
                except Exception as exception:
                    self.logger.exception("EXCEPTION", exc_info=exception)
                finally:
                    return

        await connection.send_response(
            PlainTextResponse(status=404, body=b"Not Found")
        )
