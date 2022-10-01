from dataclasses import dataclass
from pathlib import Path, PurePath
from typing import Iterable, Type

from .abc import Command
import util

__all__ = ["Include", "LoadPriority", "To", "Deploy", "Replace"]

class ModEdit:
    """Object defining all necessary information to run a command"""

    command: Command # What action are we performing?
    source: PurePath # What mod file is involved?
    deploy_path: PurePath # What game file is involved?
    tokens: Iterable # What was the modfile line that led to this action?
    priority: int # What priority does this action have?
    key: str
    index: int

    def __init__(self, command: "Type[Command]", tokens: Iterable[str], modfile_state, **kwargs):
        """Generate a command ModEdit for each token"""
        config = kwargs["config"]
        file_mods = kwargs["file_mods"]
        rel_dir = kwargs["rel_dir"]
        to_deploy = kwargs["to_deploy"]

        for target_path in modfile_state["target"]:
            full_target_path = PurePath.joinpath(config.scope_dir, target_path)
            if not util.in_scope(full_target_path, config):
                print(f"{target_path} is not in scope!")
                continue

            resolved_sources = []
            base_path = PurePath.joinpath(config.mods_dir, rel_dir)
            for source in tokens:
                resolve_source(base_path, source, resolved_sources, config)

            if not resolved_sources:
                continue

            for source in resolved_sources:
                to_deploy[source] = util.merge_dict(to_deploy.get(source), config)

                resolved_deploy_path = config.deploy_dir / Path(source).relative_to(
                    config.mods_dir
                )

                mod_edit = ModEdit(
                    source=Path(source).resolve().as_posix(),
                    deploy_path=resolved_deploy_path,
                    payload=command.payload,
                    priority=modfile_state["priority"],
                    key=target_path,
                    index=len(file_mods[target_path]),
                )

                file_mods[target_path].append(mod_edit)

    def __str__(self):
        return f"ModEdit<{self.source} with {self.payload}>"

    def execute(self):
        self.command.run(self.tokens)

from .lua import *
from .xml import *
from .sjson import *

lookup_table = Command.generate_lookup_table()
