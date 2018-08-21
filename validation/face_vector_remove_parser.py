from container_parser import ContainerParser
from face_vector_parser import FaceVectorParser
from face_vector_remove_parser_pipeline import FaceVectorRemoveParserPipeline


class FaceVectorRemoveParser(FaceVectorParser):
    def __init__(self,
                 container_parser: ContainerParser,
                 distance_metric: str) -> None:
        super().__init__(container_parser, distance_metric)
        self.__parser_pipeline = None

    @property
    def _parser_pipeline(self):
        if not self.__parser_pipeline:
            pairs = self._container_parser.compute_pairs()
            self.__parser_pipeline = FaceVectorRemoveParserPipeline(
                pairs,
                self._distance_metric)
        return self.__parser_pipeline

    def _build_pipeline(self) -> None:
        super()._build_pipeline()
        self._parser_pipeline.add(self._parser_pipeline.remove_empty)
