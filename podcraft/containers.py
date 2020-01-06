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
    c_volumes = [
        f"type=bind,source={h},destination={c}"
        for h, c in volumes.items() if c in img_volumes
    ]

    return _create(
        image,
        pod=pod.id,
        volume=c_volumes,
        **opts
    )


# Exists because https://github.com/containers/python-podman/issues/65
def _create(self, *args, **kwargs):
    """Create container from image.
    Pulls defaults from image.inspect()
    """
    details = self.inspect()

    config = ConfigDict(image_id=self._id, **kwargs)
    config["command"] = details.config.get("cmd")
    config["env"] = self._split_token(details.config.get("env"))
    config["image"] = self.id
    config["labels"] = copy.deepcopy(details.labels)
    # TODO: Are these settings still required?
    config["net_mode"] = "bridge"
    config["network"] = "bridge"
    config["args"] = flatten([config["image"], config["command"]])

    logging.debug("Image %s: create config: %s", self._id, config)
    with self._client() as podman:
        id_ = podman.CreateContainer(config)["container"]
        cntr = podman.GetContainer(id_)
    return Container(self._client, id_, cntr["container"])
