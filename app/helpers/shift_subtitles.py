import datetime
import pathlib

import click
import srt


@click.command()
@click.option(
    "--subtitles-path",
    "-sp",
    required=True,
    type=click.Path(exists=True, dir_okay=False, path_type=pathlib.Path),
)
@click.option(
    "--start",
    "-s",
    required=True,
    type=float,
    default=0,
)
@click.option(
    "--end",
    "-e",
    required=True,
    type=float,
    default=0,
)
def shift_subtitles(subtitles_path: pathlib.Path, start: float, end: float) -> None:
    with open(subtitles_path) as f:
        subtitles = list(srt.parse(f.read()))

    for subtitle in subtitles:
        start_delta = datetime.timedelta(seconds=abs(start))
        if start > 0:
            subtitle.start += start_delta
        elif start < 0:
            subtitle.start -= start_delta

        end_delta = datetime.timedelta(seconds=abs(end))
        if end > 0:
            subtitle.end += end_delta
        elif end < 0:
            subtitle.end -= end_delta

    with open(subtitles_path, "w") as f:
        f.write(srt.compose(subtitles))


if __name__ == "__main__":
    shift_subtitles()
