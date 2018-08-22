from functools import partial
from parser.container_parser import ContainerParser
from parser.face_vector_parser import FaceVectorParser
from parser.pipeline.parser_pipeline_funcs import fill_empty


class FaceVectorFillParser(FaceVectorParser):
    def __init__(self,
                 container_parser: ContainerParser,
                 embedding_size: int,
                 distance_metric: str) -> None:
        super().__init__(container_parser, distance_metric)
        self._embedding_size = embedding_size
        self.__parser_pipeline = None

    def _build_pipeline(self) -> None:
        super()._build_pipeline()
        partial_fill = partial(fill_empty, embedding_size=self._embedding_size)
        self._parser_pipeline.add(partial_fill)
