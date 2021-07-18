from xiao_asgi.requests import Request


class TestRequest:
    """Tests the :class:`Request` class."""

    def test_create_instance(self):
        request = Request(
            data={
                "type": "http.request",
                "body": b"test request",
                "more_body": False,
            },
            protocol="http",
            type="request",
        )

        assert request.data == {
            "type": "http.request",
            "body": b"test request",
            "more_body": False,
        }
        assert request.protocol == "http"
        assert request.type == "request"
