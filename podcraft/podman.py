import subprocess
import podman
import contextlib
import tempfile
import time
import os
import os.path
import signal


# TODO: Connection pooling/saving
@contextlib.contextmanager
def client():
    socket = tempfile.mktemp()
    proc = subprocess.Popen(
        ['podman', 'varlink', '--timeout', '0', f'unix:{socket}'],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
    )
    # Wait for it to start
    while not os.path.exists(socket):
        time.sleep(0.1)
    try:
        with podman.Client(f'unix:{socket}') as client:
            yield client
    finally:
        # Since the process doesn't have to timeout, we have to signal it to stop
        proc.terminate()


def start_persistent_server(socketfile, pidfile, *, wait_for_start=True):
    """
    Start the persistent server (used for giving containers access to podman).

    Does nothing if the socket already exists.
    """
    if socketfile.exists():
        # Socket exists, let's just assume things are fine
        return

    proc = subprocess.Popen(
        ['podman', 'varlink', '--timeout', '0', f'unix:{socketfile}'],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
    )
    # Wait for it to start
    while wait_for_start and not os.path.exists(socketfile):
        time.sleep(0.1)

    pidfile.write_text(str(proc.pid))


def stop_persistent_server(socketfile, pidfile, *, wait_for_stop=True):
    """
    Stop the persistent server.

    Does nothing if the socket does not exist.
    """
    if not socketfile.exists():
        # Socket not found, let's just assume things are fine
        if pidfile.exists():  # Remove the PID file if it exists.
            pidfile.unlink()
        return

    pid = int(pidfile.read_text())
    os.kill(pid, signal.SIGTERM)

    # Wait for it to stop
    while wait_for_stop and os.path.exists(socketfile):
        time.sleep(0.1)

    pidfile.unlink()
