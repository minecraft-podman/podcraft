import click


@click.group()
def main():
    pass


@main.command()
def init():
    click.echo('TODO: Build images & prep')


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
