"""Client requests.

This module contains the :class:`Request` class which can be used to hold a
information received from a request.
"""
from dataclasses import dataclass
from typing import Any


@dataclass
class Request:
    """A representation of a client request.

    Args:
        data (dict[str, Any]): the complete request.
        protocol (str): the protocol used to send the request.
        type (str): the type of the request.

    Attributes:
        data (dict[str, Any]): the complete request.
        protocol (str): the protocol used to send the request.
        type (str): the type of the request.
    """

    data: dict[str, Any]
    protocol: str
    type: str
