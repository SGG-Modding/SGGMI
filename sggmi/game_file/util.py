from collections import OrderedDict
from typing import TypeVar

T = TypeVar("T")

def prune(data: T) -> T:
    """Create a copy of the provided data with any keys where the value
    is None removed recursively. If an object other than a list, dict, or
    OrderedDict is passed, the object will just be returned.

    Parameters
    ----------
    data : T
        data to prune

    Returns
    ------
    T
        A copy of the provided data with all None values removed
    """
    if isinstance(data, OrderedDict):
        return OrderedDict(
            (key, prune(value))
            for key, value in data.items()
            if value is not None
        )

    if isinstance(data, dict):
        return {
            key: prune(value)
            for key, value in data.items()
            if value is not None
        }

    if isinstance(data, list):
        return [prune(item) for item in data if item is not None]

    raise TypeError("Called prune on an invalid type!")
