import json
import pathlib
import subprocess
from itertools import batched

import click


@click.command()
@click.option(
    "--movie-path",
    "-mp",
    required=True,
    type=click.Path(exists=True, dir_okay=False),
)
@click.option(
    "--json-path",
    "-jp",
    required=True,
    type=click.Path(exists=True, dir_okay=False),
)
@click.option(
    "--output-dir",
    "-od",
    required=True,
    type=click.Path(exists=True, dir_okay=True, file_okay=False, path_type=pathlib.Path),
)
@click.option(
    "--volume",
    "-vol",
    default=1,
    type=float,
)
def create_scenes(movie_path: str, json_path: str, output_dir: str, volume: float) -> None:
    movie_extension = movie_path.split(".")[-1]

    with open(json_path) as f:
        phrases = json.load(f)
    base_cmd = f"ffmpeg -i {movie_path}"
    output_str_groups = []

    for phrases_group in batched(phrases, 10):
        output_group = []
        for phrase in phrases_group:
            start, end = phrase["start_in_movie"], phrase["end_in_movie"]
            volume_filter = f'-filter:a "volume={volume}"'
            outputh_path = f"{output_dir}/{phrase['id']}.{movie_extension}"

            output_group.append(f" -ss {start} -to {end} {volume_filter} {outputh_path}")

        output_group_str = "".join(output_group)
        output_str_groups.append(output_group_str)

    for output_str in output_str_groups:
        cmd = f"{base_cmd} {output_str} -y"

        subprocess.run(cmd, shell=True, check=True)  # noqa: S602


if __name__ == "__main__":
    create_scenes()
