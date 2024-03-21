import enum


class MovieStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    PROCESSED = "processed"
    ERROR = "error"


class Languages(str, enum.Enum):
    EN = "en"
