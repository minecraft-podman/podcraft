"""
Host-level stuff
"""
# Stuff in the server directory:
# * server.toml: The config file that defines things
# * .tmp: Working directory of ephemeral things
# * .tmp/server.properties: The server.properties
# * .tmp/io.podman: The podman socket
# * .tmp/state.json: Place to keep a bunch of references (namely, pod ID)
# * live: The /mc/world the server works from
# * snapshot: The most recent snapshot of live
# * Whatever additional persistent volumes are defined in server.toml
# Only the first thing needs to be present
import requests
import tempfile
import tarfile
import io
import os.path
import subprocess

from .namegen import generate_name

CONTAINER_REPOS = {
    'server': "https://github.com/minecraft-podman/docker-server/archive/master.tar.gz",
    'manage': "https://github.com/minecraft-podman/manage/archive/master.tar.gz",
}


# def build_img_from_url(podman, url buildargs):
#     with tempfile.TemporaryDirectory() as tempdir:
#         # 1. Download repo
#         tarbuf = io.BytesIO()
#         with requests.get(url, stream=True) as resp:
#             resp.raise_for_status()
#             for chunk in resp.iter_content(chunk_size=8192):
#                 if chunk:  # Filter out keep-alive new chunks
#                     tarbuf.write(chunk)
#
#         tarbuf.seek(0)
#         buildroot = os.path.join(tempdir, 'context.tar')
#         dockerfile = os.path.join(tempdir, 'Dockerfile')
#         # Not a super fan of rebuilding the tarball, but :shrug:
#         with tarfile.open(fileobj=tarbuf, mode='r:gz') as src:
#             with tarfile.open(buildroot, 'w') as dest:
#                 # Copy everything, striping the leading directory off all the names
#                 for member in src.getmembers():
#                     stream = src.extractfile(member)
#                     member.name = member.name.split('/', 1)[-1]
#                     dest.addfile(member, stream)
#                     if member.name == 'Dockerfile':
#                         # Extract the Dockerfile
#                         stream.seek(0)
#                         with open(dockerfile, 'wb') as df:
#                             df.write(stream.read())
#
#         # 2. Build into image
#         img = podman.images.build(
#             buildArgs=buildargs,
#             contextDir=buildroot,
#             dockerfile=dockerfile,
#             tags=generate_name(),
#             # annotations={
#             #     'podcraft.root': serverdir,
#             # },
#         )


# https://github.com/containers/python-podman/issues/63
def build_img_from_url(podman, url, buildargs, *, verbose=False):
    """
    Downloads a tarball from the given URL and uses it to build an image.
    """
    with tempfile.TemporaryDirectory() as tempdir:
        # 1. Download repo
        tarbuf = io.BytesIO()
        with requests.get(url, stream=True) as resp:
            resp.raise_for_status()
            for chunk in resp.iter_content(chunk_size=8192):
                if chunk:  # Filter out keep-alive new chunks
                    tarbuf.write(chunk)

        tarbuf.seek(0)
        with tarfile.open(fileobj=tarbuf, mode='r:gz') as src:
            src.extractall(tempdir)
            root = src.getmembers()[0].name.split('/', 1)[0]

        buildroot = os.path.join(tempdir, root)

        # 2. Build into image
        with tempfile.NamedTemporaryFile('w+t', encoding='utf-8') as ntf:
            cli = ['podman', 'build']
            for k, v in buildargs.items():
                cli += ['--build-arg', f'{k}={v}']
            cli += ['--iidfile', ntf.name]
            cli += ['--tag', generate_name()]
            cli += [buildroot]

            # FIXME: Forward output on error
            subprocess.run(
                cli, stdin=subprocess.DEVNULL,
                stdout=None if verbose else subprocess.DEVNULL,
                stderr=subprocess.STDOUT,
                check=True,
            )

            ntf.seek(0)
            image_id = ntf.read().strip()
        return podman.images.get(image_id)


def build_server(podman, buildargs):
    """
    Build the server container image
    """
    return build_img_from_url(podman, CONTAINER_REPOS['server'], buildargs)


def build_manager(podman, buildargs):
    """
    Build the management container image
    """
    return build_img_from_url(podman, CONTAINER_REPOS['manage'], buildargs)


def get_ports(image):
    """
    Get the declared exposed ports for the given image.

    All are in the form of "<port>/<tcp|udp>".
    """
    ii = image.inspect()
    yield from ii.config.get('exposedports', {}).keys()


def get_volumes(image):
    """
    Get the declared volumes for the given image
    """
    ii = image.inspect()
    yield from ii.config.get('volumes', {}).keys()
