import json
from os.path import basename, dirname, join
from typing import Dict, Iterator, List

import docker

from pair import Pair
from pair_parser import PairParser
from parser_base import ParserBase


class ContainerParser(ParserBase):

    def __init__(self,
                 pair_parser: PairParser,
                 container_name: str,
                 prealigned_flag: bool) -> None:
        self._pair_parser = pair_parser
        self._container_name = container_name
        self._prealigned_flag = prealigned_flag
        self.__face_vectors = None

    @property
    def _face_vectors(self):
        if not self.__face_vectors:
            self.__face_vectors = self._compute_face_vectors()
        return self.__face_vectors

    def compute_pairs(self) -> Iterator[Pair]:
        pairs = self._pair_parser.compute_pairs()
        return (Pair(image1, image2, pair.is_match)
                for image1, image2, pair in
                zip(self._face_vectors[0::2], self._face_vectors[1::2], pairs))

    def compute_metrics(self) -> Dict[str, float]:
        raise NotImplementedError()

    def _compute_face_vectors(self) -> List[List[List[float]]]:
        pairs = list(self._pair_parser.compute_pairs())
        base_dir = dirname(dirname((pairs[0].image1)))
        volumes = {base_dir: {'bind': '/images', 'mode': 'ro'}}
        mounts = [join(basename(dirname(image_path)), basename(image_path))
                  for pair in pairs
                  for image_path in [pair.image1, pair.image2]]
        image_mount = ' '.join([f'/images/{path}' for path in mounts])
        env = ["PREALIGNED=true"] if self._prealigned_flag else []
        client = docker.from_env()
        stdout = client.containers.run(self._container_name,
                                       image_mount,
                                       volumes=volumes,
                                       auto_remove=True,
                                       environment=env)
        return json.loads(stdout.decode('utf-8').strip())['faceVectors']
