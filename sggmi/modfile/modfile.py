# FILE/MOD LOADING

__all__=["load"]

modfile_mlcom_start = "-:"
modfile_mlcom_end = ":-"
modfile_comment = "::"
modfile_linebreak = ";"
modfile_delimiter = ","

KWRD_to = ["To"]
KWRD_loadpriority = ["Load","Priority"]
KWRD_include = ["Include"]
KWRD_deploy = ["Deploy"]
KWRD_import = ["Import"]

def startswith(tokens, keyword, n):
    m = len(tokens) - len(keyword)
    if m >= n and tokens[: len(keyword)] == keyword :
        return m
    return 0

def loadcommand(reldir, tokens, to, n, mode, todeploy, cfg={}, **load):
    for scopepath in to:
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
                            todeploy[src] = util.merge_dict(todeploy.get(src), cfg)
                        f = lambda x: map(
                            lambda y: PurePath.joinpath(config.deploy_rel_dir, y), x
                        )
                        codes[scopepath].append(
                            Mod(
                                "\n".join(
                                    [
                                        Path(source).resolve().as_posix()
                                        for source in sources
                                    ]
                                ),
                                tuple(f(sources)),
                                mode,
                                scopepath,
                                len(codes[scopepath]),
                                **load,
                            )
                        )

def load(filename, todeploy, config):
    if util.is_subfile(filename, config.mods_dir).message == "SubDir":
        for entry in Path(filename).iterdir():
            modfile_load(entry, config)
        return

    rel_name = filename.relative_to(config.mods_dir)
    try:
        file = alt_open(filename, "r")
    except IOError:
        return

    if config.echo:
        alt_print(rel_name, config=config)

    default_target = config.chosen_profile.default_target if config.chosen_profile else []

    reldir = rel_name.parent
    p = DEFAULT_PRIORITY
    to = default_target
    cfg = {}

    with file:
        for line in modfile_splitlines(file.read()):
            tokens = modfile_tokenise(line)
            if len(tokens) == 0:
                continue

            elif modfile_startswith(tokens, KWRD_to, 0):
                to = [Path(s).as_posix() for s in tokens[1:]]
                if len(to) == 0:
                    to = default_target

            elif modfile_startswith(tokens, KWRD_loadpriority, 0) <= 1:
                try:
                    p = int(tokens[len(KWRD_loadpriority)])
                except IndexError:
                    p = DEFAULT_PRIORITY

            if modfile_startswith(tokens, KWRD_include, 1):
                for s in tokens[1:]:
                    modfile_load(PurePath.joinpath(reldir, s.replace('"', "")), todeploy, config)

            elif modfile_startswith(tokens, KWRD_deploy, 1):
                for token in tokens[1:]:
                    check = util.is_subfile(s, modsdir)
                    if check:
                        todeploy[s] = util.merge_dict(todeploy.get(s), cfg)
                    elif check.message == "SubDir":
                        for entry in Path(s).iterdir():
                            S = entry.resolve().as_posix()
                            todeploy[S] = util.merge_dict(todeploy.get(S), cfg)

            elif modfile_startswith(tokens, KWRD_import, 1):
                modfile_loadcommand(
                    reldir,
                    tokens[len(KWRD_import) :],
                    to,
                    1,
                    "lua",
                    todeploy,
                    cfg,
                    priority=p,
                )
            elif modfile_startswith(tokens, sggmi_xml.KEYWORD, 1):
                modfile_loadcommand(
                    reldir,
                    tokens[len(sggmi_xml.KEYWORD) :],
                    to,
                    1,
                    "xml",
                    todeploy,
                    cfg,
                    priority=p,
                )
            elif modfile_startswith(tokens, sggmi_sjson.KEYWORD, 1):
                if sjson:
                    modfile_loadcommand(
                        reldir,
                        tokens[len(sggmi_sjson.KEYWORD) :],
                        to,
                        1,
                        "sjson",
                        todeploy,
                        cfg,
                        priority=p,
                    )

                else:
                    alt_warn("SJSON module not found! Skipped command: " + line)
