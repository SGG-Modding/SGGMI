__all__ = ["XML"]

from game_file import XmlGameFile
from mod_file import ModFile

from .abc import Command

RESERVED = {
    "replace": "_replace",
    "delete": "_delete",
}

# XML
class XML(Command):

    keywords = ("XML",)

    def __init__(self, tokens):
        self.mod_file = ModFile(tokens[0])

    def run(self, modfile_state, **const):
        game_file = XmlGameFile(modfile_state)
        game_file.update(self.mod_file.read())