from abc import ABC
from abc import abstractmethod
from typing import Generic
from typing import List
from typing import TypeVar

from pair import Pair

T = TypeVar('T')


class Calculator(ABC, Generic[T]):

    @abstractmethod
    def calculate(self, pair: List[Pair]) -> T:
        pass
