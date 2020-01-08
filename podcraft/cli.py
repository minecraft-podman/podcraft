import os
import sys
import logging

import click

from .mainobj import Podcraft, NoProjectError


@click.group()
@click.pass_context
def main(ctx):
    logging.basicConfig(format='%(message)s', level=logging.INFO)
    try:
        ctx.obj = Podcraft.find_project(os.getcwd())
    except NoProjectError:
        sys.exit("No podcraft.toml found")


@main.command()
@click.pass_obj
def build(pc):
    """
    (Re)build containers and related resources.
    """
    with pc:
        pc.cleanup()
        pc.rebuild_everything()


@main.command()
@click.pass_obj
def unbuild(pc):
    """
    Clean up container-related resources.

    Does not delete volume data.
    """
    with pc:
        pc.cleanup()


@main.command()
@click.pass_obj
def start(pc):
    """
    Start the server.

    Will fail if it's not built.
    """
    with pc:
        pc.start()


@main.command()
@click.pass_obj
def status(pc):
    """
    Checks if the server is running.

    0 if it is, 1 if it isn't.
    """
    with pc:
        sys.exit(0 if pc.is_running() else 1)


@main.command()
@click.pass_obj
def stop(pc):
    """
    Stop the server.
    """
    with pc:
        pc.stop()


# init/new
# RCON
# Server list ping
# Whitelist
# Banlist
