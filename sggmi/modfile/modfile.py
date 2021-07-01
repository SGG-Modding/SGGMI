# FILE/MOD LOADING

__all__=["load","Command","Payload","ModEdit"]

from collections import defaultdict

mlcom_start = "-:"
mlcom_end = ":-"
comment = "::"
linebreak = ";"
delimiter = ","

DEFAULT_PRIORITY = 100

class Command:
    """ modfile commands """

    min = 0
    max = None
    keywords = (,)

    @classmethod
    def mklookup(cls, commands, i=0):
        "make recursive lookup of commands by keywords"
        layer = defaultdict([])
        for command in commands:
            layer[command.keywords[i]].append(command)
        lookup = {}
        for keyword, commands in layer.items():
            shallow = None
            deep = []
            for command in commands:
                if len(command.keywords)>i:
                    deep.append(command)
                elif shallow is not None:
                    raise RuntimeError(f"More than one command defined for the same keywords: {shallow.keywords}")
                else:
                    shallow = command
            lookup[keyword] = (shallow,cls.mklookup(deep,i+1))
        return lookup

    def run(self,tokens,info,**const):
        pass

class Payload:
    """ mod edit payload mode """

    order = 1
    def act(target,source,*args,**kwargs):
        pass

from dataclasses import dataclass
from typing import Tuple

@dataclass
class ModEdit:
    """ mod edit data """
    source: str
    args: Tuple[str]
    payload: Payload
    priority: int
    key: str
    index: int

def splitlines(body):
    glines = map(lambda s: s.strip().split('"'), body.split("\n"))
    lines = []
    li = -1
    mlcom = False

    def gp(group, lines, li, mlcom, even):
        if mlcom:
            tgroup = group.split(mlcom_end, 1)
            if len(tgroup) == 1:  # still commented, carry on
                even = not even
                return (lines, li, mlcom, even)
            else:  # comment ends, if a quote, even is disrupted
                even = False
                mlcom = False
                group = tgroup[1]
        if even:
            lines[li] += '"' + group + '"'
        else:
            tgroup = group.split(comment, 1)
            tline = tgroup[0].split(mlcom_start, 1)
            tgroup = tline[0].split(linebreak)
            lines[li] += tgroup[0]  # uncommented line
            for g in tgroup[1:]:  # new uncommented lines
                lines.append(g)
                li += 1
            if len(tline) > 1:  # comment begins
                mlcom = True
                lines, li, mlcom, even = gp(tline[1], lines, li, mlcom, even)
        return (lines, li, mlcom, even)

    for groups in glines:
        even = False
        li += 1
        lines.append("")
        for group in groups:
            lines, li, mlcom, even = gp(group, lines, li, mlcom, even)
            even = not even
    return lines


def tokenise(line):
    groups = line.strip().split('"')
    for i, group in enumerate(groups):
        if i % 2:
            groups[i] = [group]
        else:
            groups[i] = group.replace(" ", delimiter)
            groups[i] = groups[i].split(delimiter)
    tokens = []
    for group in groups:
        for x in group:
            if x != "":
                tokens.append(x)
    return tokens


def checkcommand(tokens, command):
    if command is not None:
        n = len(tokens)-1
        if command.min <= n and (command.max is None or n<=command.max):
            return True
    return False


def load(filename, info=None, **const):
    config = const["config"]
    
    if util.is_subfile(filename, config.mods_dir).message == "SubDir":
        for entry in Path(filename).iterdir():
            load(entry, **const)
        return

    if info is None:
        info = {}
        info.setdefault("priority",DEFAULT_PRIORITY)
        info.setdefault("target",config.chosen_profile.default_target if config.chosen_profile else [])

    rel_name = filename.relative_to(config.mods_dir)
    try:
        file = alt_open(filename, "r")
    except IOError:
        return

    if config.echo:
        alt_print(rel_name, config=config)

    reldir = rel_name.parent
    
    with file:
        for line in splitlines(file.read()):
            tokens = tokenise(line)
            commands = const["commands"]
            
            while commands and len(tokens) > 0:
                command, commands = commands[tokens[0]]
                if checkcommand(tokens, command):
                    tokens.pop(0)
                    command.run(tokens,info,**const)
                    break
    
