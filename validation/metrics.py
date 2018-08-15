from enum import Enum, auto


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
