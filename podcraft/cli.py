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
        pc.rebuild_everything()


@main.command()
def start():
    click.echo('TODO: Start pod')


@main.command()
def status():
    click.echo('TODO: Check pod')


@main.command()
def stop():
    click.echo('TODO: Stop pod')


# init/new
# RCON
# Whitelist
# Banlist
