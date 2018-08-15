from abc import ABC, abstractmethod
from typing import Dict, List
from pair import Pair


class ParserBase(ABC):

    @abstractmethod
    def get_pairs(self) -> List[Pair]:
        pass

    @abstractmethod
    def get_metrics(self) -> Dict[str, float]:
        pass
