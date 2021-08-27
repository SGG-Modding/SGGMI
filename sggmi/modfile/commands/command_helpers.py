__all__ = ["instance", "stdpayload"]

from typing import Iterable, List, Mapping, Tuple
from . import Command


def lookup_command(
    tokens: Iterable[str], lookup_table: Mapping
) -> Tuple[Command, List[str]]:
    """Lookup command for given tokens in lookup_table

    Parameters
    ----------
    tokens : Iterable[str]
        tokens to find Command for
    lookup_table : Mapping
        nested lookup table of all Command subclasses

    Returns
    -------
    (Command, List[str])
        (command, parameters) for command that matches specified tokens

    Raises
    ------
    KeyError, RuntimeError
        if no path exists for specified tokens
    """
    target_command = None
    lookup_layer = lookup_table
    for idx, token in enumerate(tokens):
        target_command = lookup_layer[token]
        if isinstance(target_command, Command):
            return (target_command, tokens[idx + 1 :])

        lookup_layer = target_command

    raise RuntimeError("No command found for given tokens")
