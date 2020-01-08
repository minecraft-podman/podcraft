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
    with pc:
        pc.cleanup()
        pc.rebuild_everything()


@main.command()
@click.pass_obj
def start(pc):
    with pc:
        pc.start()


@main.command()
@click.pass_obj
def status(pc):
    with pc:
        sys.exit(0 if pc.is_running() else 1)


@main.command()
@click.pass_obj
def stop(pc):
    with pc:
        pc.stop()


# init/new
# RCON
# Whitelist
# Banlist
