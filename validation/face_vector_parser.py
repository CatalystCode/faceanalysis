from typing import Dict, List
from container_parser import ContainerParser
from distance_calculator import DistanceCalculator
from pair import Pair
from parser_base import ParserBase


class FaceVectorParser(ParserBase):

    def __init__(self,
                 container_parser: ContainerParser,
                 embedding_size: int,
                 distance_metric: str,
                 remove_empty_embeddings_flag: bool) -> None:
        self._container_parser = container_parser
        self._embedding_size = embedding_size
        self._distance_metric = distance_metric
        self._remove_empty_embeddings_flag = remove_empty_embeddings_flag

    def get_pairs(self) -> List[Pair]:
        pairs = self._container_parser.get_pairs()
        if self._remove_empty_embeddings_flag:
            pairs = self._remove_empty_pairs(pairs)
        else:
            pairs = self._fill_empty_pairs(pairs)
        return self._filter_target_pairs(pairs)

    def get_metrics(self) -> Dict[str, float]:
        pairs = self._container_parser.get_pairs()
        num_expected = len(pairs)
        num_missing = num_expected - len(self._remove_empty_pairs(pairs))
        percentage_missing = 100 * (num_missing / num_expected)
        metrics = {'num_expected': num_expected,
                   'num_missing': num_missing,
                   'percentage_missing': percentage_missing}
        return metrics

    def _remove_empty_pairs(self, pairs: List[Pair]) -> List[Pair]:
        indices_to_exclude = []
        for i, pair in enumerate(pairs):
            if not (pair.image1 and pair.image2):
                indices_to_exclude.append(i)
        full_pairs = []
        for i, pair in enumerate(pairs):
            if i not in indices_to_exclude:
                full_pairs.append(pair)
        return full_pairs

    def _fill_empty_pairs(self, pairs: List[Pair]) -> List[Pair]:
        filled_images = []
        for pair in pairs:
            image1 = ([[0] * self._embedding_size]
                      if not pair.image1 else pair.image1)
            image2 = ([[0] * self._embedding_size]
                      if not pair.image2 else pair.image2)
            filled_images.append(Pair(image1, image2, pair.is_match))
        return filled_images

    def _filter_target_pairs(self, pairs: List[Pair]) -> List[Pair]:
        target_pairs = []
        for pair in pairs:
            target_pair = self._get_target_pair(pair)
            target_pairs.append(target_pair)
        return target_pairs

    def _get_target_pair(self, pair: Pair) -> Pair:
        possible_pairs = [Pair(image1, image2, pair.is_match)
                          for image1 in pair.image1
                          for image2 in pair.image2]
        distance_calculator = DistanceCalculator(self._distance_metric)
        distances = distance_calculator.calculate(possible_pairs)
        distance_criteria = min if pair.is_match else max
        index, _ = distance_criteria(enumerate(distances), key=lambda x: x[1])
        return possible_pairs[index]
