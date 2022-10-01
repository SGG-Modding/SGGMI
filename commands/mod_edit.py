from pathlib import PurePath
from typing import Iterable, Type

from game_file.abc import GameFile

from .abc import Command
import util


class ModEdit:
    """Object defining all necessary information to run a command"""

    command: Command  # What action are we performing?
    mod_file: GameFile  # What mod file is involved?
    target_file: GameFile  # What game file is involved?
    priority: float  # What priority does this action have?

    def __init__(
        self,
        command: "Type[Command]",
        mod_file_path: PurePath,
        target_path: PurePath,
        mod_file_type: GameFile,
        priority: float,
        **kwargs,
    ):
        """Generate a ModEdit for given Command"""
        config = kwargs["config"]

        full_target_path = PurePath.joinpath(config.scope_dir, target_path)
        if not util.file.in_scope(full_target_path, config):
            raise Exception(f"{target_path} is not in scope!")

        resolved_deploy_path = config.deploy_dir / PurePath(mod_file_path).relative_to(
            config.mods_dir
        )

        self.command = command
        self.mod_file = mod_file_type(resolved_deploy_path)
        self.target_file = mod_file_type(target_path)
        self.priority = priority

    def __str__(self):
        return f"ModEdit<{self.target_file} with {self.mod_file}>"

    def execute(self):
        self.command.execute(self)
