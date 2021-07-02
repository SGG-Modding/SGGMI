from . import instance, stdpayload
from ..modfile import load, Command, Payload
from pathlib import Path, PurePath

__all__ = ["Include","LoadPriority","To","Deploy","Replace"]

#Include
@instance()
class Include(Command):

    keywords = ("Include",)

    def run(self,tokens,info,**const):
        for s in tokens:
            load(PurePath.joinpath(const["reldir"], s.replace('"', "")), **const)

#Load Priority
@instance()
class LoadPriority(Command):

    max = 1
    keywords = ("Load","Priority")

    def run(self,tokens,info,**const):
        info["priority"] = float(tokens[0])

#To
@instance()
class To(Command):

    keywords = ("To",)

    def run(self,tokens,info,**const):
        to = [Path(s).as_posix() for s in tokens]
        if len(to) == 0:
            info.pop("target")
        else:
            info["target"] = to

#Deploy
@instance()
class Deploy(Command):

    keywords = ("Deploy",)

    def run(self,tokens,info,**const):
        for token in tokens:
            check = util.is_subfile(s, const["config"].mods_dir)
            if check:
                todeploy[s] = util.merge_dict(todeploy.get(s), const["config"])
            elif check.message == "SubDir":
                for entry in Path(s).iterdir():
                    S = entry.resolve().as_posix()
                    todeploy[S] = util.merge_dict(todeploy.get(S), const["config"])

#Replace
@instance()
class Replace(Command):

    max = 1
    keywords = ("Replace",)

    @instance()
    class payload(Payload):

        def act(self,target,source,*args,**kwargs):
            ##TO BE IMPLEMENTED
            pass

    def run(self,tokens,info,**const):
        stdpayload(self,tokens,info,1,**const)
        
