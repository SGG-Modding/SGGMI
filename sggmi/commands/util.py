from pathlib import PurePath
from typing import Iterable, Mapping
from . import Command

def lookup_command(
    tokens: Iterable[str], lookup_table: Mapping
) -> tuple["Command", list[str]]:
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

def resolve_source(
    base_path: PurePath, source: str, resolved_sources: list[str], config: Mapping
):
    """
    Recursively resolve `source` with relation to `base_path` and add to `resolved_sources`
    """
    full_source_path = base_path / source.replace('"', "")

    if not util.in_scope(full_source_path, config):
        return

    if full_source_path.is_dir():
        for entry in full_source_path.iterdir():
            resolve_source(
                full_source_path, PurePath(entry).name, resolved_sources, config
            )
    else:
        resolved_sources.append(full_source_path.resolve().as_posix())
