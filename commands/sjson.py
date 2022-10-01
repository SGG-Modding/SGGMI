__all__ = ["SJSON"]

from .abc import Command

# SJSON
class SJSON(Command):

    keywords = ("SJSON",)

    def __init__(self, tokens, *args, **kwargs):
        self.mod_file = tokens[0]

    def run(self, modfile_state, **const):
        generate_mod_edit(self, tokens, modfile_state, **const)
