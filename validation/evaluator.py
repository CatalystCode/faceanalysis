from argparse import Namespace
from typing import Dict
import numpy as np
from sklearn.metrics import accuracy_score, precision_score, recall_score
from container_parser import ContainerParser
from distance_calculator import DistanceCalculator
from face_vector_parser import FaceVectorParser
from pair_parser import PairParser
from threshold_calculator import ThresholdCalculator


class Evaluator:

    def __init__(self,
                 face_vector_parser: FaceVectorParser,
                 threshold_calculator: ThresholdCalculator,
                 distance_calculator: DistanceCalculator) -> None:
        self._face_vector_parser = face_vector_parser
        self._threshold_calculator = threshold_calculator
        self._distance_calculator = distance_calculator

    @classmethod
    def create_evaluator(cls, args: Namespace) -> 'Evaluator':
        pair_parser = PairParser(args.pairs_fname, args.image_dir)
        container_parser = ContainerParser(pair_parser,
                                           args.container_name,
                                           args.prealigned_flag)
        face_vector_parser = FaceVectorParser(
            container_parser,
            args.embedding_size,
            args.distance_metric,
            args.remove_empty_embeddings_flag)
        threshold_calculator = ThresholdCalculator(args.distance_metric,
                                                   args.threshold_metric,
                                                   args.threshold_start,
                                                   args.threshold_end,
                                                   args.threshold_step)
        distance_calculator = DistanceCalculator(args.distance_metric)
        return cls(face_vector_parser,
                   threshold_calculator,
                   distance_calculator)

    def get_metrics(self) -> Dict[str, float]:
        return self._face_vector_parser.get_metrics()

    def evaluate(self) -> Dict[str, float]:
        pairs = self._face_vector_parser.get_pairs()
        threshold = self._threshold_calculator.calculate(pairs)
        dist = self._distance_calculator.calculate(pairs)
        predictions = np.less(dist, threshold)
        labels = [pair.is_match for pair in pairs]
        evaluation_results = {
            'accuracy': accuracy_score(labels, predictions),
            'recall': recall_score(labels, predictions),
            'precision': precision_score(labels, predictions)
        }
        return evaluation_results
