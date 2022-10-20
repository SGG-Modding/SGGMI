from pathlib import PurePath

from mod_file import load_mod

from .abc import Command


class Include(Command):
    keywords = ["Include"]
    targets: list

    def __init__(self, tokens, **kwargs):
        self.targets = [
            PurePath.joinpath(kwargs["rel_dir"], token.replace('"', ""))
            for token in tokens
        ]

    def process(self, modfile_state, *args, **kwargs):
        for target in self.targets:
            load_mod(target, **kwargs)


class LoadPriority(Command):
    max = 1
    keywords = ["Load", "Priority"]
    new_priority: float

    def __init__(self, tokens, **kwargs):
        self.new_priority = float(tokens[0])

    def process(self, modfile_state, *args, **kwargs):
        modfile_state["priority"] = self.new_priority


class To(Command):
    keywords = ["To"]
    target: list

    def __init__(self, tokens, **kwargs):
        self.target = [PurePath(token).as_posix() for token in tokens]

    def process(self, modfile_state, *args, **kwargs):
        modfile_state["target"] = self.target
