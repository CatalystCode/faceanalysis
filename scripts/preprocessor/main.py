import sys
import argparse
from processor import normalize_images

parser = argparse.ArgumentParser()
parser.add_argument('-i', '--input',
                    help='the path to the input directory',
                    required=True)
parser.add_argument('-o', '--output',
                    help='the path to the output directory',
                    required=True)


def main(argv):
    args = parser.parse_args()
    inputdirectory = args.input
    outputdirectory = args.output

    print('Input directory is {}.'.format(inputdirectory))
    print('Output directory is {}.'.format(outputdirectory))

    normalize_images(inputdirectory, outputdirectory)


if __name__ == "__main__":
    main(sys.argv[1:])
