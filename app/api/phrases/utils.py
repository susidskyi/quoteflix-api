import os
import string

from app.api.phrases.models import PhraseModel


def normalize_phrase_text(text: str) -> str:
    """
    Normalizes text by removing new lines, extra spaces, and punctuation,
    while handling Unicode characters.

    """
    # Remove punctuation using a custom translation table
    translation_table = dict.fromkeys(ord(char) for char in string.punctuation)
    text = text.translate(translation_table)

    # Remove new lines and extra spaces
    text = " ".join(text.split())

    # Lower case
    text = text.lower()

    return text


def ffmpeg_output_arg_from_phrase(
    phrase: PhraseModel, output_dir: str, file_extension: str
) -> str:
    start_time = phrase.start_in_movie.total_seconds()
    end_time = phrase.end_in_movie.total_seconds()

    file_name = f"{phrase.id}{file_extension}"
    file_path = os.path.join(output_dir, file_name)

    return f"-ss {start_time} -to {end_time} {file_path}"
