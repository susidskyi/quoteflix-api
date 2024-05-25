import os
import re

from app.api.phrases.models import PhraseModel


def normalize_phrase_text(text: str) -> str:
    """
    Normalizes text by removing extra new lines, extra spaces, and punctuation,
    while handling Unicode characters.
    The punctuation leaved in the text: [!.?]
    """

    # Text replaces
    replaces_rules = (
        ("...", "."),
        ('".', "."),
        ('"!', "!"),
        ('"?', "?"),
    )

    # Replace text
    for old, new in replaces_rules:
        text = text.replace(old, new)

    # Replace punctuation rules
    punctuation_replaces_rules = (
        ('"#$%&()*+,-/:;<=>@[\\]^_`{|}~', " "),
        ("!?.", "{char} "),
        ("'", ""),
    )

    # Replace punctuations
    for puncuation, replacement in punctuation_replaces_rules:
        translation_table = {ord(char): replacement.format(char=char) for char in puncuation}

        text = text.translate(translation_table)

    # Remove new lines and extra spaces
    text = " ".join(text.split())

    return text.lower()


def ffmpeg_output_arg_from_phrase(phrase: PhraseModel, output_dir: str, file_extension: str) -> str:
    start_time = phrase.start_in_movie.total_seconds()
    end_time = phrase.end_in_movie.total_seconds()

    file_name = f"{phrase.id}{file_extension}"
    file_path = os.path.join(output_dir, file_name)

    return f'-ss {start_time} -filter:a "volume=1.5" -to {end_time} {file_path}'


def get_matched_phrase(full_phrase_text: str, normalized_search_text: str) -> str:
    """
    TODO: implement
    """
    return ""
