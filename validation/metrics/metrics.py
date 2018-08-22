from enum import Enum
from enum import auto

from dataclasses import dataclass


@dataclass
class EvaluationMetric:
    accuracy: float
    recall: float
    precision: float


@dataclass
class FaceVectorMetric:
    num_expected: int
    num_missing: int
    percentage_missing: float


class DistanceMetric(Enum):
    ANGULAR_DISTANCE = auto()
    EUCLIDEAN_SQUARED = auto()


class ThresholdMetric(Enum):
    ACCURACY = auto()
    PRECISION = auto()
    RECALL = auto()
    F1 = auto()


class DistanceMetricException(Exception):
    pass


class ThresholdMetricException(Exception):
    pass
