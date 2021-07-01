from command_helpers import instance, stdpayload
from ..modfile import Command, Payload

__all__ = ["Import","Top_Import"]

## LUA import statement adding
def addimport(base, path):
    with open(base, "a") as basefile:
        basefile.write(f"\nImport {path}")

#Import
@instance
class Import(Command):

    keywords = ("Import",)

    @instance()
    class payload(Payload):

        def act(target,source,*args,**kwargs):
            addimport(target,source)

    def run(self,tokens,info,**const):
        stdpayload(self,tokens,info,1,**const)

#Top Import
@instance
class Top_Import(Command):

    keywords = ("Top","Import")

    @instance()
    class payload(Payload):

        order = -1
        
        def act(target,source,*args,**kwargs):
            ##TO BE IMPLEMENTED
            pass

    def run(self,tokens,info,**const):
        stdpayload(self,tokens,info,1,**const)

