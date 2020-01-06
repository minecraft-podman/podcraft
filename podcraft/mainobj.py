import logging
import pathlib

import toml
from cached_property import cached_property

from .config import Config
from .state import State
from .images import build_server, build_manager
from .podman import client

CONFIG_FILE_NAME = "podcraft.toml"
STATE_FILE_NAME = ".tmp/state"

log = logging.getLogger(__name__)


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

    def __enter__(self):
        self.state.__enter__()
        return self

    def __exit__(self, type, value, tb):
        self.state.__exit__(type, value, tb)

    def _ensure_tmp(self):
        if not (self.root / ".tmp").exists():
            (self.root / ".tmp").mkdir(parents=True)

    @cached_property
    def state(self):
        """
        Config data from the TOML file
        """
        self._ensure_tmp()
        return State(self.root / STATE_FILE_NAME)

    def rebuild_everything(self):
        """
        Rebuild all of the stuff
        """
        # FIXME: Clean up old stuff
        # FIXME: Don't allow this to run when the pod is started
        with client() as pm:
            # 1. Build the images
            log.info("Building server")
            serv_img = build_server(pm, self.config.server_buildargs())
            self.state.save_image('server', serv_img)

            log.info("Building manager")
            man_img = build_manager(pm, self.config.manage_buildargs())
            self.state.save_image('manager', man_img)

            # 2. Assemble complete list of volumes and forwards
            ports = self.config.exposed_ports()
            volumes = {
                c: h if h else f".tmp/{c.replace('/', '_')}"
                for h, c in self.config.volumes()
            }
            # TODO: Add addon analysis

            # 3. Create volumes (storage directories)
            log.info("Checking volumes")
            self._ensure_tmp()
            for hostpath in volumes.values():
                hostpath = self.root / hostpath
                if hostpath.name == 'io.podman.socket':
                    # This gets created when podman is started
                    # XXX: I really hope we can bind-mount a non-existent inode
                    pass
                elif not hostpath.exists():
                    # FIXME: Better heuristic for what's files and directories
                    if '.' in hostpath.name:
                        hostpath.touch()
                    else:
                        hostpath.mkdir(parents=True)

            # 4. Create pod
            log.info("Creating pod")
            pod = pm.pods.create()  # FIXME: Forwards
            self.state.save_pod(pod)

            # 5. Write out server.properties
            log.warning("TODO: server.properties")

            # 6. Create containers
            log.info("Creating containers")
            log.warning("TODO: Container creation")
