podcraft
========

Manages and runs minecraft servers, using podman and container pods.


Config
------

```toml
[properties]
motd="My Server"
server-port=25565

[server]
eula=yes
type="vanilla"

[volumes]
map="/srv/overviewer"

[management]
server-port=26656
plugins=["pkg1", "pkg2"]

[management.backup]
frequency="1h"

[[management.backup.job]]
image="podcraft/overviewer"
dest='/srv/overviewer'

[[management.backup.job]]
image="podcraft/s3"
dest='s3://mybucket/myworld_%y-%m-%d.tar.xz'

[[addon]]
image="myimage"
```

### properties
Same as [`server.properties`](https://minecraft.gamepedia.com/Server.properties), with some variation:

* RCON is always enabled, but including the settings will expose it outside the pod and/or override generated values
* `server-port` controls the exposed port on the host
* `level-name` is disallowed
* `enable-flight` defaults to true because elytra and mods
* Setting Query-related options will expose the port
* Setting `resource-pack` will trigger the server to generate a `resource-pack-sha1`


### server
These set the arguments used to construct the server. Changing these will trigger a server rebuild on next startup.

((These are the same as the docker-server buildargs. Copy/paste those docs here when stuff is more stable/complete.))


### management
This is the configuration for the management server.

* `server-port`: The exposed port on the host
* `plugins`: Additional python packages to install

### management.backup
This controls the backup settings.

The backup system is based on coherent snapshots: on a regular basis, the world data is flushed and copied, and then a series of jobs are triggered. This makes it easy to run extra programs against that data while making sure those jobs don't see corrupted data.

* `frequency`: approximately how often to perform a snapshot and trigger the post-snapshot jobs. Some randomness is deliberately applied.

### management.backup.job
These sections each define the post-snapshot jobs. These are containers that are run after each snapshot is performed.

Volumes are taken from the container.

* `image`: The container image used to for the job

Per-job settings are also defined here. Individual docs forthcoming.

### addon
These sections define additional service containers to run inside the pod. These can vary from user-facing web apps to <more examples>.

Volumes and exposed ports are taken from the container.

* `image`: The container image to use

Image-specific settings are also defined here.
