import datetime
import pathlib

import pytest

from app.api.phrases.models import PhraseModel
from app.api.phrases.utils import ffmpeg_output_arg_from_phrase, normalize_phrase_text


@pytest.mark.parametrize(
    ("phrase_text", "expected_output"),
    [
        ('This\n\nis a    \n   test   string\n\n"', "this is a test string"),
        ("Hello, there! How are you doing?", "hello there! how are you doing?"),
        ("ThIs StRiNg HaS UpPeRcAsE LeTtErS", "this string has uppercase letters"),
        (
            "The quick brown fox jumps over the lazy dog! 12345",
            "the quick brown fox jumps over the lazy dog! 12345",
        ),
        ('Text+text,,Text: "text". Text.text', "text text text text. text. text"),
        ("Text...some more text?", "text. some more text?"),
        ("Кириллица, Umlaut ä, French: É", "кириллица umlaut ä french é"),
        ("Until he's ready.", "until hes ready."),
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
