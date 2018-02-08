import enum


class ImageStatusEnum(enum.Enum):
    finished_processing = 4
    processing = 3
    on_queue = 2
    uploaded = 1
