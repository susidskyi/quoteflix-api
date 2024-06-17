import datetime
import json
import subprocess
from itertools import batched
from pathlib import Path

import click
import srt
from pydantic import BaseModel


class Phrase(BaseModel):
    id: str | None = None
    start: datetime.timedelta
    end: datetime.timedelta
    text: str

    @property
    def output_name(self) -> str:
        if self.id:
            return f"{self.id}"

        return f"{self.start}-{self.end}"


def srt_parser(file_path: Path) -> list[Phrase]:
    with open(file_path) as f:
        content = f.read()

        return [
            Phrase(
                start=phrase.start,
                end=phrase.end,
                text=phrase.content,
            )
            for phrase in srt.parse(content)
        ]


def json_parser(file_path: Path) -> list[Phrase]:
    with open(file_path) as f:
        content = f.read()
        json_content = json.loads(content)
        return [
            Phrase(
                id=phrase["id"],
                start=phrase["start_in_movie"],
                end=phrase["end_in_movie"],
                text=phrase["full_text"],
            )
            for phrase in json_content
        ]


PHRASES_FILE_PARSERS_MAPPING = {
    ".srt": srt_parser,
    ".json": json_parser,
}


def handle_create_subtitles(phrases: list[Phrase], output_dir: Path) -> None:
    for phrase in phrases:
        subtitle = srt.Subtitle(
            index=1,
            start=datetime.timedelta(),
            end=phrase.end,
            content=phrase.text,
        )

        output_path = output_dir.joinpath(f"{phrase.output_name}.srt")

        with open(output_path, "w") as f:
            f.write(srt.compose([subtitle]))


@click.command()
@click.option("--movie-path", "-m", required=True, type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--phrases-path", "-p", required=True, type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option(
    "--output-dir",
    "-o",
    required=True,
    type=click.Path(exists=True, dir_okay=True, file_okay=False, path_type=Path),
)
@click.option("--volume", "-v", default=1.5, type=click.FloatRange(min=0.0))
@click.option("--create-subtitles", "-s", default=False, is_flag=True)
@click.option("--limit", "-l", default=99999, type=click.IntRange(min=1))
def create_scenes(
    movie_path: Path,
    phrases_path: Path,
    output_dir: Path,
    volume: float,
    create_subtitles: bool,
    limit: int,
) -> None:
    movie_extension = movie_path.suffix
    phrases_extension = phrases_path.suffix

    if phrases_extension not in PHRASES_FILE_PARSERS_MAPPING:
        raise ValueError(f"Unsupported phrases file extension: {phrases_extension}")

    phrases_parser = PHRASES_FILE_PARSERS_MAPPING[phrases_extension]
    phrases = phrases_parser(phrases_path)[:limit]

    for phrase in phrases:
        volume_arg = f'-filter:a "volume={volume}"'
        start_arg = f"-ss {phrase.start}"
        end_arg = f"-to {phrase.end}"
        output_path_arg = output_dir.joinpath(f"{phrase.output_name}{movie_extension}")

        cmd = f"ffmpeg {start_arg} {end_arg} -i {movie_path} {volume_arg} {output_path_arg} -y"
        subprocess.run(cmd, shell=True, check=True)  # noqa: S602

    if create_subtitles:
        handle_create_subtitles(phrases, output_dir)


if __name__ == "__main__":
    create_scenes()
