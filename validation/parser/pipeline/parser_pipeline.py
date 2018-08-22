from parser.container_parser import ContainerParser
from parser.pair import Pair
from typing import Callable
from typing import Iterable
from typing import Iterator

PipelineFunction = Callable[[Iterable[Pair]], Iterator[Pair]]


class ParserPipeline:
    def __init__(self, container_parser: ContainerParser) -> None:
        self._container_parser = container_parser
        self._funcs: Iterable[PipelineFunction] = None
        self.__pairs: Iterable[Pair] = None

    @property
    def _pairs(self):
        if not self.__pairs:
            self.__pairs = self._container_parser.compute_pairs()
        return self.__pairs

    def build(self, funcs: Iterable[Callable[[Iterable[Pair]],
                                             Iterable[Pair]]]) -> None:
        self._funcs = funcs

    def execute_pipeline(self) -> Iterable[Pair]:
        pairs = self._pairs
        for func in self._funcs:
            pairs = func(pairs)
        return pairs
