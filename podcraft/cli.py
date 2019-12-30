import click


@click.group()
def main():
    pass


@main.command()
def build():
    click.echo('TODO: Build images')


@main.command()
def start():
    click.echo('TODO: Start pod')


@main.command()
def status():
    click.echo('TODO: Check pod')


@main.command()
def stop():
    click.echo('TODO: Stop pod')


# Whitelist
# Banlist