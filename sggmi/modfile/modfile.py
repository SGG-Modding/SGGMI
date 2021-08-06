# FILE/MOD LOADING

__all__ = ["load_mod", "Command", "Payload", "ModEdit"]

from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from sggmi import util
from sggmi.util.io_util import alt_print
from typing import Any, Mapping, Tuple
import re

LINE_BREAK = ";"
DELIMITER = ","

DEFAULT_PRIORITY = 100


class Command:
    """modfile commands"""

    min_tokens = 0
    max_tokens = 999
    keywords = ()

    @classmethod
    def mklookup(cls, commands, i=0):
        "make recursive lookup of commands by keywords"
        layer = defaultdict(list)
        for command in commands:
            if len(command.keywords) > i:
                layer[command.keywords[i]].append(command)
        i += 1
        lookup = {}
        for keyword, commands in layer.items():
            shallow = None
            deep = []
            for command in commands:
                if len(command.keywords) > i:
                    deep.append(command)
                elif shallow is not None:
                    raise RuntimeError(
                        f"More than one command defined for the same keywords: {shallow.keywords}"
                    )
                else:
                    shallow = command
            lookup[keyword] = (shallow, cls.mklookup(tuple(deep), i))
        return lookup

    def run(self, tokens, info, rel_dir, **kwargs):
        pass

    def valid_tokens(self, tokens: list[str]) -> bool:
        """Check whether tokens match the amount valid for command"""
        return self.min_tokens <= len(tokens) <= self.max_tokens


class Payload:
    """mod edit payload mode"""

    order = 1

    def act(target, source, *args, **kwargs):
        pass


@dataclass
class ModEdit:
    """mod edit data"""

    source: str
    args: Tuple[str]
    payload: Payload
    priority: int
    key: str
    index: int


def parse_modfile(data: str) -> list[str]:
    """Split modfile data into a list of lines with comments and
    whitespace removed"""

    def remove_comments(segment: str) -> str:
        """
        Relies on caching to handle regex compiling. If performance suffers,
        convert to `re.compile` passed into the function, or in-line
        """
        segment = re.sub(r"-:.*:-", "", segment, flags=re.S)
        segment = re.sub(r"::.*", "", segment)

        return segment

    cleaned_modfile = []
    for idx, group in enumerate(data.split('"')):
        if idx % 2:  # We're inside quotes, remove newlines
            cleaned_modfile.append(group.replace("\n", ""))
        else:  # We're outside quotes, remove comments
            cleaned_modfile.append(remove_comments(group))

    cleaned_modfile = "".join(cleaned_modfile)

    # Split modfile lines into a list after replacing LINE_BREAK with \n
    modfile_lines = [
        line.strip()
        for line in cleaned_modfile.replace(LINE_BREAK, "\n").splitlines()
        if line.strip() != ""
    ]

    # simplify delimiters, then split
    return [
        [
            token.strip()
            for token in re.sub(f'[" "|{DELIMITER}]+', " ", line).split(" ")
            if token.strip() != ""
        ]
        for line in modfile_lines
    ]


def load_mod(
    modfile_path: Path,
    info: Mapping[str, Any] = None,
    **kwargs: Mapping[str, Any],
):
    """Run modfile specified by modfile_path. If it's a directory, recurse."""
    config = kwargs["config"]

    if util.is_subfile(modfile_path, config.mods_dir).message == "SubDir":
        for entry in Path(modfile_path).iterdir():
            load_mod(entry, **kwargs)
        return

    if info is None:
        info = {}

    info.setdefault("priority", DEFAULT_PRIORITY)
    info.setdefault(
        "target", config.chosen_profile.default_target if config.chosen_profile else []
    )

    rel_name = modfile_path.relative_to(config.mods_dir)
    if config.echo:
        util.alt_print(rel_name, config=config)

    rel_dir = rel_name.parent
    try:
        execute_modfile(modfile_path, info, rel_dir, **kwargs)
    except IOError:
        return


def execute_modfile(modfile_path, info, rel_dir, **kwargs):
    """Open modfile, parse contents, and execute commands"""
    with util.alt_open(modfile_path, "r") as modfile:
        lines_of_tokens = parse_modfile(modfile.read())
        commands = kwargs["commands"]
        if not commands:
            return

        for tokens in lines_of_tokens:
            try:
                command = commands[tokens[0]]
            except KeyError:
                alt_print(f"Failed to find command: {tokens[0]}")
                continue

            if not command.valid_tokens(tokens[1:]):
                alt_print(f"{command}: Invalid amount of tokens ({tokens})")
                continue

            command.run(tokens[1:], info, rel_dir=rel_dir, **kwargs)
            break
