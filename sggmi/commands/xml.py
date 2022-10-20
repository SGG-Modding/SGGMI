from game_file import XmlGameFile
from mod_file import ModFile

from .abc import ExecutableCommand
from .mod_edit import ModEdit


class XML(ExecutableCommand):

    keywords = ["XML"]

    def __init__(self, tokens):
        self.mod_file = ModFile(tokens[0])

    def process(self, modfile_state, **kwargs):
        return ModEdit(
            type(self),
            self.mod_file,
            modfile_state["target"],
            XmlGameFile,
            modfile_state["priority"],
            **kwargs,
        )

    def execute(self, mod_edit: ModEdit, **kwargs):
        mod_edit.target_file.update(self.mod_file.read())
