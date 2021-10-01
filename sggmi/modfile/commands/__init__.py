from dataclasses import dataclass
from ... import util
from pathlib import Path, PurePath
from typing import Iterable, List, Mapping, Tuple


class Command:
    """modfile commands"""

    min_tokens = 0
    max_tokens = 999
    keywords = ()

    @classmethod
    def generate_lookup_table(cls):
        "Create lookup table of all subclassed commands by keywords"
        lookup_table = {}
        for command in cls.__subclasses__():
            # Start at root
            lookup_layer = lookup_table
            for idx, keyword in enumerate(command.keywords):
                # If this is the last token
                if (idx + 1) == len(command.keywords):
                    # Make sure we're not colliding with another command
                    if isinstance(lookup_layer.get(keyword), cls):
                        raise RuntimeError(
                            "Command keyword collision: "
                            f"{lookup_layer.get(keyword)} and {command}"
                        )
                    # Set command as end of path
                    lookup_layer[keyword] = command()
                else:
                    # Create another layer
                    lookup_layer[keyword] = {}
                    # Set as current layer
                    lookup_layer = lookup_layer[keyword]

        return lookup_table

    def __str__(self):
        return self.__class__.__name__

    def run(self, tokens, modfile_state, rel_dir, **kwargs):
        pass

    def valid_parameters(self, tokens: Iterable[str]) -> bool:
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
    deploy_path: PurePath
    payload: Payload
    priority: int
    key: str
    index: int

    def __str__(self):
        return f"ModEdit<{self.source} with {self.payload}>"


def instance(*args, **kwargs):
    return lambda cls: cls(*args, **kwargs)


def resolve_source(
    base_path: PurePath, source: str, resolved_sources: List[str], config: Mapping
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


def generate_mod_edit(
    command: "Command", tokens: Iterable[str], modfile_state, **kwargs
):
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


from .general import *
from .lua import *
from .xml import *
from .sjson import *

lookup_table = Command.generate_lookup_table()
