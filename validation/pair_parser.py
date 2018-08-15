from os.path import exists, join
from typing import Dict, List
from pair import Pair
from parser_base import ParserBase


class PairParser(ParserBase):

    def __init__(self, pairs_fname: str, image_dir: str) -> None:
        self.pairs_fname = pairs_fname
        self._image_dir = image_dir

    def get_pairs(self) -> List[Pair]:
        pairs: List[Pair] = []
        with open(self.pairs_fname, 'r') as f:
            next(f)
            for line in f:
                pair = self._get_pair(line)
                pairs.append(pair)
        return pairs

    def get_metrics(self) -> Dict[str, float]:
        raise NotImplementedError()

    def _get_full_path(self, image_path: str) -> str:
        exts = ['.jpg', '.png']
        for ext in exts:
            full_image_path = join(self._image_dir, f'{image_path}{ext}')
            if exists(full_image_path):
                return full_image_path
        err = f'{image_path} does not exist with extensions: {exts}'
        raise FileNotFoundError(err)

    def _get_pair(self, line: str) -> Pair:
        line_info = line.strip().split()
        if len(line_info) == 3:
            name, n1, n2 = line_info
            image1 = self._get_full_path(join(name, f'{name}_{int(n1):04d}'))
            image2 = self._get_full_path(join(name, f'{name}_{int(n2):04d}'))
            is_match = True
        else:
            name1, n1, name2, n2 = line_info
            image1 = self._get_full_path(join(name1, f'{name1}_{int(n1):04d}'))
            image2 = self._get_full_path(join(name2, f'{name2}_{int(n2):04d}'))
            is_match = False
        return Pair(image1, image2, is_match)
