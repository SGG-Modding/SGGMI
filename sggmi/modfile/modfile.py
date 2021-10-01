# FILE/MOD LOADING

__all__ = ["load_mod", "Command", "Payload", "ModEdit"]

from pathlib import Path
from sggmi import util
from sggmi.util.io_util import alt_print
from typing import List, Mapping
import re

from sggmi.modfile import commands
from sggmi.modfile.commands import Command
from .commands.command_helpers import lookup_command


DEFAULT_PRIORITY = 100

LINE_BREAK = ";"
DELIMITER = ","


class ParsingError(Exception):
    def __init__(self, tokens: List):
        self.tokens = tokens

    def __str__(self):
        return f"Failed to parse: '{' '.join(self.tokens)}'"


def load_mod(
    modfile_path: Path,
    **kwargs: Mapping,
):
    """Run modfile specified by modfile_path. If it's a directory, recurse."""
    config = kwargs["config"]

    if util.is_subfile(modfile_path, config.mods_dir).message == "SubDir":
        for entry in Path(modfile_path).iterdir():
            load_mod(entry, **kwargs)
        return

    rel_name = modfile_path.relative_to(config.mods_dir)
    if config.echo:
        util.alt_print(f"- {rel_name.parent}", config=config)

    rel_dir = rel_name.parent
    try:
        execute_modfile(modfile_path, rel_dir, **kwargs)
    except ParsingError as exc:
        print(f"{rel_name} - {exc}")
    except IOError:
        return


def parse_modfile(data: str) -> List[str]:
    """Split modfile data into a list of Commands and associated tokens

    Removes comments and whitespace, and strips newlines from quote-enclosed strings

    Raises KeyError or RuntimeError if fails to parse
    """

    def remove_comments(segment: str) -> str:
        """
        Relies on caching to handle regex compiling. If performance suffers,
        convert to `re.compile` passed into the function, or in-line
        """
        segment = re.sub(r"-:.*:-", "", segment, flags=re.S)
        segment = re.sub(r"::.*", "", segment)

        return segment

    cleaned_modfile = []
    data = remove_comments(data)
    for idx, group in enumerate(data.split('"')):
        if idx % 2:  # We're inside quotes, remove newlines
            cleaned_modfile.append(group.replace("\n", ""))
        else:
            cleaned_modfile.append(group)

    cleaned_modfile = "".join(cleaned_modfile)

    # Split modfile lines into a list after replacing LINE_BREAK with \n
    modfile_lines = [
        line.strip()
        for line in cleaned_modfile.replace(LINE_BREAK, "\n").splitlines()
        if line.strip() != ""
    ]

    # simplify delimiters, then split
    lists_of_tokens = [
        [
            token.strip()
            for token in re.sub(f'[" "|{DELIMITER}]+', " ", line).split(" ")
            if token.strip() != ""
        ]
        for line in modfile_lines
    ]
    commands_and_parameters = []
    for tokens in lists_of_tokens:
        try:
            commands_and_parameters.append(
                lookup_command(tokens, commands.lookup_table)
            )
        except (KeyError, RuntimeError):
            raise ParsingError(tokens)

    return commands_and_parameters


def execute_modfile(modfile_path, rel_dir, **kwargs):
    """Open modfile, parse contents, and execute commands"""
    with util.alt_open(modfile_path, "r") as modfile:
        parsed_modfile = parse_modfile(modfile.read())

    config = kwargs["config"]

    modfile_state = {
        "priority": DEFAULT_PRIORITY,
        "target": (config.profile.get("default_target", []) if config.profile else []),
    }

    for command, parameters in parsed_modfile:
        if not command.valid_parameters(parameters):
            continue

        command.run(parameters, modfile_state, rel_dir=rel_dir, **kwargs)
