from pathlib import Path
import os
import glob
import cv2 as cv

allowed_file_extensions = ['.png', '.jpg', '.jpeg']

# recursively load and normalize images using histogram equalization from OpenCV
def normalize_images(inputdirectory, outputdirectory):
    inputpath = Path(inputdirectory)
    outputpath = Path(outputdirectory)
    inputfiles = []

    for fe in allowed_file_extensions:
        inputfiles.extend(list(inputpath.glob('**/*' + fe)))

    for f in inputfiles:
        abs_file_path = Path.absolute(f)
        file_path = str(abs_file_path)
        output_file_name = get_output_file_name(f, inputpath, outputpath)
        print('normalizing image: ' + str(f) + ' to: ' + str(output_file_name))

        img_output = normalize_image(file_path)

        ensure_dir_exists_for_file(output_file_name)

        save_image(str(output_file_name), img_output)

def normalize_image(file_path):
        img = cv.imread(file_path)
        img_yuv = cv.cvtColor(img, cv.COLOR_BGR2YUV)

        img_yuv[:,:,0] = cv.equalizeHist(img_yuv[:,:,0])

        img_output = cv.cvtColor(img_yuv, cv.COLOR_YUV2BGR)
        return img_output

def save_image(file_path, img):
    cv.imwrite(file_path, img)

def get_output_file_name(f, inputpath, outputpath):
        parent_dir = f.parent

        if not inputpath.samefile(Path(parent_dir)):
            parent_dir_name = parent_dir.stem
            output_file_name = outputpath.joinpath(parent_dir_name, f.name)
        else:
            output_file_name = outputpath.joinpath(f.name)

        return output_file_name

def ensure_dir_exists_for_file(file_name):
        output_parent_dir = file_name.parent

        if not Path.exists(output_parent_dir):
            Path.mkdir(output_parent_dir)