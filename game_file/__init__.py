import pathlib  # GameFileABC
from abc import ABC, abstractmethod  # GameFileABC
from enum import Enum  # GameFileABC
from typing import Any, Optional, Union  # GameFileABC


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
