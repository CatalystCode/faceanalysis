from enum import Enum
from enum import auto


class EvaluationMetric:
    def __init__(self,
                 accuracy: float,
                 recall: float,
                 precision: float) -> None:
        self._accuracy = accuracy
        self._recall = recall
        self._precision = precision

    @property
    def accuracy(self):
        return self._accuracy

    @property
    def recall(self):
        return self._recall

    @property
    def precision(self):
        return self._precision


class FaceVectorMetric:
    def __init__(self,
                 num_expected: int,
                 num_missing: int,
                 percentage_missing: float) -> None:
        self._num_expected = num_expected
        self._num_missing = num_missing
        self._percentage_missing = percentage_missing

    @property
    def num_expected(self):
        return self._num_expected

    @property
    def num_missing(self):
        return self._num_missing

    @property
    def percentage_missing(self):
        return self._percentage_missing


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
