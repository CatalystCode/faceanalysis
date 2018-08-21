from typing import Callable
from typing import Iterable
from typing import Iterator
from typing import List

from pair import Pair

PipelineFunction = Callable[[Iterable[Pair]], Iterator[Pair]]


class ParserPipeline:
    def __init__(self, pairs: Iterable[Pair]) -> None:
        self._pairs = pairs
        self._funcs: List[PipelineFunction] = []

    def add(self, func: PipelineFunction):
        self._funcs.insert(0, func)

    def apply(self) -> Iterable[Pair]:
        pairs = self._pairs
        for func in self._funcs:
            pairs = func(pairs)
        return pairs
