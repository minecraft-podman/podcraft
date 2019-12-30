podcraft
========

Manages and runs minecraft servers, using podman and container pods.


Example Config
--------------

```toml

[properties]
# Based on https://minecraft.gamepedia.com/Server.properties
motd="My Server"
port=25565

[server]
type=vanilla


[management]
plugins=["pkg1", "pkg2"]

[[addon]]
image=myimage
volumes=['/world-snapshot', '/mc']

  [[addon.args]]
  spam=eggs
```