# FILE/MOD LOADING

__all__ = ["load_mod", "Command", "Payload", "ModEdit"]

from pathlib import Path
import pathlib
from typing import List, Mapping
import re

from commands import Command, lookup_table
from commands.util import lookup_command
from .util import remove_comments
from util.file import is_subfile, is_subdirectory


DEFAULT_PRIORITY = 100

LINE_BREAK = ";"
DELIMITER = ","


class ParsingError(Exception):
    def __init__(self, tokens: List):
        self.tokens = tokens

    def __str__(self):
        return f"Failed to parse: '{' '.join(self.tokens)}'"


class ModFile:

    path: pathlib.Path
    parsed: list[tuple]

    def __init__(self, file_path):
        self.path = pathlib.Path(file_path)
        self.parsed = self.parse()

    def read(self):
        with open(self.path, "r", encoding="utf-8-sig") as modfile:
            return modfile.read()

    def parse(self) -> list[str]:
        """Split modfile data into a list of Commands and associated tokens

        Raises KeyError or RuntimeError if fails to parse
        """
        data = self.read()

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

        commands = []
        for tokens in lists_of_tokens:
            try:
                command, parameters = lookup_command(tokens, lookup_table)
                commands.append(command(parameters))
            except (KeyError, RuntimeError):
                raise ParsingError(tokens)

        return commands

    def process(self, rel_dir, **kwargs):
        """Open modfile, parse contents, and generate relevant ModEdits"""
        config = kwargs["config"]

        modfile_state = {
            "priority": DEFAULT_PRIORITY,
            "target": (
                config.profile.get("default_target", []) if config.profile else []
            ),
        }

        mod_edits = []
        for command in self.parsed.items():
            mod_edit = command.process(modfile_state, rel_dir=rel_dir, **kwargs)
            if mod_edit:
                mod_edits.append(mod_edit)

        return mod_edits

def load_mod(
    modfile: ModFile,
    **kwargs: Mapping,
):
    """Run modfile specified by modfile_path. If it's a directory, recurse."""
    config = kwargs["config"]

    if is_subdirectory(modfile.path, config.mods_dir):
        for entry in Path(modfile.path).iterdir():
            load_mod(entry, **kwargs)
        return

    if not is_subfile(modfile.path, config.mods_dir):
        raise Exception(f"{modfile.path} is not part of {config.mods_dir}!")

    rel_name = modfile.path.relative_to(config.mods_dir)
    if config.echo:
        print(f"- {rel_name.parent}", config=config)

    rel_dir = rel_name.parent
    try:
        modfile.execute(rel_dir, **kwargs)
    except ParsingError as exc:
        print(f"{rel_name} - {exc}")
    except IOError:
        return
