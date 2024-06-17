import datetime
import os
import re
from pathlib import Path

from app.api.phrases.models import PhraseModel


def normalize_phrase_text(phrase: str) -> str:
    # Step 1
    # Replacing \n with space
    phrase = phrase.replace("\\n", " ")

    # Step 2
    # Replacing with space: #$%&()*+,/:;<=>@[\\]^_`{|}~"
    punctuations_to_replace_with_space = r'[\#\$%&()*+,/:;<=>@\[\]^\\_`{|}~\-"]'
    phrase = re.sub(punctuations_to_replace_with_space, " ", phrase)

    # Step 3
    # Replace ?!. with . if they are repeated
    phrase = re.sub(r"[?!.]+", ". ", phrase)

    # Step 4
    # Remove extra spaces
    phrase = re.sub(r"\s+", " ", phrase)

    # Step 5
    # Temporary solution (or maybe permanent):
    # make all words surrounded with spaces. It helps to avoid
    # results like "that" when we search for "hat" etc.
    phrase = re.sub(r"\s*\.\s*", " . ", phrase)

    # Step 6
    # Make sentence lowercase and strip spaces
    phrase = phrase.lower().strip()

    # Step 7
    # Add spaces on the left and right of the whole phrase
    return " " + phrase + " "


def get_ffmpeg_trim_cmd_for_phrase(phrase: PhraseModel, movie_path: Path, output_dir: Path) -> str:
    movie_ext = movie_path.suffix
    start_arg = f"-ss {phrase.start_in_movie}"
    end_arg = f"-to {phrase.end_in_movie}"
    output_filename = f"{phrase.id}{movie_ext}"
    output_path_arg = Path(output_dir, output_filename)

    return f"ffmpeg {start_arg} {end_arg} -i {movie_path} {output_path_arg}"


def get_matched_phrase(normalized_search_text: str, full_text: str) -> str:
    search_words = normalized_search_text.replace(" . ", " ").strip().split()
    matched_phrase = None

    if len(search_words) == 1:
        pattern = f"({search_words[0]})"
        matched_phrase = re.search(pattern, full_text, re.IGNORECASE | re.DOTALL)
    elif len(search_words) > 1:
        pattern = rf"({search_words[0]}"

        for word in search_words[1:]:
            pattern += rf"[^\b{word}\b]*{word}"

        pattern += ")"
        matched_phrase = re.search(pattern, full_text, re.IGNORECASE | re.DOTALL)

    return matched_phrase.group(1) if matched_phrase else ""


def format_duration(duration: datetime.timedelta) -> str:
    hours, remainder = divmod(duration.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    milliseconds = duration.microseconds // 1000

    return f"{hours:02}:{minutes:02}:{seconds:02}.{milliseconds:03}"


def parse_duration(duration_str: str) -> datetime.timedelta:
    """
    CURRENTLY NOT USED ANYWHERE
    """
    hours, minutes, seconds_milliseconds = duration_str.split(":")
    seconds, milliseconds = seconds_milliseconds.split(".")

    return datetime.timedelta(
        hours=int(hours),
        minutes=int(minutes),
        seconds=int(seconds),
        milliseconds=int(milliseconds),
    )
