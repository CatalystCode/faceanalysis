from container_parser import ContainerParser
from face_vector_parser import FaceVectorParser
from parser_pipeline_funcs import remove_empty


class FaceVectorRemoveParser(FaceVectorParser):
    def __init__(self,
                 container_parser: ContainerParser,
                 distance_metric: str) -> None:
        super().__init__(container_parser, distance_metric)
        self.__parser_pipeline = None

    def _build_pipeline(self) -> None:
        super()._build_pipeline()
        self._parser_pipeline.add(remove_empty)
