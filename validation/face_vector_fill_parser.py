from container_parser import ContainerParser
from face_vector_fill_parser_pipeline import FaceVectorFillParserPipeline
from face_vector_parser import FaceVectorParser


class FaceVectorFillParser(FaceVectorParser):
    def __init__(self,
                 container_parser: ContainerParser,
                 embedding_size: int,
                 distance_metric: str) -> None:
        super().__init__(container_parser, distance_metric)
        self._embedding_size = embedding_size
        self.__parser_pipeline = None

    @property
    def _parser_pipeline(self):
        if not self.__parser_pipeline:
            pairs = self._container_parser.compute_pairs()
            self.__parser_pipeline = FaceVectorFillParserPipeline(
                pairs,
                self.distance_metric,
                self.embedding_size)
        return self.__parser_pipeline

    def _build_pipeline(self) -> None:
        super()._build_pipeline()
        self._parser_pipeline.add(self._parser_pipeline.fill_empty)
