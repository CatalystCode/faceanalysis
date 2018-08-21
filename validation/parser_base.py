from abc import ABC
from abc import abstractmethod
from typing import Any
from typing import Iterator

from pair import Pair


class ParserBase(ABC):

    @abstractmethod
    def compute_pairs(self) -> Iterator[Pair]:
        pass

    @abstractmethod
    def compute_metrics(self) -> Any:
        pass
