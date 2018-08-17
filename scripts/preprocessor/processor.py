from pathlib import Path

from skimage import exposure
from skimage import io

allowed_file_extensions = ['.png', '.jpg', '.jpeg']


def normalize_images(inputdirectory, outputdirectory):
    inputpath = Path(inputdirectory)
    outputpath = Path(outputdirectory)

    inputfiles = []

    for extension in allowed_file_extensions:
        inputfiles.extend(list(inputpath.glob('**/*' + extension)))

    for infile in inputfiles:
        abs_file_path = Path.absolute(infile)
        file_path = str(abs_file_path)
        output_file_name = get_output_file_name(infile, inputpath, outputpath)
        print('normalizing image: {} to: {}'.format(infile, output_file_name))

        img_output = normalize_image(file_path)
        ensure_dir_exists_for_file(output_file_name)
        save_image(str(output_file_name), img_output)


def normalize_image(file_path):
    img = io.imread(file_path)
    img_output = exposure.equalize_adapthist(img)
    return img_output


def save_image(file_path, img):
    io.imsave(file_path, img)


def get_output_file_name(infile, inputpath, outputpath):
    parent_dir = infile.parent

    if not inputpath.samefile(Path(parent_dir)):
        parent_dir_name = parent_dir.stem
        output_file_name = outputpath.joinpath(parent_dir_name, infile.name)
    else:
        output_file_name = outputpath.joinpath(infile.name)

    return output_file_name


def ensure_dir_exists_for_file(file_name):
    output_parent_dir = file_name.parent

    if not Path.exists(output_parent_dir):
        Path.mkdir(output_parent_dir)
