
__all__=["load"]

from . import modfile
from . import commands

def getcommands():
    return modfile.Command.mklookup( [ command for command in [ getattr(commands,name) for name in commands.__dir__() if name[0] != '_' ] if isinstance(command,modfile.Command) ] )

def load(filename, **const):
    return modfile.load(filename, commands=getcommands(), **const)
