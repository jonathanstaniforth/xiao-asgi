from unittest.mock import AsyncMock

from pytest import fixture, mark

from xiao_asgi.applications import Xiao
from xiao_asgi.routing import Route, Router


class TestXiao:
    @fixture
    def router(self):
        return Router(
            [
                Route("/", AsyncMock()),
                Route("/test", AsyncMock(), ["GET", "POST"]),
            ]
        )

    def test_create(self, router):
        app = Xiao(router)
        assert app._routes == router

    @mark.asyncio
    async def test_calling(self):
        scope = {}
        mock_receive = AsyncMock()
        mock_send = AsyncMock()
        mock_router = AsyncMock()

        app = Xiao(mock_router)
        await app(scope, mock_receive, mock_send)

        mock_router.assert_awaited_once_with(scope, mock_receive, mock_send)
