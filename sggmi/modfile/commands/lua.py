from pathlib import PurePath
from . import instance, generate_mod_edit, Command, Payload

__all__ = ["Import", "TopImport"]

## LUA import statement adding
def addimport(base: PurePath, path: str):
    with open(base, "a") as base_file:
        base_file.write(f'\nImport "{PurePath(path).as_posix()}"')


# Import
@instance()
class Import(Command):

    keywords = ("Import",)

    @instance()
    class payload(Payload):
        def act(self, target, source, *args, **kwargs):
            addimport(target, source)

    def run(self, tokens, modfile_state, **kwargs):
        generate_mod_edit(self, tokens, modfile_state, **kwargs)


# Top Import
@instance()
class TopImport(Command):

    keywords = ("Top", "Import")

    @instance()
    class payload(Payload):

        order = -1

        def act(self, target, source, *args, **kwargs):
            ##TO BE IMPLEMENTED
            pass

    def run(self, tokens, modfile_state, **const):
        generate_mod_edit(self, tokens, modfile_state, **const)
