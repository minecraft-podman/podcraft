import pathlib
import toml

from cached_property import cached_property

from .config import Config


CONFIG_FILE_NAME = "podcraft.toml"


class NoProjectError(Exception):
    """
    No server config found at the given directory.
    """


class Podcraft:
    """
    Main access object
    """

    def __init__(self, root):
        self.root = pathlib.Path(root).absolute()

    @classmethod
    def find_project(cls, start):
        start = pathlib.Path(start).absolute()
        for p in [start] + list(start.parents):
            if (p / CONFIG_FILE_NAME).exists():
                return cls(p)
        else:
            raise NoProjectError

    @cached_property
    def config(self):
        """
        Config data from the TOML file
        """
        with (self.root / CONFIG_FILE_NAME).open('rt') as cf:
            return Config(toml.load(cf))
        # TODO: Apply schema/defaults
