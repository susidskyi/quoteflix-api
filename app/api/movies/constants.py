import enum


class MovieStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    PROCESSED = "processed"
    ERROR = "error"


class Languages(str, enum.Enum):
    EN = "en"


SUPPORTED_VIDEO_EXTENSIONS = ["mp4", "mkv", "avi", "mov", "mpeg", "mpg", "webm"]
SUPPORTED_SUBTITLES_EXTENSIONS = ["srt", "vtt"]
