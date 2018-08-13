import json
import math
import docker
import numpy as np
from argparse import ArgumentParser, Namespace
from sklearn.metrics import accuracy_score, recall_score, precision_score
from sklearn.metrics.pairwise import paired_distances
from sklearn.model_selection import KFold
from os.path import join, exists
from enum import Enum
from typing import List, Union, Tuple, cast

Match = Tuple[str, int, int]
Mismatch = Tuple[str, int, str, int]
Pair = Union[Match, Mismatch]

Path = Tuple[str, str]
Label = bool


class DistanceMetric(Enum):
    COSINE = 'cosine'
    EUCLIDEAN = 'euclidean'


class DistanceMetricException(Exception):
    pass


def evaluate(embeddings: np.ndarray,
             labels: np.ndarray,
             num_folds: int,
             distance_metric: DistanceMetric,
             subtract_mean: bool,
             divide_stddev: bool,
             threshold_start: float,
             threshold_end: float,
             threshold_step: float) -> Tuple[np.float, np.float, np.float]:
    thresholds = np.arange(threshold_start, threshold_end, threshold_step)
    embeddings1 = embeddings[0::2]
    embeddings2 = embeddings[1::2]
    accuracy, recall, precision = _score_k_fold(thresholds,
                                                embeddings1,
                                                embeddings2,
                                                labels,
                                                num_folds,
                                                distance_metric,
                                                subtract_mean,
                                                divide_stddev)
    return np.mean(accuracy), np.mean(recall), np.mean(precision)


def _read_pairs(pairs_filename: str) -> List[Pair]:
    pairs = []
    with open(pairs_filename, 'r') as pair_file:
        for line_num, line in enumerate(pair_file):
            if line_num != 0:
                pair = cast(Pair, tuple([int(i) if i.isdigit() else i
                                         for i in line.strip().split()]))
                pairs.append(pair)
    return pairs


def _get_paths_and_labels(image_dir: str,
                          pairs: List[Pair]) -> Tuple[List[Path], List[Label]]:
    paths = []
    labels = []
    for pair in pairs:
        _add_extension = (lambda rel_image_path, image_dir:
                          f'{rel_image_path}.jpg'
                          if exists(join(image_dir, f'{rel_image_path}.jpg'))
                          else f'{rel_image_path}.png')
        if len(pair) == 3:
            person, image_num_0, image_num_1 = cast(Match, pair)
            rel_image_path_no_ext = join(person,
                                         f'{person}_{image_num_0:04d}')
            rel_image_path_0 = _add_extension(rel_image_path_no_ext, image_dir)
            rel_image_path_no_ext = join(person,
                                         f'{person}_{image_num_1:04d}')
            rel_image_path_1 = _add_extension(rel_image_path_no_ext, image_dir)
            is_same_person = True
        elif len(pair) == 4:
            person_0, image_num_0, person_1, image_num_1 = cast(Mismatch, pair)
            rel_image_path_no_ext = join(person_0,
                                         f'{person_0}_{image_num_0:04d}')
            rel_image_path_0 = _add_extension(rel_image_path_no_ext, image_dir)
            rel_image_path_no_ext = join(person_1,
                                         f'{person_1}_{image_num_1:04d}')
            rel_image_path_1 = _add_extension(rel_image_path_no_ext, image_dir)
            is_same_person = False
        if (exists(join(image_dir, rel_image_path_0))
                and
                exists(join(image_dir, rel_image_path_1))):
            paths.append((rel_image_path_0, rel_image_path_1))
            labels.append(is_same_person)
        else:
            err = f'{rel_image_path_no_ext} with .jpg or .png extensions'
            raise FileNotFoundError(err)
    return paths, labels


def _distance_between_embeddings(
        embeddings1: np.ndarray,
        embeddings2: np.ndarray,
        distance_metric: DistanceMetric) -> np.ndarray:
    if distance_metric == DistanceMetric.EUCLIDEAN:
        return np.square(
            paired_distances(
                embeddings1,
                embeddings2,
                metric=DistanceMetric.EUCLIDEAN.value))
    elif distance_metric == DistanceMetric.COSINE:
        # Angular Distance: https://en.wikipedia.org/wiki/Cosine_similarity
        similarity = 1 - paired_distances(embeddings1,
                                          embeddings2,
                                          metric=DistanceMetric.COSINE.value)
        return np.arccos(similarity) / math.pi
    else:
        metrics = [f'{DistanceMetric.__qualname__}.{attr}'
                   for attr in dir(DistanceMetric)
                   if not callable(getattr(DistanceMetric, attr))
                   and not attr.startswith("__")]
        err = f"Undefined {DistanceMetric.__qualname__}. Choose from {metrics}"
        raise DistanceMetricException(err)


def _calculate_best_threshold(thresholds: np.ndarray,
                              dist: np.ndarray,
                              labels: np.ndarray) -> np.float:
    acc_train = np.zeros((len(thresholds)))
    for threshold_idx, threshold in enumerate(thresholds):
        predictions = np.less(dist, threshold)
        acc_train[threshold_idx] = accuracy_score(labels, predictions)
    best_threshold_index = np.argmax(acc_train)
    return thresholds[best_threshold_index]


def _score_k_fold(thresholds: np.ndarray,
                  embeddings1: np.ndarray,
                  embeddings2: np.ndarray,
                  labels: np.ndarray,
                  num_folds: int,
                  distance_metric: DistanceMetric,
                  subtract_mean: bool,
                  divide_stddev: bool) -> Tuple[np.ndarray,
                                                np.ndarray,
                                                np.ndarray]:
    k_fold = KFold(n_splits=num_folds, shuffle=False)
    accuracy = np.zeros((num_folds))
    recall = np.zeros((num_folds))
    precision = np.zeros((num_folds))
    splits = k_fold.split(np.arange(len(labels)))
    for fold_idx, (train_set, test_set) in enumerate(splits):
        train_embeddings = np.concatenate([embeddings1[train_set],
                                           embeddings2[train_set]])
        mean = np.mean(train_embeddings, axis=0) if subtract_mean else 0.0
        stddev = np.std(train_embeddings, axis=0) if divide_stddev else 1.0
        dist = _distance_between_embeddings((embeddings1 - mean) / stddev,
                                            (embeddings2 - mean) / stddev,
                                            distance_metric)
        best_threshold = _calculate_best_threshold(thresholds,
                                                   dist[train_set],
                                                   labels[train_set])
        predictions = np.less(dist[test_set], best_threshold)
        accuracy[fold_idx] = accuracy_score(labels[test_set], predictions)
        recall[fold_idx] = recall_score(labels[test_set], predictions)
        precision[fold_idx] = precision_score(labels[test_set], predictions)
    return accuracy, recall, precision


def _parse_arguments():
    parser = ArgumentParser()
    parser.add_argument('--image_dir',
                        type=str,
                        required=True,
                        help='Path to the image directory.')
    parser.add_argument('--pairs_file_name',
                        type=str,
                        required=True,
                        help='Filename of pairs.txt')
    parser.add_argument('--face_verification_container',
                        type=str,
                        required=True,
                        help='Name of docker container for face verification')
    parser.add_argument('--num_folds',
                        type=int,
                        required=True,
                        help='Number of cross validation folds')
    distance_metrics = [f'{attr}'
                        for attr in dir(DistanceMetric)
                        if not callable(getattr(DistanceMetric, attr))
                        and not attr.startswith("__")]
    parser.add_argument(
        '--distance_metric',
        type=str,
        required=True,
        help=f"Distance metric for face verification: {distance_metrics}.")
    parser.add_argument('--threshold_start',
                        type=float,
                        required=True,
                        help='Start value for distance threshold.')
    parser.add_argument('--threshold_end',
                        type=float,
                        required=True,
                        help='End value for distance threshold')
    parser.add_argument(
        '--embedding_size',
        type=int,
        required=True,
        help='Size of face vectors from face_verification_container.')
    parser.add_argument(
        '--threshold_step',
        type=float,
        required=True,
        help='Step size for iterating in cross validation search.')
    parser.add_argument(
        '--subtract_mean',
        action='store_true',
        help=f"Subtract mean of embeddings before distance calculation.")
    parser.add_argument(
        '--divide_stddev',
        action='store_true',
        help=f"Divide embeddings by stddev before distance calculation.")
    return parser.parse_args()


def _main(args: Namespace) -> None:
    args = _parse_arguments()
    pairs = _read_pairs(args.pairs_file_name)
    pair_paths, labels = _get_paths_and_labels(args.image_dir, pairs)
    flat_paths = [path for pair in pair_paths for path in pair]
    client = docker.from_env()
    volumes = {args.image_dir: {'bind': '/images', 'mode': 'ro'}}
    img_mount = ' '.join([f'/images/{path}' for path in flat_paths])
    stdout = client.containers.run(args.face_verification_container,
                                   img_mount,
                                   volumes=volumes,
                                   auto_remove=True,
                                   environment=["PREALIGNED=true"])
    response = json.loads(stdout.decode('utf-8').strip())
    assert(max([len(i) for i in response['faceVectors']]) <= 1)
    embeddings = np.asarray([[0] * args.embedding_size
                             if not embedding else embedding[0]
                             for embedding in response['faceVectors']])

    labels = np.asarray(labels)
    distance_metric = getattr(DistanceMetric, args.distance_metric)
    accuracy, recall, precision = evaluate(embeddings,
                                           labels,
                                           args.num_folds,
                                           distance_metric,
                                           args.subtract_mean,
                                           args.divide_stddev,
                                           args.threshold_start,
                                           args.threshold_end,
                                           args.threshold_step)
    print(f'Accuracy: {accuracy}')
    print(f'Recall: {recall}')
    print(f'Precision: {precision}')


def _cli() -> None:
    args = _parse_arguments()
    _main(args)


if __name__ == '__main__':
    _cli()
