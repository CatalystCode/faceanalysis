import json
from os.path import basename
from os.path import dirname
from os.path import join
from parser.pair import Pair
from parser.pair_parser import PairParser
from parser.parser_base import ParserBase
from typing import Dict
from typing import Iterable
from typing import List

import docker


class ContainerParser(ParserBase):

    def __init__(self,
                 pair_parser: PairParser,
                 container_name: str,
                 is_prealigned: bool) -> None:
        self._pair_parser = pair_parser
        self._container_name = container_name
        self._is_prealigned = is_prealigned
        self.__face_vectors = None

    @property
    def _face_vectors(self):
        if not self.__face_vectors:
            self.__face_vectors = self._compute_face_vectors()
        return self.__face_vectors

    def compute_pairs(self) -> Iterable[Pair]:
        pairs = self._pair_parser.compute_pairs()
        return (Pair(image1, image2, pair.is_match)
                for image1, image2, pair in
                zip(self._face_vectors[0::2], self._face_vectors[1::2], pairs))

    def compute_metrics(self) -> Dict[str, float]:
        raise NotImplementedError()

    def _compute_face_vectors(self) -> List[List[List[float]]]:
        pairs = list(self._pair_parser.compute_pairs())
        base_dir = self._get_base_dir_for_volume_mapping(pairs[0].image1)
        volumes = {base_dir: {'bind': '/images', 'mode': 'ro'}}
        mounts = [join(basename(dirname(image_path)), basename(image_path))
                  for pair in pairs
                  for image_path in [pair.image1, pair.image2]]
        image_mount = ' '.join([f'/images/{path}' for path in mounts])
        env = ["PREALIGNED=true"] if self._is_prealigned else []
        client = docker.from_env()
        stdout = client.containers.run(self._container_name,
                                       image_mount,
                                       volumes=volumes,
                                       auto_remove=True,
                                       environment=env)
        return json.loads(stdout.decode('utf-8').strip())['faceVectors']

    @staticmethod
    def _get_base_dir_for_volume_mapping(full_image_path: str) -> str:
        return dirname(dirname(full_image_path))
