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

GAME_SERVER_URL = "https://github.com/minecraft-podman/docker-server/archive/master.tar.gz"


def build_server(podman, serverdir, buildargs):
    with tempfile.TemporaryDirectory() as tempdir:
        # 1. Download repo
        tarbuf = io.BytesIO()
        with requests.get(GAME_SERVER_URL, stream=True) as resp:
            resp.raise_for_status()
            for chunk in resp.iter_content(chunk_size=8192):
                if chunk:  # Filter out keep-alive new chunks
                    tarbuf.write(chunk)

        tarbuf.seek(0)
        buildroot = os.path.join(tempdir, 'context.tar')
        dockerfile = os.path.join(tempdir, 'Dockerfile')
        # Not a super fan of rebuilding the tarball, but :shrug:
        with tarfile.open(fileobj=tarbuf, mode='r:gz') as src:
            with tarfile.open(buildroot, 'w') as dest:
                # Copy everything, striping the leading directory off all the names
                for member in src.getmembers():
                    stream = src.extractfile(member)
                    member.name = member.name.split('/', 1)[-1]
                    dest.addfile(member, stream)
                    if member.name == 'Dockerfile':
                        # Extract the Dockerfile
                        stream.seek(0)
                        with open(dockerfile, 'wb') as df:
                            df.write(stream.read())

        # 2. Build into image
        return podman.images.build(
            buildArgs=buildargs,
            contextDir=buildroot,
            dockerfile=dockerfile,
            tags="TODO",  # TODO: Generate system-unique tags
            annotations={
                'podcraft.root': serverdir,
            },
        )
