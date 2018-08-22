from abc import ABC
from abc import abstractmethod
from parser.pair import Pair
from typing import Generic
from typing import Iterable
from typing import TypeVar

T = TypeVar('T')


class Calculator(ABC, Generic[T]):

    @abstractmethod
    def calculate(self, pair: Iterable[Pair]) -> T:
        pass
