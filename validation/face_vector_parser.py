from functools import partial
from typing import Iterator

from container_parser import ContainerParser
from metrics import FaceVectorMetric
from pair import Pair
from parser_base import ParserBase
from parser_pipeline import ParserPipeline
from parser_pipeline_funcs import filter_target


class FaceVectorParser(ParserBase):

    def __init__(self,
                 container_parser: ContainerParser,
                 distance_metric: str) -> None:
        self._container_parser = container_parser
        self._distance_metric = distance_metric
        self.__parser_pipeline = None

    @property
    def _parser_pipeline(self):
        if not self.__parser_pipeline:
            pairs = self._container_parser.compute_pairs()
            self.__parser_pipeline = ParserPipeline(pairs)
        return self.__parser_pipeline

    def compute_pairs(self) -> Iterator[Pair]:
        self._build_pipeline()
        return self._parser_pipeline.apply()

    def compute_metrics(self) -> FaceVectorMetric:
        pairs = list(self._container_parser.compute_pairs())
        num_expected = len(pairs)
        num_existing = sum(1 for pair in pairs if pair.image1 and pair.image2)
        num_missing = num_expected - num_existing
        percentage_missing = 100 * (num_missing / num_expected)
        return FaceVectorMetric(num_expected, num_missing, percentage_missing)

    def _build_pipeline(self) -> None:
        partial_filter = partial(filter_target,
                                 distance_metric=self._distance_metric)
        self._parser_pipeline.add(partial_filter)
