from processor import normalize_images


def _main(inputdirectory, outputdirectory):
    print('Input directory is {}.'.format(inputdirectory))
    print('Output directory is {}.'.format(outputdirectory))

    normalize_images(inputdirectory, outputdirectory)


def _cli():
    from argparse import ArgumentParser
    from argparse import ArgumentTypeError
    from os.path import isdir

    def directory_type(arg):
        if not isdir(arg):
            raise ArgumentTypeError('{} is not a directory'.format(arg))
        return arg

    parser = ArgumentParser()
    parser.add_argument('-i', '--input',
                        type=directory_type,
                        help='the path to the input directory',
                        required=True)
    parser.add_argument('-o', '--output',
                        type=directory_type,
                        help='the path to the output directory',
                        required=True)
    args = parser.parse_args()

    _main(args.input, args.output)


if __name__ == "__main__":
    _cli()
