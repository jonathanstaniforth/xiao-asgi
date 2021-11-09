"""Object representation of a request.

The ``Request`` class can be used to hold a request's information.
"""
from dataclasses import dataclass
from typing import Any


@dataclass
class Request:
    """A dataclass representation of a request.

    Holds the information of a request in an object for easy access.

    Args:
        data (dict[str, Any]): the data passed with the request.
        protocol (str): the protocol used to send the request.
        type (str): the type of the request.

    Attributes:
        data (dict[str, Any]): the complete request.
        protocol (str): the protocol used to send the request.
        type (str): the request type, for example: request.

    Example:
        Creating a request::

            >>> request = Request(
            >>>     protocol="http",
            >>>     type="request",
            >>>     data={"body": b"", "more_body": False}
            >>> )
    """

    data: dict[str, Any]
    protocol: str
    type: str
