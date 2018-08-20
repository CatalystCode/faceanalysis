from abc import ABC, abstractmethod
from typing import Generic, List, TypeVar

from pair import Pair

T = TypeVar('T')


class Calculator(ABC, Generic[T]):

    @abstractmethod
    def calculate(self, pair: List[Pair]) -> T:
        pass
