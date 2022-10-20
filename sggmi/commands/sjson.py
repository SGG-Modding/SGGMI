from game_file import SjsonGameFile

from .abc import ExecutableCommand
from .mod_edit import ModEdit


class SJSON(ExecutableCommand):

    keywords = ["SJSON"]

    def __init__(self, tokens, *args, **kwargs):
        self.mod_file = tokens[0]

    def process(self, modfile_state, **kwargs):
        return ModEdit(
            type(self),
            self.mod_file,
            modfile_state["target"],
            SjsonGameFile,
            modfile_state["priority"],
            **kwargs,
        )

    def execute(self, mod_edit: ModEdit, **kwargs):
        mod_edit.target_file.update(mod_edit.mod_file)
