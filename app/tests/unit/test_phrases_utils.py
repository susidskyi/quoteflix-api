import datetime
import pathlib

import pytest

from app.api.phrases.models import PhraseModel
from app.api.phrases.utils import (
    ffmpeg_output_arg_from_phrase,
    format_duration,
    get_matched_phrase,
    normalize_phrase_text,
    parse_duration,
)


@pytest.mark.parametrize(
    ("phrase_text", "expected_output"),
    [
        ('This\n\nis a    \n   test   string\n\n"', " this is a test string "),
        ("Hello, there! How are you doing?", " hello there . how are you doing . "),
        ("I'm afraid so, professor.\nThe good and the bad.", " i'm afraid so professor . the good and the bad . "),
        ("36?!!Last year I had 37", " 36 . last year i had 37 "),
        ("- They really are...\n- The only family he has.", " they really are . the only family he has . "),
        ("Ah, Professor, I would trust Hagrid\nwith my life.", " ah professor i would trust hagrid with my life . "),
        ("ThIs StRiNg HaS UpPeRcAsE LeTtErS", " this string has uppercase letters "),
        (
            "The quick brown fox jumps over the lazy dog! 12345",
            " the quick brown fox jumps over the lazy dog . 12345 ",
        ),
        ('Text+text,,Text: "text". Text.text', " text text text text . text . text "),
        ("Text...some more text?", " text . some more text . "),
        ("Кириллица, Umlaut ä, French: É", " кириллица umlaut ä french é "),
        ("Until he's ready.", " until he's ready . "),
    ],
)
def test_normalize_phrase_text(
    phrase_text: str,
    expected_output: str,
):
    result = normalize_phrase_text(phrase_text)
    assert result == expected_output


def test_ffmpeg_output_arg_from_phrase(phrase_model_data: PhraseModel, tmp_path: pathlib.Path):
    phrase_model_data.start_in_movie = datetime.timedelta(seconds=5)
    phrase_model_data.end_in_movie = datetime.timedelta(seconds=10)

    expected_path = pathlib.PurePath(tmp_path, f"{phrase_model_data.id}.mp4")
    expected_result = f'-ss 5.0 -filter:a "volume=1.5" -to 10.0 {expected_path}'

    result = ffmpeg_output_arg_from_phrase(phrase_model_data, tmp_path, ".mp4")

    assert result == expected_result


@pytest.mark.parametrize(
    ("search_text", "full_phrase", "expected_result"),
    [
        ("i'm afraid so", "I'm afraid so, professor. The good and the bad.", "I'm afraid so"),
        ("ah professor", "Ah, Professor, I would trust Hagrid\nwith my life.", "Ah, Professor"),
        ("hagrid with my life", "Ah, Professor, I would trust Hagrid\nwith my life.", "Hagrid\nwith my life"),
        ("it's safe, leaving him", "it's safe,\nleaving him with these people?", "it's safe,\nleaving him"),
        ("they really are", "- They really are...\n- The only family he has.", "They really are"),
    ],
)
def test_get_matched_phrase(
    search_text: str,
    full_phrase: str,
    expected_result: str,
):
    result = get_matched_phrase(normalize_phrase_text(search_text), full_phrase)

    assert result == expected_result


@pytest.mark.parametrize(
    ("timedelta", "expected_str"),
    [
        (datetime.timedelta(seconds=5), "00:00:05.000"),
        (datetime.timedelta(seconds=60), "00:01:00.000"),
        (datetime.timedelta(seconds=3600), "01:00:00.000"),
        (datetime.timedelta(milliseconds=500), "00:00:00.500"),
    ],
)
def test_format_duration(timedelta: datetime.timedelta, expected_str: str):
    result = format_duration(timedelta)

    assert result == expected_str


@pytest.mark.parametrize(
    ("duration_str", "expected_timedelta"),
    [
        ("00:00:05.000", datetime.timedelta(seconds=5)),
        ("00:01:00.000", datetime.timedelta(seconds=60)),
        ("01:00:00.000", datetime.timedelta(seconds=3600)),
        ("00:00:00.500", datetime.timedelta(milliseconds=500)),
    ],
)
def test_parse_duration(duration_str: str, expected_timedelta: datetime.timedelta):
    result = parse_duration(duration_str)

    assert result == expected_timedelta
