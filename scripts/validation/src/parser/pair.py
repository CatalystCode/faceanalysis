from dataclasses import dataclass
from typing import Generic
from typing import TypeVar

T = TypeVar('T')


@dataclass
class Pair(Generic[T]):  # pylint: disable=unsubscriptable-object
    image1: T
    image2: T
    is_match: bool
