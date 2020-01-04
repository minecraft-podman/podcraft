import os
import sys

import click

from .mainobj import Podcraft, NoProjectError
from .poddir import build_server, build_manager
from .podman import client


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
    with client() as pm:
        print("Building server...")
        serv_img = build_server(pm, {'eula': 'yes'})
        print(serv_img)
        print(serv_img.inspect())
        print("Building manager...")
        man_img = build_manager(pm)
        print(man_img)
        print(man_img.inspect())


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
