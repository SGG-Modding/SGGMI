from . import Command, Payload, generate_mod_edit
from sggmi.util import is_subfile, merge_dict
from pathlib import Path, PurePath

__all__ = ["Include", "LoadPriority", "To", "Deploy", "Replace"]


class Include(Command):
    keywords = ["Include"]

    def run(self, tokens, *args, **kwargs):
        from sggmi.modfile.modfile import load_mod

        for token in tokens:
            include_target = PurePath.joinpath(
                kwargs["rel_dir"], token.replace('"', "")
            )
            load_mod(include_target, **kwargs)


class LoadPriority(Command):
    max = 1
    keywords = ["Load", "Priority"]

    def run(self, tokens, modfile_state, **kwargs):
        modfile_state["priority"] = float(tokens[0])


class To(Command):
    keywords = ["To"]

    def run(self, tokens, modfile_state, **kwargs):
        install_target = [Path(token).as_posix() for token in tokens]
        if len(install_target) == 0:
            modfile_state.pop("target")
        else:
            modfile_state["target"] = install_target


class Deploy(Command):
    keywords = ["Deploy"]

    def run(self, tokens, modfile_state, **kwargs):
        to_deploy = kwargs["to_deploy"]
        for token in tokens:
            check = is_subfile(token, kwargs["config"].mods_dir)
            if check:
                to_deploy[token] = merge_dict(to_deploy.get(token), kwargs["config"])
            elif check.message == "SubDir":
                for entry in Path(token).iterdir():
                    entry = entry.resolve().as_posix()
                    to_deploy[entry] = merge_dict(
                        to_deploy.get(entry), kwargs["config"]
                    )


class Replace(Command):
    max = 1
    keywords = ["Replace"]

    class payload(Payload):
        def act(self, target, source, *args, **kwargs):
            ##TO BE IMPLEMENTED
            pass

    def run(self, tokens, modfile_state, **kwargs):
        generate_mod_edit(self, tokens, modfile_state, **kwargs)
