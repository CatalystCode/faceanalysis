from typing import Dict, Iterable, Iterator

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

    def compute_pairs(self) -> Iterator[Pair]:
        pairs = self._container_parser.compute_pairs()
        if self._remove_empty_embeddings_flag:
            pairs = self._remove_empty_pairs(pairs)
        else:
            pairs = self._fill_empty_pairs(pairs)
        return self._filter_target_pairs(pairs)

    def compute_metrics(self) -> Dict[str, float]:
        pairs = list(self._container_parser.compute_pairs())
        num_expected = len(pairs)
        num_missing = num_expected - len(list(self._remove_empty_pairs(pairs)))
        percentage_missing = 100 * (num_missing / num_expected)
        metrics = {'num_expected': num_expected,
                   'num_missing': num_missing,
                   'percentage_missing': percentage_missing}
        return metrics

    def _remove_empty_pairs(self, pairs: Iterable[Pair]) -> Iterator[Pair]:
        return (pair for pair in pairs if pair.image1 and pair.image2)

    def _fill_empty_pairs(self, pairs: Iterable[Pair]) -> Iterator[Pair]:
        empty_embedding = [[0] * self._embedding_size]
        return (Pair(pair.image1 or empty_embedding,
                     pair.image2 or empty_embedding,
                     pair.is_match) for pair in pairs)

    def _filter_target_pairs(self, pairs: Iterable[Pair]) -> Iterator[Pair]:
        return (self._compute_target_pair(pair) for pair in pairs)

    def _compute_target_pair(self, pair: Pair) -> Pair:
        possible_pairs = [Pair(image1, image2, pair.is_match)
                          for image1 in pair.image1
                          for image2 in pair.image2]
        distance_calculator = DistanceCalculator(self._distance_metric)
        distances = distance_calculator.calculate(possible_pairs)
        distance_criteria = min if pair.is_match else max
        index, _ = distance_criteria(enumerate(distances), key=lambda x: x[1])
        return possible_pairs[index]
