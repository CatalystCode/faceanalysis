from typing import Iterator

from container_parser import ContainerParser
from face_vector_parser_pipeline import FaceVectorParserPipeline
from metrics import FaceVectorMetric
from pair import Pair
from parser_base import ParserBase


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
            self.__parser_pipeline = FaceVectorParserPipeline(
                pairs, self._distance_metric)
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
        self._parser_pipeline.add(self._parser_pipeline.filter_target)
