import pathlib
import toml

from cached_property import cached_property


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
            return toml.load(cf)
        # TODO: Apply schema/defaults

    @property
    def server_buildargs(self):
        """
        The buildargs for the server container
        """
        return self.config['server']

    def server_properties(self):
        """
        Compute the values of server.properties for use inside the pod.

        NOTE: This can vary from what the user specified
        """
