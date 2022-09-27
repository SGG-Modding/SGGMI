from collections import OrderedDict  # SjsonGameFile
import pathlib  # GameFileABC
import xml.etree.ElementTree as xml  # XmlGameFile
from abc import ABC, abstractmethod  # GameFileABC
from enum import Enum  # GameFileABC, XmlGameFile
from typing import Any, Optional, Union  # GameFileABC, XmlGameFile

from .exceptions import InvalidGameFile
from .util import prune
import sjson  # pip: SJSON


class GameFileABC(ABC):
    """Abstract base class for game files.

    Contains a default implementation for __init__
    """

    path: pathlib.Path
    contents: Optional[Any]
    RESERVED: Optional[Enum]

    def __init__(self, file_path: pathlib.Path):
        """Create a GameFile object and load contents


        Parameters
        ----------
        file_path : Path
            path to GameFile
        """
        self.path = file_path
        self.contents = self.read()

    @abstractmethod
    def get(self, key: Union[str, int], context: Optional[Any] = None) -> Any:
        """Get value of key from context. If context is not None, use GameFile contents

        Parameters
        ----------
        key : Union[str, int]
            value to read from context
        context: Optional[Any], default: None
            data to get key from. If None, use GameFile contents
        """
        ...

    @abstractmethod
    def read(self) -> Any:
        """Returns contents of GameFile

        Should raise game_file.exceptions.InvalidGameFile if the file is invalid
        """
        ...

    @abstractmethod
    def write(self):
        """Write self.contents back to self.file_path"""
        ...

    def format(self):
        """This function should be called after each write, for GameFiles that require
        specific formatting. By default this function will do nothing.
        """
        pass

    @abstractmethod
    def update(self, changes: Any, autowrite: bool = True):
        """Update self.contents with the specified changes

        Parameters
        ----------
        changes : Any
            changes to make to self.contents
        autowrite : bool, default: True
            If True, write changes back to file after updating
        """
        ...

    @classmethod
    def merge(cls, base_file_path: pathlib.Path, input_file_path: pathlib.Path):
        """Merge the contents of input_file into base_file

        Parameters
        ----------
        base_file : pathlib.Path
            file to merge changes into
        input_file : pathlib.Path
            file containing content to merge into base_file
        """
        base_file = cls(base_file_path)
        input_file = cls(input_file_path)

        base_file.update(input_file.contents)


class XmlGameFile(GameFileABC):
    """Class to read, write, and interact with XML game files"""

    class RESERVED(Enum):
        REPLACE = "_replace"
        DELETE = "_delete"

    def get(self, key, context: Optional[Any] = None):
        context = context or self.contents

        if isinstance(context, list):
            if isinstance(key, int):
                if key < len(context) and key >= 0:
                    return context[key]

        if isinstance(context, xml.ElementTree):
            root = context.getroot()
            if root:
                return root.get(key)

        if isinstance(context, xml.Element):
            return context.get(key)

        raise ValueError("Provided context is not valid.")

    def read(self):
        try:
            return xml.parse(self.file_path)
        except xml.ParseError as exc:
            raise InvalidGameFile() from exc

    def write(self, start=None):
        if not isinstance(self.content, xml.ElementTree):
            raise ValueError("Argument 'content' must be of type 'xml.ElementTree'")

        self.content.write(self.file_path)
        self.format()

    def format(self):
        # Indentation styling
        data = ""

        with open(self.file_path, "r") as input_file:
            i = 0
            for line in input_file:
                if len(line.replace("\t", "").replace(" ", "")) > 1:
                    q = True
                    p = ""
                    for s in line:
                        if s == '"':
                            q = not q
                        if p == "<" and q:
                            if s == "/":
                                i -= 1
                                data = data[:-1]
                            else:
                                i += 1
                            data += p
                        if s == ">" and p == "/" and q:
                            i -= 1
                        if p in (" ") or (s == ">" and p == '"') and q:
                            data += "\n" + "\t" * (i - (s == "/"))
                        if s not in (" ", "\t", "<") or not q:
                            data += s
                        p = s

        with open(self.file_path, "w") as output_file:
            output_file.write(data)

    def update(self, changes):
        if not changes:
            return

        if type(self.contents) == type(changes):
            if isinstance(changes, dict):
                for k, v in changes.items():
                    self.contents[k] = self.update(self.contents.get(k), v)
                return self.contents
            if isinstance(changes, xml.ElementTree):
                root = self.update(self.contents.getroot(), changes.getroot())
                if root:
                    self.contents._setroot(root)
                return self.contents
            elif isinstance(changes, xml.Element):
                mtags = dict()
                for v in changes:
                    if not mtags.get(v.tag, False):
                        mtags[v.tag] = True
                for tag in mtags:
                    mes = changes.findall(tag)
                    ies = self.contents.findall(tag)
                    for i, me in enumerate(mes):
                        ie = self.get(i, context=ies)
                        if not ie:
                            self.contents.append(me)
                            continue

                        if me.get(self.RESERVED.DELETE) not in {
                            None,
                            "0",
                            "false",
                            "False",
                        }:
                            self.contents.remove(ie)
                            continue

                        if me.get(self.RESERVED.REPLACE) not in {
                            None,
                            "0",
                            "false",
                            "False",
                        }:
                            ie.text = me.text
                            ie.tail = me.tail
                            ie.attrib = me.attrib
                            del ie.attrib[self.RESERVED.REPLACE]
                            continue
                        ie.text = self.update(ie.text, me.text)
                        ie.tail = self.update(ie.tail, me.tail)
                        ie.attrib = self.update(ie.attrib, me.attrib)
                        self.update(ie, me)
                return self.contents
            return changes

        return changes


class SjsonGameFile(GameFileABC):
    class RESERVED(Enum):
        SEQUENCE = "_sequence"
        APPEND = "_append"
        REPLACE = "_replace"
        DELETE = "_delete"

    def get(self, key, context):
        context = context or self.contents

        if isinstance(context, list):
            if isinstance(key, int):
                if key < len(context) and key >= 0:
                    return context[key]
            return None

        if isinstance(context, OrderedDict):
            return context.get(key)

        raise TypeError("Provided context is not valid.")

    def read(self):
        with open(self.file_path, "r") as input_file:
            try:
                contents = sjson.loads(input_file.read().replace("\\", "\\\\"))
                return prune(contents)
            except sjson.ParseException as exc:
                raise InvalidGameFile() from exc

    def write(self):
        if not isinstance(self.contents, OrderedDict):
            raise TypeError("'content' must be of type 'OrderedDict'")

        content = sjson.dumps(prune(self.content))

        with open(self.file_path, "w") as output_file:
            output_file.write(content)

        self.format()

    def format(self):

        with open(self.file_path, "r") as input_file:
            content = input_file.read()

        s = "{\n" + content + "}"

        # Indentation styling
        p = ""
        S = ""
        for c in s:
            if c in ("{", "[") and p in ("{", "["):
                S += "\n"
            if c in ("}", "]") and p in ("}", "]"):
                S += "\n"
            S += c
            if p in ("{", "[") and c not in ("{", "[", "\n"):
                S = S[:-1] + "\n" + S[-1]
            if c in ("}", "]") and p not in ("}", "]", "\n"):
                S = S[:-1] + "\n" + S[-1]
            p = c
        s = S.replace(", ", "\n").split("\n")
        i = 0
        L = []
        for S in s:
            for c in S:
                if c in ("}", "]"):
                    i = i - 1
            L.append("  " * i + S)
            for c in S:
                if c in ("{", "["):
                    i = i + 1
        s = "\n".join(L)

        with open(self.file_path, "w") as output_file:
            output_file.write(s)

    @classmethod
    def update_data(cls, base_data, new_data):
        if not new_data:
            return

        base_data = base_data

        if cls.get(cls.RESERVED.SEQUENCE, new_data):
            S = []
            for k, v in new_data.items():
                try:
                    d = int(k) - len(S)
                    if d >= 0:
                        S.extend([None] * (d + 1))
                    S[int(k)] = v
                except ValueError:
                    continue
            new_data = S

        if type(base_data) == type(new_data):
            if isinstance(new_data, list):
                for i in range(1, len(new_data)):
                    base_data.append(new_data[i])
                return base_data

            if cls.get(0, new_data) != cls.RESERVED.APPEND or isinstance(
                new_data, OrderedDict
            ):
                if isinstance(new_data, list):
                    if cls.get(0, new_data) == cls.RESERVED.DELETE:
                        return None
                    if cls.get(0, new_data) == cls.RESERVED.REPLACE:
                        del new_data[0]
                        return new_data
                    base_data.expand([None] * (len(new_data) - len(base_data)))
                    for k, v in enumerate(new_data):
                        cls.contents[k] = cls.update_data(cls.get(k, base_data), v)
                else:
                    if cls.get(cls.RESERVED.DELETE, new_data):
                        return None

                    if cls.get(cls.RESERVED.REPLACE, new_data):
                        del new_data[cls.RESERVED.REPLACE]
                        return new_data
                    for k, v in new_data.items():
                        base_data[k] = cls.update_data(cls.get(k, base_data), v)

                return base_data

        return new_data


class LuaGameFile(GameFileABC):
    def get(self, key, context):
        # This makes no sense for a Lua file
        pass

    def read(self):
        with open(self.file_path, "r") as input_file:
            return input_file.read()

    def write(self):
        with open(self.file_path, "w") as output_file:
            output_file.write(self.contents)

    def add_import(self, mod_path):
        self.contents.append(f'\nImport "{mod_path}"')
