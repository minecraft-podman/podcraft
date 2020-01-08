"""
Manages the statefile, which tracks things like:

* Image IDs
* Container IDs
* Pod ID

The important thing is that while none of this is critical state, it would be
quite annoying to rebuild.
"""
import json


def default_state():
    return {
        'images': {},
        'containers': {},
    }


class State:
    """
    The stateful/cache bits of podcraft.

    Built on named image/container pairs.
    """
    def __init__(self, fname):
        self.statefile = fname

    def __enter__(self):
        try:
            with open(self.statefile, 'rt') as sf:
                self.data = json.load(sf)
        except FileNotFoundError:
            self.data = default_state()
        except Exception:
            # FIXME: Warn about the loss of state
            ...
            self.data = default_state()
        return self

    def __exit__(self, type, value, tb):
        with open(self.statefile, 'wt') as sf:
            json.dump(self.data, sf)

    def save_image(self, name, img):
        """
        Save a custom-made image
        """
        if img is None:
            del self.data['images'][name]
            return
        if isinstance(img, str):
            save = {'id': img}
        else:
            save = dict(img.items())
        self.data['images'][name] = save

    def get_image(self, name):
        """
        Get the ID for the given image.
        """
        return self.data['images'][name]['id']

    def get_image_object(self, name, *, client):
        """
        Get the ID for the given image.
        """
        obj = client.images.get(self.get_image(name))
        self.save_image(name, obj)  # Update cache
        return obj

    def save_container(self, name, cont):
        """
        Save a container
        """
        if cont is None:
            del self.data['containers'][name]
            return
        if isinstance(cont, str):
            save = {'id': cont}
        else:
            save = dict(cont.items())
        self.data['containers'][name] = save

    def get_container(self, name):
        """
        Get the ID for the given image.
        """
        return self.data['containers'][name]['id']

    def get_container_object(self, name, *, client):
        """
        Get the ID for the given image.
        """
        obj = client.containers.get(self.get_container(name))
        self.save_container(name, obj)  # Update cache
        return obj

    def save_pod(self, pod):
        """
        Save a container
        """
        if pod is None:
            del self.data['pod']
            return
        if isinstance(pod, str):
            save = {'id': pod}
        else:
            save = dict(pod.items())
        self.data['pod'] = save

    def get_pod(self):
        """
        Get the ID for the given image.
        """
        return self.data.get('pod', {}).get('id')

    def get_pod_object(self, *, client):
        """
        Get the ID for the given image.
        """
        podid = self.get_pod()
        if podid is None:
            return
        obj = client.pods.get(podid)
        self.save_pod(obj)  # Update cache
        return obj

    def should_rebuild_container(self, name, *, client=None):
        """
        Is there a new image for this container?

        Roughly, returns True if the image has changed but the container hasn't
        been updated for the new image.

        Returns None if the image is unknown to us.

        Returns True if the container is unknown to us.

        If client is not given, ... can be returned if podman would need to be
        consulted.
        """
        # We are unaware of this image, so the container can't be rebuilt
        if name not in self.data['images']:
            return None

        # We are unaware of this container, so yes you need a new one
        if name not in self.data['containers']:
            return True

        container = self.data['containers'][name]
        image = self.data['images'][name]
        if 'imageid' in container:
            # We have all the information we need locally
            return container['imageid'] != image['id']
        elif client is None:
            # We would have to pull data from podman, but it was not given to us
            return ...
        else:
            # We need to pull complete information from podman
            cobj = client.containers.get(container['id'])
            iobj = client.images.get(image['id'])

            # Update our caches
            self.save_image(name, iobj)
            self.save_container(name, cobj)

            return cobj.imageid != iobj.id
