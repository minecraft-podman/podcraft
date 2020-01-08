"""
Deals with some of the fiddly bits about containers
"""
import copy
import logging

from podman.libs import ConfigDict, flatten
from podman.libs.containers import Container

from .images import get_volumes


def create_container(image, pod, volumes, **opts):
    img_volumes = set(get_volumes(image))
    c_mounts = [
        f"type=bind,source={h},destination={c}"
        for c, h in volumes.items() if c in img_volumes
    ]

    return _create(
        image,
        pod=pod.id,
        mount=c_mounts,
        **opts
    )


# Exists because bug work-arounds
def _create(self, *args, **kwargs):
    """Create container from image.
    Pulls defaults from image.inspect()
    """
    details = self.inspect()

    config = ConfigDict(image_id=self._id, **kwargs)
    config["command"] = details.config.get("cmd")
    config["env"] = self._split_token(details.config.get("env"))
    config["image"] = copy.deepcopy(details.repotags[0])  # Falls to https://github.com/containers/python-podman/issues/65
    config["labels"] = copy.deepcopy(details.labels)
    config["args"] = [config["image"], *config["command"]]

    logging.debug("Image %s: create config: %s", self._id, config)
    with self._client() as podman:
        id_ = podman.CreateContainer(config)["container"]
        cntr = podman.GetContainer(id_)
    return Container(self._client, id_, cntr["container"])
