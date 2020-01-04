import subprocess
import podman
import contextlib
import tempfile
import time
import os.path


# TODO: Connection pooling/saving
@contextlib.contextmanager
def client():
    socket = tempfile.mktemp()
    proc = subprocess.Popen(
        ['podman', 'varlink', '--timeout', '0', f'unix:{socket}'],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
    )
    while not os.path.exists(socket):
        time.sleep(0.1)
    try:
        with podman.Client(f'unix:{socket}') as client:
            yield client
    finally:
        proc.terminate()
