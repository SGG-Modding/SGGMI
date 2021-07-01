
__all__=["load"]

from . import modfile
from . import commands

def getcommands():
    return Command.mklookup(( getattr(commands,name) for name in commands.__dir__() if name[0] != '_' ))

def load(filename, **const):
    return modfile.load(filename, commands=getcommands(), **const)
