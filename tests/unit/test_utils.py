from functools import partial

from xiao_asgi.utils import is_coroutine


class TestIsCoroutine:
    def test_async_function(self):
        async def test():
            pass

        assert is_coroutine(test)

    def test_sync_function(self):
        def test():
            pass

        assert not is_coroutine(test)

    def test_async_partial(self):
        async def test():
            pass

        partial_object = partial(test)

        assert is_coroutine(partial_object)

    def test_sync_partial(self):
        def test():
            pass

        partial_object = partial(test)

        assert not is_coroutine(partial_object)
