#!/usr/bin/env python
import collections
import csv
from argparse import ArgumentParser, ArgumentTypeError, Namespace
from typing import Callable, List, Set, Tuple

import dhash
import numpy as np
from PIL import Image


def get_image_from_path(image_path: str) -> np.ndarray:
    image = Image.open(image_path)
    return image


def image_to_hash(image: np.ndarray) -> int:
    image_hash = dhash.dhash_int(image)
    return image_hash


def image_distance(x: int, y: int) -> int:
    """Calculates the distance between to image hashes
    Returns:
        int -- hamming distance of two image hashes
    """
    return dhash.get_num_bits_different(x, y)


def read_tsv(tsv_file: str):
    lines = []
    with open(tsv_file) as fd:
        rd = csv.reader(fd, delimiter="\t", quotechar='"')
        for line in rd:
            lines.append(line)
    return lines


def print_tsv(image1: str, image2: str, distance: str):
    output = '{}\t{}\t{}'.format(image1, image2, distance)
    print(output)


def dedupe_tsv(tsv_file: str, min_distance: float, hash_cutoff: int):
    tsv = read_tsv(tsv_file)
    for line in tsv:
        image1, image2, distance = line
        if float(distance) > min_distance:
            image1_hash = image_to_hash(get_image_from_path(image1))
            image2_hash = image_to_hash(get_image_from_path(image2))
            hash_distance = image_distance(image1_hash, image2_hash)
            if hash_distance > hash_cutoff:
                print_tsv(image1, image2, str(hash_distance))


def restricted_float(x):
    x = float(x)
    if x < 0.0 or x > 1.0:
        raise ArgumentTypeError("%r not in range [0.0, 1.0]" % (x,))
    return x


def _cli() -> None:
    args = _parse_arguments()
    dedupe_tsv(
        args.tsv_file,
        args.min_distance,
        args.hash_cutoff)


def _parse_arguments() -> Namespace:
    parser = ArgumentParser()
    parser.add_argument('tsv_file',
                        type=str,
                        help='path to tsv file')
    parser.add_argument('min_distance',
                        type=restricted_float,
                        help='min similarity to consider for duplicates')
    parser.add_argument('hash_cutoff',
                        type=int,
                        help='Image hash hamming distance for cutoff')
    return parser.parse_args()


if __name__ == '__main__':
    _cli()


# python dedupe_tsv.py data.tsv 0.98 50
