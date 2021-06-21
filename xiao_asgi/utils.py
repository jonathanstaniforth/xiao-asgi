"""Helper functions to handle miscellaneous tasks."""
from functools import partial
from inspect import iscoroutinefunction
from typing import Any


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
