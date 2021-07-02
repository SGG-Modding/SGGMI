
__all__ = ["instance","stdpayload"]

from ..modfile import ModEdit

def instance(*args,**kwargs):
    return lambda cls: cls(*args,**kwargs)

def stdpayload(command, tokens, info, n=None, **const):
    config = const["config"]
    filemods = const["filemods"]
    for scopepath in info["target"]:
        path = PurePath.joinpath(config.scope_dir, scopepath)
        if util.in_scope(path,config):
            args = [tokens[i::n] for i in range(n)]
            for i in range(len(args[-1])):
                sources = [
                    PurePath.joinpath(reldir, arg[i].replace('"', "")) for arg in args
                ]
                paths = []
                num = -1
                for source in sources:
                    if PurePath.joinpath(config.mods_dir, source).is_dir():
                        tpath = []
                        for entry in PurePath.joinpath(
                            config.mods_dir, source
                        ).iterdir():
                            if util.in_scope(
                                entry,
                                config.local_dir,
                                config.base_cache_dir,
                                config.edit_cache_dir,
                                config.scope_dir,
                            ):
                                tpath.append(entry.as_posix())
                        paths.append(tpath)
                        if num > len(tpath) or num < 0:
                            num = len(tpath)
                    elif util.in_scope(PurePath.joinpath(config.mods_dir, source), config):
                        paths.append(
                            PurePath.joinpath(config.mods_dir, source)
                            .resolve()
                            .as_posix()
                        )
                if paths:
                    for j in range(abs(num)):
                        sources = [x[j] if isinstance(x, list) else x for x in paths]
                        for src in sources:
                            todeploy[src] = util.merge_dict(todeploy.get(src), config)
                        f = lambda x: map(
                            lambda y: PurePath.joinpath(config.deploy_rel_dir, y), x
                        )
                        filemods[scopepath].append(
                            ModEdit(
                                "\n".join(
                                    [
                                        Path(source).resolve().as_posix()
                                        for source in sources
                                    ]
                                ),
                                tuple(f(sources)),
                                command.payload,
                                info["priority"],
                                scopepath,
                                len(filemods[scopepath])
                            )
                        )
