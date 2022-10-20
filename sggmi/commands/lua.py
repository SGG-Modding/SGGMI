from game_file import LuaGameFile
from .abc import ExecutableCommand
from .mod_edit import ModEdit

# Import
class Import(ExecutableCommand):

    keywords = ["Import"]

    def __init__(self, tokens):
        self.mod_file = tokens[0]

    def process(self, modfile_state, **kwargs):
        return ModEdit(
            Import,
            self.mod_file,
            modfile_state["target"],
            LuaGameFile,
            modfile_state["priority"],
            **kwargs,
        )

    def execute(self, mod_edit: ModEdit):
        mod_edit.target_file.add_import(mod_edit.source_file)
