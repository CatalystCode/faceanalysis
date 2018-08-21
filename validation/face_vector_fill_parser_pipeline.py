from typing import Iterable
from typing import Iterator

from face_vector_parser_pipeline import FaceVectorParserPipeline
from pair import Pair


class FaceVectorFillParserPipeline(FaceVectorParserPipeline):
    def __init__(self,
                 pairs: Iterable[Pair],
                 distance_metric: str,
                 embedding_size: int) -> None:
        super().__init__(pairs, distance_metric)
        self._embedding_size = embedding_size

    def fill_empty(self, pairs: Iterable[Pair]) -> Iterator[Pair]:
        empty_embedding = [[0] * self._embedding_size]
        return (Pair(pair.image1 or empty_embedding,
                     pair.image2 or empty_embedding,
                     pair.is_match) for pair in pairs)
