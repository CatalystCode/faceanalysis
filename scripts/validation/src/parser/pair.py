from typing import Generic
from typing import TypeVar

from dataclasses import dataclass

T = TypeVar('T')


@dataclass
class Pair(Generic[T]):
    image1: T
    image2: T
    is_match: bool
