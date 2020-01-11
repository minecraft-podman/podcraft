import logging
import pathlib
import subprocess

import toml
from cached_property import cached_property
import podman.libs.errors

from .config import Config
from .state import State
from .images import build_server, build_manager,  get_volumes
from .podman import client
from .pods import create_pod
from .containers import create_container

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

    def cleanup(self):
        """
        Deletes all the podman resources.

        Does not delete volume data
        """
        log.info("Cleaning up")
        with client() as pm:
            for name in ('server', 'manager'):
                try:
                    log.debug(f"Getting {name} container")
                    c = self.state.get_container_object(name, client=pm)
                except KeyError:
                    pass
                except podman.libs.errors.ContainerNotFound:
                    log.debug("Stale state")
                    self.state.save_container(name, None)
                else:
                    try:
                        log.debug(f"Removing {name} container")
                        c.remove(force=True)
                    except Exception:
                        pass
                    self.state.save_container(name, None)

                try:
                    log.debug(f"Getting {name} image")
                    i = self.state.get_image_object(name, client=pm)
                except KeyError:
                    pass
                else:
                    try:
                        log.debug(f"Removing {name} image")
                        i.remove(force=True)
                    except Exception:
                        pass
                    self.state.save_image(name, None)

            log.debug("Getting pod")
            p = self.state.get_pod_object(client=pm)
            if p is not None:
                try:
                    log.debug(f"Removing pod")
                    p.remove(force=True)
                except Exception:
                    pass
                self.state.save_pod(None)

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
            strip_proto = lambda p: str(p).split('/', 1)[0]
            ports = [
                f'{strip_proto(outter)}:{inner}'
                for outter, (_, inner) in self.config.exposed_ports().items()
            ]
            volumes = {
                c: self.root / (h if h else f".tmp/{c.replace('/', '_')}")
                for h, c in self.config.volumes()
            }
            for img in (serv_img, man_img):
                ivols = get_volumes(img)
                for v in ivols:
                    if v not in volumes:
                        volumes[v] = f".tmp/{v.replace('/', '_')}"
            # TODO: Add addon analysis

            # 3. Create volumes (storage directories)
            log.info("Checking volumes")
            self._ensure_tmp()
            for hostpath in volumes.values():
                hostpath = self.root / hostpath
                if not hostpath.exists():
                    # FIXME: Better heuristic for what's files and directories
                    if '.' in hostpath.name:
                        if not hostpath.exists():
                            if hostpath.suffix == '.json':
                                hostpath.write_text('[]')
                            else:
                                hostpath.touch()
                    else:
                        hostpath.mkdir(parents=True)

            # 5. Write out server.properties
            (self.root / self.config.properties_file).write_text(
                '\n'.join(produce_properties(self.config.server_properties()))
            )

            # 4. Create pod
            log.info("Creating pod")
            pod = create_pod(pm, publish=ports)
            self.state.save_pod(pod)

            # 6. Create containers
            log.info("Creating containers")
            serv_con = create_container(serv_img, pod, volumes)
            self.state.save_container('server', serv_con)
            man_con = create_container(man_img, pod, volumes)
            self.state.save_container('manager', man_con)

    def start(self):
        with client() as pm:
            self.state.get_pod_object(client=pm).start()

    def stop(self):
        with client() as pm:
            self.state.get_pod_object(client=pm).stop()

    def restart(self):
        with client() as pm:
            self.state.get_pod_object(client=pm).restart()

    def pause(self):
        with client() as pm:
            self.state.get_pod_object(client=pm).pause()

    def unpause(self):
        with client() as pm:
            self.state.get_pod_object(client=pm).pause()

    def is_running(self):
        with client() as pm:
            pod = self.state.get_pod_object(client=pm)
            return pod.status == 'Running'

    def exec(self, cname, cmd):
        # TODO: Use ExecContainer instead
        with client() as pm:
            cont = self.state.get_container_object(cname, client=pm)

            proc = subprocess.run(
                ['podman', 'exec', cont.id, *cmd], encoding='utf-8',
                stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )
        return proc.returncode, proc.stdout


def produce_properties(props):
    yield "# Generated by podcraft"
    for k, v in props.items():
        if isinstance(v, bool):
            yield f"{k}={str(v).lower()}"
        else:
            yield f"{k}={v}"
