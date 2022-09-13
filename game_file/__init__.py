import pathlib  # GameFileABC
import xml.etree.ElementTree as xml  # XmlGameFile
from abc import ABC, abstractmethod  # GameFileABC
from enum import Enum  # GameFileABC, XmlGameFile
from typing import Any, Optional, Union  # GameFileABC, XmlGameFile

from .exceptions import InvalidGameFile


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
