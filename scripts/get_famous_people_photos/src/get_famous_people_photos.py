import collections
import glob
import gzip
import itertools
import os
import pickle
import time
from ctypes import c_int
from functools import wraps
from io import BytesIO
from itertools import islice
from multiprocessing import Lock, Manager, Pool, Queue, Value
from multiprocessing.dummy import Pool as ThreadPool
from os import getenv
from time import time
from typing import Generator, List, Set

import cv2
import dhash
import numpy as np
import progressbar as pb
import pybktree
import requests
import tensorflow as tf
from facenet_sandberg import face
from pathos.multiprocessing import ProcessPool
from PIL import Image
from requests import exceptions

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
BING_API_KEY = str(getenv('BING_API_KEY', ''))
NUM_THREADS = int(getenv('NUM_THREADS', 50))
NUM_PROCESSES = min(int(getenv('NUM_PROCESSES', 4)), os.cpu_count())
MAX_RESULTS = 150

URL = "https://api.cognitive.microsoft.com/bing/v7.0/images/search"
HEADERS = {"Ocp-Apim-Subscription-Key": BING_API_KEY}

IMAGE_HASH = collections.namedtuple('IMAGE_HASH', 'bits url')

timer: pb.ProgressBar = None
counter: Value = Value(c_int)  # defaults to 0
counter_lock: Lock = Lock()


facenet_model_checkpoint = "../../common/models/20180402-114759.pb"
famous_people_file = '../../common/text_files/famous_people.txt.gz'
url_file = '../../common/text_files/image_urls.data'
images_directory = '../../common/images/'


def increment(add_amount: int=1):
    with counter_lock:
        counter.value += add_amount


def reset():
    global timer
    with counter_lock:
        counter.value == 0
    timer = None


def get_photos(famous_people_file: str):
    unique_people = set()
    with gzip.open(famous_people_file, mode='rt', encoding='utf-8') as fp:
        unique_people = {line.strip() for line in fp}
    total_count = len(unique_people)

    urls, people = fetch_urls_multithread(unique_people, total_count)
    reset()

    matched_urls, people = multiprocess(
        safe_match_images, urls, people, total_count, 'matching images')
    reset()

    deduped_urls, people = multiprocess(
        dedupe_images, matched_urls, people, total_count, 'deduping images')
    reset()

    multiprocess(download_urls, deduped_urls, people,
                 total_count, 'downloading images')
    timer.finish()


def fetch_urls_multithread(
        unique_people: Set[str], total_count: int) -> (List[List[str]], List[str]):
    print("[INFO] Fetching image urls with {} threads".format(NUM_THREADS))
    global timer
    widgets_urls = ['Fetching urls: ', pb.Percentage(), ' ',
                    pb.Bar(marker=pb.RotatingMarker()), ' ', pb.ETA()]
    # Check if we have cached our image urls
    if not os.path.isfile(url_file):
        timer = pb.ProgressBar(widgets=widgets_urls,
                               maxval=total_count).start()

        thread_pool = ThreadPool(NUM_THREADS)
        urls_and_people = thread_pool.imap(get_urls, unique_people)
        thread_pool.close()
        thread_pool.join()

        with open(url_file, 'wb') as filehandle:
            pickle.dump(urls_and_people, filehandle)
    else:
        with open(url_file, 'rb') as filehandle:
            urls_and_people = pickle.load(filehandle)
    urls, people = zip(*urls_and_people)
    print("[INFO] Done fetching image urls")
    return urls, people


def multiprocess(function: any,
                 all_urls: List[List[str]],
                 people: List[str],
                 total_count: int,
                 info: str) -> (List[List[str]],
                                List[str]):
    print("[INFO] {} with {} processes".format(info, NUM_PROCESSES))
    global timer
    widgets_match = ['{}: '.format(info), pb.Percentage(), ' ',
                     pb.Bar(marker=pb.RotatingMarker()), ' ', pb.ETA()]
    timer = pb.ProgressBar(widgets=widgets_match, maxval=total_count).start()

    if NUM_PROCESSES > 1:
        process_pool = ProcessPool(NUM_PROCESSES)
        urls_and_people = process_pool.imap(function, all_urls, people)
        process_pool.close()
        process_pool.join()
        filtered_urls, people = zip(*urls_and_people)
    else:
        filtered_urls = []
        for urls, person in zip(all_urls, people):
            filtered, person = function(urls, person)
            filtered_urls.append(filtered)
    print("[INFO] Done {}".format(info))
    return filtered_urls, people


def get_urls(person: str) -> (List[str], str):
    params = {"q": person, "count": MAX_RESULTS, "imageType": "photo"}
    search = requests.get(URL, headers=HEADERS, params=params)
    search.raise_for_status()
    results = search.json()
    thumbnail_urls = [img["thumbnailUrl"] +
                      '&c=7&w=250&h=250' for img in results["value"]]
    # update counter
    increment()
    timer.update(int(counter.value))
    return thumbnail_urls, person


def safe_match_images(*args, **kwargs):
    try:
        return match_images(*args, **kwargs)
    except Exception as e:
        print(e)


def match_images(thumbnail_urls: List[str], person: str) -> (List[str], str):
    urls = set()
    directory = images_directory + person
    # Skip directories that have already been made
    if not os.path.exists(directory) and len(thumbnail_urls) > 10:
        # Make sure all the matches are of the same person
        try:
            identifier = face.Identifier(
                threshold=1.0, facenet_model_checkpoint=facenet_model_checkpoint)
            images = map(identifier.download_image, thumbnail_urls)
            all_faces: Generator[List[face.Face], None, None] = identifier.detect_encode_all(
                images, urls=thumbnail_urls, save_memory=True)
            # Flattens the lists of faces into one generator
            faces = (face for faces in all_faces for face in faces)
            # import pdb;pdb.set_trace()
            anchor_embedding = list(islice(faces, 1))[0].embedding
            # Assume first image is of the right person and check other images
            # are of the same person
            for other in faces:
                is_match, distance = identifier.compare_embedding(
                    anchor_embedding, other.embedding)
                if is_match:
                    urls.add(other.url)
            identifier.tear_down()
            del identifier
        except Exception as e:
            print(e)
    # Update counter
    increment()
    timer.update(int(counter.value))
    return list(urls), person


def dedupe_images(matched_urls: List[str], person: str) -> (List[str], str):
    """Hashes images and removes nearly identical images

    Arguments:
        matched_urls {str[] or set} -- list or set of urls to dedupe
        person{str} -- name of person

    Returns:
        str[] -- list of deduped urls
    """
    image_hashes = [IMAGE_HASH(url_to_img_hash(url), url)
                    for url in matched_urls]
    tree = pybktree.BKTree(image_distance, image_hashes)
    # this makes images saved in order of similarity so we can spot duplicates
    # easier
    sorted_image_hashes = sorted(tree)
    to_discard = []
    urls_to_keep = set()
    for image_hash in sorted_image_hashes:
        if image_hash not in to_discard:
            # gets pictures within a hamming distance of 5
            matches = tree.find(image_hash, 5)
            for match in matches:
                if match[1].url != image_hash.url:
                    to_discard.append(match[1])
            urls_to_keep.add(image_hash.url)
    # Update counter
    increment()
    timer.update(int(counter.value))
    return list(urls_to_keep), person


def download_urls(deduped_urls: List[str], person: str):
    """Downloads the urls to the image directory

    Arguments:
        deduped_urls {str[]} -- list of urls to download
        person {str} -- name of the person
    Returns:
        None, None -- only to follow same function format
    """

    if len(deduped_urls) > 5:
        directory = images_directory + person
        os.makedirs(directory, exist_ok=True)
        for count, url in enumerate(deduped_urls):
            image = url_to_image(url)
            image_path = os.path.join(directory, str(count))
            image.save(image_path + '.jpg')
    # update counter
    increment()
    timer.update(int(counter.value))
    return None, None


def url_to_image(url: str) -> np.ndarray:
    """Converts a url to a PIL image

    Arguments:
        url {str} -- url to image

    Returns:
        np.ndarray -- image array
    """

    image_data = requests.get(url)
    image_data.raise_for_status()
    image = Image.open(BytesIO(image_data.content))
    return image


def url_to_img_hash(url: str) -> int:
    """Converts a url to an image hash

    Arguments:
        url {str} -- url to image

    Returns:
        int -- hash of image
    """

    image = url_to_image(url)
    image_hash = dhash.dhash_int(image)
    return image_hash


def image_distance(x: IMAGE_HASH, y: IMAGE_HASH) -> int:
    """Calculates the distance between to image hashes

    Arguments:
        x {IMAGE_HASH} -- IMAGE_HASH object for image 1
        y {IMAGE_HASH} -- IMAGE_HASH object for image 2

    Returns:
        int -- hamming distance of two image hashes
    """

    return pybktree.hamming_distance(x.bits, y.bits)


if __name__ == "__main__":
    get_photos(famous_people_file)
