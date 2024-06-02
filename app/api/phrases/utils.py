import os
import re

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


def ffmpeg_output_arg_from_phrase(phrase: PhraseModel, output_dir: str, file_extension: str) -> str:
    start_time = phrase.start_in_movie.total_seconds() + 0.5
    end_time = phrase.end_in_movie.total_seconds() + 0.5

    file_name = f"{phrase.id}{file_extension}"
    file_path = os.path.join(output_dir, file_name)

    return f'-ss {start_time} -filter:a "volume=1.5" -to {end_time} {file_path}'


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
