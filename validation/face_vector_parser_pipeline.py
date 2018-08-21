from typing import Iterable
from typing import Iterator

from distance_calculator import DistanceCalculator
from pair import Pair
from parser_pipeline import ParserPipeline


class FaceVectorParserPipeline(ParserPipeline):
    def __init__(self, pairs: Iterable[Pair], distance_metric: str) -> None:
        super().__init__(pairs)
        self._distance_metric = distance_metric

    def filter_target(self, pairs: Iterable[Pair]) -> Iterator[Pair]:
        return (self._compute_target(pair) for pair in pairs)

    def _compute_target(self, pair: Pair) -> Pair:
        possible_pairs = [Pair(image1, image2, pair.is_match)
                          for image1 in pair.image1
                          for image2 in pair.image2]
        distance_calculator = DistanceCalculator(self._distance_metric)
        distances = distance_calculator.calculate(possible_pairs)
        distance_criteria = min if pair.is_match else max
        index, _ = distance_criteria(enumerate(distances), key=lambda x: x[1])
        return possible_pairs[index]
