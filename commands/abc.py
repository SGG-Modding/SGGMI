from abc import ABC, abstractmethod  # Command
from typing import Iterable  # Command

class Command(ABC):
    """Class holding defined Mod actions"""

    min_tokens = 0
    max_tokens = 999
    keywords: tuple

    @classmethod
    def generate_lookup_table(cls):
        "Create lookup table of all subclassed commands by keywords"
        lookup_table = {}
        for command in cls.__subclasses__():
            # Start at root
            lookup_layer = lookup_table
            for idx, keyword in enumerate(command.keywords):
                # If this is the last token
                if (idx + 1) == len(command.keywords):
                    # Make sure we're not colliding with another command
                    if issubclass(lookup_layer.get(keyword), cls):
                        raise RuntimeError(
                            "Command keyword collision: "
                            f"{lookup_layer.get(keyword)} and {command}"
                        )
                    # Set command as end of path
                    lookup_layer[keyword] = command
                else:
                    # Create another layer
                    lookup_layer[keyword] = {}
                    # Set as current layer
                    lookup_layer = lookup_layer[keyword]

        return lookup_table

    @abstractmethod
    def __init__(self, tokens):
        ...

    def __str__(self):
        return self.__class__.__name__

    @abstractmethod
    def run(self, modfile_state, **kwargs):
        ...

    def valid_parameters(self, tokens: Iterable[str]) -> bool:
        """Check whether tokens match the amount valid for command"""
        return self.min_tokens <= len(tokens) <= self.max_tokens