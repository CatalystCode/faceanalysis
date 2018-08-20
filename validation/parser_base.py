from abc import ABC, abstractmethod
from typing import Dict, Iterator

from pair import Pair


class ParserBase(ABC):

    @abstractmethod
    def compute_pairs(self) -> Iterator[Pair]:
        pass

    @abstractmethod
    def compute_metrics(self) -> Dict[str, float]:
        pass
