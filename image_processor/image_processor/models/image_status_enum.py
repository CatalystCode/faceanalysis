import enum


class ImageStatusEnum(enum.Enum):
    finished_processing = 5
    processing = 4
    on_queue = 3
    uploaded = 2
    not_yet_uploaded = 1
