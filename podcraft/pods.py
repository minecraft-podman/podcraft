"""
Stuff for pods
"""


# https://github.com/containers/python-podman/issues/64
from podman.libs import ConfigDict
from podman.libs.pods import Pod


def create_pod(client, ident=None, cgroupparent=None, labels=None, share=None,
               infra=False, publish=[]):
    """Create a new empty pod."""
    infra = infra or bool(publish)
    if not share and infra:
        share = ['cgroup', 'ipc', 'net', 'uts']
    config = ConfigDict(
        name=ident,
        cgroupParent=cgroupparent,
        labels=labels,
        share=share,
        infra=infra,
        publish=publish
    )

    with client._client() as podman:
        result = podman.CreatePod(config)
        details = podman.GetPod(result['pod'])
    return Pod(client._client, result['pod'], details['pod'])
