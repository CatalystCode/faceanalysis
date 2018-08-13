from typing import List
import json
import os

from docker import DockerClient

from faceanalysis.log import get_logger
from faceanalysis.settings import DOCKER_DAEMON
from faceanalysis.settings import HOST_DATA_DIR
from faceanalysis.settings import MOUNTED_DATA_DIR

FaceVector = List[float]
logger = get_logger(__name__)


def _format_mount_path(img_path: str) -> str:
    return '/{}'.format(os.path.basename(img_path))


def _format_host_path(img_path: str) -> str:
    # volume mounts must be absolute
    if not img_path.startswith('/'):
        img_path = os.path.abspath(img_path)

    # adjust the path if it itself is a mount and if we're spawning a
    # sibling container
    if MOUNTED_DATA_DIR and HOST_DATA_DIR:
        img_path = img_path.replace(MOUNTED_DATA_DIR, HOST_DATA_DIR)

    return img_path


def get_face_vectors(img_path: str, algorithm: str) -> List[FaceVector]:
    img_mount = _format_mount_path(img_path)
    img_host = _format_host_path(img_path)
    volumes = {img_host: {'bind': img_mount, 'mode': 'ro'}}

    logger.debug('Running container %s with image %s', algorithm, img_host)
    client = DockerClient(base_url=DOCKER_DAEMON)
    stdout = client.containers.run(algorithm, img_mount,
                                   volumes=volumes, auto_remove=True)

    face_vectors = json.loads(stdout.decode('ascii')).get('faceVectors')
    return face_vectors[0] if face_vectors else []


def face_vector_to_text(vector: FaceVector) -> str:
    return json.dumps(vector)


def face_vector_from_text(text: str) -> FaceVector:
    return json.loads(text)
