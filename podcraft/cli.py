import json
import os
import sys
import logging

import click

from .mainobj import Podcraft, NoProjectError


@click.group()
@click.pass_context
def main(ctx):
    logging.basicConfig(format='%(message)s', level=logging.DEBUG)
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


@main.command()
@click.argument('cmd', nargs=-1)
@click.pass_obj
def rcon(pc, cmd):
    """
    Run an rcon command
    """
    with pc:
        rc, out = pc.exec('server', ['cmd', ' '.join(cmd)])
        print(out)
        sys.exit(rc)


@main.command()
@click.argument('cmd', nargs=-1)
@click.pass_obj
def ping(pc, cmd):
    """
    Do a server list ping
    """
    with pc:
        rc, out = pc.exec('server', ['status'])
        try:
            data = json.loads(out)
        except Exception:
            click.echo(out)
        else:
            # This bit adapted from mcstatus
            click.echo(f"version: v{data['version']['name']} (protocol {data['version']['protocol']})")
            click.echo(f"description: {data['description']['text']}")
            click.echo(
                "players: {}/{} {}".format(
                    data['players']['online'],
                    data['players']['max'],
                    [
                        "{} ({})".format(player['name'], player['id'])
                        for player in data['players']['sample']
                    ] if data.get('players', {}).get('sample') else "No players online"
                )
            )
        sys.exit(rc)

# init/new
# Whitelist
# Banlist
