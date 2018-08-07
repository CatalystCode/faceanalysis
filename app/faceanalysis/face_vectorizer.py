import os
import json
import docker
from .log import get_logger

logger = get_logger(__name__, os.environ['LOGGING_LEVEL'])

mounted_data_dir = os.environ['MOUNTED_DATA_DIR']
host_data_dir = os.environ['HOST_DATA_DIR']


def _format_mount_path(img_path):
    return '/{}'.format(os.path.basename(img_path))


def _format_host_path(img_path):
    # volume mounts must be absolute
    if not img_path.startswith('/'):
        img_path = os.path.abspath(img_path)

    # adjust the path if it itself is a mount and if we're spawning a
    # sibling container
    if mounted_data_dir and host_data_dir:
        img_path = img_path.replace(mounted_data_dir, host_data_dir)

    return img_path


def get_face_vectors(img_path, algorithm):
    img_mount = _format_mount_path(img_path)
    img_host = _format_host_path(img_path)
    volumes = {img_host: {'bind': img_mount, 'mode': 'ro'}}

    client = docker.from_env()
    stdout = client.containers.run(algorithm, img_mount,
                                   volumes=volumes, auto_remove=True)

    face_vectors = json.loads(stdout.decode('ascii')).get('faceVectors', [])
    return face_vectors
