from pathlib import Path, PurePath

from mod_file import ModFile
from util import merge_dict
from . import Command


class Include(Command):
    keywords = ["Include"]
    targets: list

    def __init__(self, tokens, **kwargs):
        self.targets = [
            PurePath.joinpath(
                kwargs["rel_dir"], token.replace('"', "")
            )
            for token in tokens
        ]


    def run(self, *args, **kwargs):
        from mod_file import load_mod

        for target in self.targets:
            load_mod(target, **kwargs)


class LoadPriority(Command):
    max = 1
    keywords = ["Load", "Priority"]
    new_priority: float

    def __init__(self, tokens, **kwargs):
        self.new_priority = float(tokens[0])

    def run(self, modfile_state, *args, **kwargs):
        modfile_state["priority"] = self.new_priority


class To(Command):
    keywords = ["To"]
    target: list

    def __init__(self, tokens, **kwargs):
        self.target = [Path(token).as_posix() for token in tokens]

    def run(self, modfile_state, *args, **kwargs):
        if len(self.target) == 0:
            modfile_state.pop("target")
        else:
            modfile_state["target"] = self.target


class Deploy(Command):
    keywords = ["Deploy"]
    additional_deploys: dict

    def __init__(self, tokens, **kwargs):
        self.additional_deploys = tokens

    def run(self, **kwargs):
        to_deploy = kwargs["to_deploy"]

        for token in self.additional_deploys:
            mod_file = ModFile(token)
            if mod_file.is_subfile(kwargs["config"].mods_dir):
                to_deploy[token] = merge_dict(to_deploy.get(token), kwargs["config"])

            if mod_file.is_subdirectory(kwargs["config"].mods_dir):
                for entry in Path(token).iterdir():
                    entry = entry.resolve().as_posix()
                    to_deploy[entry] = merge_dict(
                        to_deploy.get(entry), kwargs["config"]
                    )


class Replace(Command):
    max = 1
    keywords = ["Replace"]

    # TODO: what is this
    def __init__(self):
        pass

    def run(self, tokens, modfile_state, **kwargs):
        generate_mod_edit(self, tokens, modfile_state, **kwargs)
