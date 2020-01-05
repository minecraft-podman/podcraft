import os
import sys

import click

from .mainobj import Podcraft, NoProjectError


@click.group()
@click.pass_context
def main(ctx):
    try:
        ctx.obj = Podcraft.find_project(os.getcwd())
    except NoProjectError:
        sys.exit("No podcraft.toml found")


@main.command()
@click.pass_obj
def build(pc):
    pc.rebuild_images(lambda cont: print(f"Building {cont}..."))


@main.command()
def start():
    click.echo('TODO: Start pod')


@main.command()
def status():
    click.echo('TODO: Check pod')


@main.command()
def stop():
    click.echo('TODO: Stop pod')


# RCON
# Whitelist
# Banlist
