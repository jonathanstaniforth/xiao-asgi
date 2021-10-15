"""Classes to handle routing requests to endpoints and sending responses."""
from asyncio import to_thread
from typing import Any, Callable, Coroutine
from functools import partial
from inspect import iscoroutinefunction

from xiao_asgi.requests import Request


def is_coroutine(obj: Any) -> bool:
    """Return whether the object is a coroutine function.

    Args:
        obj (Any): object to check.

    Returns:
        bool: ``True`` if the object is a coroutine function,
            ``False`` otherwise.
    """
    while isinstance(obj, partial):
        obj = obj.func
    return iscoroutinefunction(obj)


class Route:
    """A HTTP route with an endpoint."""

    def __init__(
        self,
        path: str,
        endpoint: Callable[..., Response],
        methods: list[str] = ["GET"],
    ) -> None:
        """Establish the route and construct the endpoint.

        Args:
            path (str): the endpoint's path.
            endpoint (Callable): callback function to call when handling a
                request.
            methods (str, optional): the endpoint's HTTP method.
                Defaults to "GET".
        """
        self.endpoint = self._construct(endpoint)
        self.methods = methods
        self.path = path

    @staticmethod
    def _construct(func: Callable[[Request], Any]) -> Coroutine:
        """Construct a callable endpoint on receipt of a request.

        A synchronous ``func`` will be executed in a separate thread.

        Args:
            func (Callable): endpoint to construct to a callable async
                endpoint.

        Returns:
            Coroutine: callable async endpoint.
        """
        coroutine = is_coroutine(func)

        async def endpoint(
            scope: dict, receive: Coroutine, send: Coroutine
        ) -> None:
            request = Request(scope, receive=receive, send=send)

            if coroutine:
                response = await func(request)
            else:
                response = await to_thread(func, request)

            await response(send)

        return endpoint

    async def handle(
        self, scope: dict, receive: Coroutine, send: Coroutine
    ) -> None:
        """Handle processing a request.

        Args:
            scope (dict): the request information.
            receive (Coroutine): the coroutine function to call to receive a
                client message.
            send (Coroutine): the coroutine function to call to send the
                response to the client.
        """
        if scope["method"] not in self.methods:
            response = PlainTextResponse("Method Not Allowed", status_code=405)
            await response(send)
        else:
            await self.endpoint(scope, receive, send)


class Router:
    """Handle routing requests to the appropriate endpoint."""

    def __init__(self, routes: list[Route]) -> None:
        """Establish the list of routes available to the router.

        Args:
            routes (list[Route]): list of available routes.
        """
        self.routes = routes

    async def __call__(
        self, scope: dict, receive: Coroutine, send: Coroutine
    ) -> None:
        """Route a request to an endpoint.

        Args:
            scope (dict): the request information.
            receive (Coroutine): the coroutine function to call to receive a
                client message.
            send (Coroutine): the coroutine function to call to send the
                response to the client.
        """
        if scope["type"] != "http":
            response = PlainTextResponse("Not Found", status_code=404)
            await response(send)
            return

        for route in self.routes:

            if scope["path"] == route.path:
                await route.handle(scope, receive, send)
                return

        response = PlainTextResponse("Not Found", status_code=404)
        await response(send)
