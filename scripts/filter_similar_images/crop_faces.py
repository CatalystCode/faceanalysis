#!/usr/bin/env python
import csv
from argparse import ArgumentParser, ArgumentTypeError, Namespace

from facenet_sandberg import align_dataset


def crop_directory(tsv_file: str, config_file: str, input_dir: str, output_dir: str, is_flat_dir: bool=True):
    align_dataset(
        config_file=config_file,
        input_dir=input_dir,
        output_dir=output_dir,
        is_flat_dir=is_flat_dir)
    with open(tsv_file) as fd:
        print(fd.read().replace(input_dir, output_dir))


def _cli() -> None:
    args = _parse_arguments()
    crop_directory(
        args.tsv_file,
        args.config_file,
        args.input_dir,
        args.output_dir,
        args.is_flat_dir)


def _parse_arguments() -> Namespace:
    parser = ArgumentParser()
    parser.add_argument('tsv_file',
                        type=str,
                        help='path to tsv file')
    parser.add_argument('config_file',
                        type=str,
                        help='path to the config file')
    parser.add_argument('input_dir',
                        type=str,
                        help='path to the image directory')
    parser.add_argument('output_dir',
                        type=str,
                        help='desired output path of cropped images')
    parser.add_argument('--is_flat_dir',
                        action='store_true',
                        help='Set this flag if the images are all in one flat directory.')
    return parser.parse_args()


if __name__ == '__main__':
    _cli()

# python crop_faces.py data.tsv crop_config.json ./images ./cropped_images --is_flat_dir
