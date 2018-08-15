import math
from typing import List, Union, cast
import numpy as np
from sklearn.metrics.pairwise import paired_distances
from calculator import Calculator
from metrics import DistanceMetric, DistanceMetricException
from pair import Pair


class DistanceCalculator(Calculator):

    def __init__(self, distance_metric: Union[str, DistanceMetric]) -> None:
        if type(distance_metric) == str:
            self._distance_metric = getattr(DistanceMetric,
                                            cast(str, distance_metric))
        else:
            self._distance_metric = distance_metric

    def calculate(self, pairs: List[Pair]) -> np.ndarray:
        embeddings1 = []
        embeddings2 = []
        for pair in pairs:
            embeddings1.append(pair.image1)
            embeddings2.append(pair.image2)
        if self._distance_metric == DistanceMetric.EUCLIDEAN_SQUARED:
            return np.square(
                paired_distances(
                    embeddings1,
                    embeddings2,
                    metric='euclidean'))
        elif self._distance_metric == DistanceMetric.ANGULAR_DISTANCE:
            # Angular Distance: https://en.wikipedia.org/wiki/Cosine_similarity
            similarity = 1 - paired_distances(
                embeddings1,
                embeddings2,
                metric='cosine')
            return np.arccos(similarity) / math.pi
        else:
            metrics = [f'{DistanceMetric.__qualname__}.{attr}'
                       for attr in dir(DistanceMetric)
                       if not callable(getattr(DistanceMetric, attr))
                       and not attr.startswith("__")]
            err = f"Undefined {DistanceMetric.__qualname__}. \
Choose from {metrics}"
            raise DistanceMetricException(err)
