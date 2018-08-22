from dataclasses import dataclass
from typing import Generic
from typing import TypeVar

T = TypeVar('T')

# pylint: disable=unsubscriptable-object
@dataclass
class Pair(Generic[T]):
    image1: T
    image2: T
    is_match: bool
