from game_file import LuaGameFile
from mod_file import ModFile

from .abc import Command

__all__ = ["Import", "TopImport"]

# Import
class Import(Command):

    keywords = ["Import"]

    mod_file: ModFile
    target: LuaGameFile

    def __init__(self, tokens):
        self.mod_file = ModFile(tokens[0])

    def run(self, modfile_state, **kwargs):
        self.target.add_import(self.mod_file)


# Top Import
class TopImport(Command):

    keywords = ["Top", "Import"]

    def act(self, target, source, *args, **kwargs):
        ##TO BE IMPLEMENTED
        pass

    def run(self, tokens, modfile_state, **const):
        generate_mod_edit(self, tokens, modfile_state, **const)
