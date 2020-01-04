"""
Do all the calculations for config stuff
"""
import json
import secrets

MINECRAFT_PORT = 25565
RCON_PORT = 25575
QUERY_PORT = 25565


class Config(dict):
    def server_buildargs(self):
        """
        The buildargs for the server container
        """
        return self['server']

    def manage_buildargs(self):
        return {
            'extra_pkgs': json.dumps(self['management'].get('plugins')),
        }

    def server_properties(self):
        """
        Compute the values of server.properties for use inside the pod.

        NOTE: This can vary from what the user specified
        """
        props = self['properties'].copy()
        props['server-port'] = MINECRAFT_PORT  # Has to match container delcaration
        props['level-name'] = 'world'  # Has to match volumes and stuff
        props.setdefault('enable-flight', True)  # Switch default because elytra
        # Enable rcon for internal usage
        props['enable-rcon'] = True
        props['rcon.port'] = RCON_PORT
        if 'rcon.password' not in props:
            # Don't think this needs to be cached, everything that needs it
            # reads it from server.properties
            props['rcon.password'] = secrets.token_urlsafe()
        return props

    def exposed_ports(self):
        """
        Calculate the ports exposed by the pod

        Returns a dict mapping external port to (container name, port)
        """
        rv = {}
        # Minecraft
        mc_port = self['properties'].get('server-port', MINECRAFT_PORT)
        rv[mc_port] = ('server', MINECRAFT_PORT)

        # MC RCON
        if self['properties'].get('enable-rcon', False):
            rcon_port = self['properties'].get('rcon.port', RCON_PORT)
            rv[rcon_port] = ('server', RCON_PORT)

        # MC Query
        if self['properties'].get('enable-query', False):
            query_port = self['properties'].get('query.port', QUERY_PORT)
            rv[f'{query_port}/udp'] = ('server', query_port)

        # Management API
        if 'server-port' in self['management']:
            man_port = self['management']['server-port']
            rv[man_port] = ('manage', 80)

        # Can't compute ports for addons, those come from the container images

        return rv

    def volumes(self):
        """
        Generates (local dir, mount point) of all the volumes in the config.

        Local dir can be None, in which case it doesn't need to be save locally
        """
        yield 'live', '/mc/world'
        yield 'snapshot', '/mc/snapshot'
        yield '.tmp/server.properties', '/mc/server.properties'
        yield 'logs', '/mc/logs'
        for fname in ("banned-ips.json", "ops.json", "whitelist.json"):
            yield fname, f'/mc/{fname}'

        for name, mount in self['volumes']:
            yield name, mount
