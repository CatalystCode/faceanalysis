from enum import Enum


class ImageStatusEnum(Enum):
    finished_processing = 4
    processing = 3
    on_queue = 2
    uploaded = 1
