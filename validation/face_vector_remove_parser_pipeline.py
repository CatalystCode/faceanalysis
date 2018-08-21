from typing import Iterable
from typing import Iterator

from face_vector_parser_pipeline import FaceVectorParserPipeline
from pair import Pair


class FaceVectorRemoveParserPipeline(FaceVectorParserPipeline):
    def __init__(self, pairs: Iterable[Pair], distance_metric: str) -> None:
        super().__init__(pairs, distance_metric)

    def remove_empty(self, pairs: Iterable[Pair]) -> Iterator[Pair]:
        return (pair for pair in pairs if pair.image1 and pair.image2)
