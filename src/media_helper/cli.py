from enum import Enum
from pathlib import Path
from typing import Annotated, Union

import typer

from .bootstrap import get_movie_service, get_ui
from .ports import ManyMoviesFoundError, MovieNotFoundError

movie_srv = get_movie_service()
ui = get_ui()
app = typer.Typer()
movies_app = typer.Typer(help="Movies related commands")

app.add_typer(movies_app, name="movie")


class RenameStrategy(str, Enum):
    HARDLINK = "hardlink"
    MOVE = "move"
    NOOP = "noop"


@movies_app.command()
def parse(
    filename: Annotated[str, typer.Argument(help="File name to parse")],
) -> None:
    """Extract and display media information from given file name."""
    srv = get_movie_service()
    media_info = srv.parse_filename(filename)
    ui.print_media_information(media_info)


@movies_app.command()
def format(
    filepath: Annotated[Path, typer.Argument(help="File name to format")],
) -> None:
    """Suggest a clean name for the movie file having given name."""
    filename = filepath.name
    try:
        fmedia_info = movie_srv.format_filename(filename)
    except MovieNotFoundError as not_found:
        ui.error(not_found)
        movie_id = ui.ask_movie_id()
        fmedia_info = movie_srv.format_filename(filename, movie_id=movie_id)
        ui.print_formatted_media_info(fmedia_info)
    except ManyMoviesFoundError as many_found:
        ui.print_movies(many_found, many_found.movies)
        movie_id = ui.ask_movie_id(default=many_found.movies[0].id)
        fmedia_info = movie_srv.format_filename(filename, movie_id=movie_id)
        ui.print_formatted_media_info(fmedia_info)
    else:
        ui.print_formatted_media_info(fmedia_info)


@movies_app.command()
def rename(
    filepaths: Annotated[
        list[Path],
        typer.Argument(
            exists=False,
            file_okay=True,
            dir_okay=False,
            resolve_path=True,
            help="Path(s) to the movie(s) file(s) to rename",
        ),
    ],
    strategy: Annotated[
        RenameStrategy,
        typer.Option(
            "-s", "--strategy", help="Define how the file will actually be renamed"
        ),
    ] = RenameStrategy.MOVE,
    output_dir: Annotated[
        Union[Path | None],
        typer.Option(
            "-o",
            "--output-dir",
            dir_okay=True,
            help="Directory where the renamed file will be put. Defaults to its parent folder",
        ),
    ] = None,
    # TODO: add flag to force parsing files already tagged with a source (imdb/tmdb)
    # TODO: add a flag to trust and use the source in file names for searching movie info
    # TODO: add a tag for answering YES to all confirmations automatically
) -> None:
    """Rename a movie file in a standard way.

    Based on the current file name, the program will reach TMDB for finding the movie
    it corresponds to. If results not match your expectation you can provide the movie
    ID by yourself. Then, the file will be renamed following the recommended Plex pattern
    looking like the following.

    Simple case:

    ``Movie Title (2024) {tmdb-42423}.mkv``

    Specific edition:

    ``Movie Title (2024) {tmdb-42423} {edition-Extended Edition}.mkv``

    When a movie is split on several files (disks, dvds, ...):

    ``Movie Title (2024) {tmdb-42423} - part1.mkv``

    All together:

    ``Movie Title (2024) {tmdb-42423} {edition-Extended Edition} - part1 [extras infos].mkv``

    To ensure ouput will feet your needs, start off using the ``--strategy noop`` flag
    for a dry run.
    """
    # TODO: update docstrings
    for filepath in ui.iterpaths(
        filepaths,
        skipif=lambda p: "Already source"
        if "source" in movie_srv.parse_filename(p.stem)
        else "",
    ):
        # TODO: extract this try except block into the UI service directly
        filename = filepath.name
        try:
            fmedia_info = movie_srv.format_filename(filename)
        except MovieNotFoundError as not_found:
            ui.error(not_found)
            movie_id = ui.ask_movie_id()
            fmedia_info = movie_srv.format_filename(filename, movie_id=movie_id)
        except ManyMoviesFoundError as many_found:
            ui.print_movies(many_found, many_found.movies)
            movie_id = ui.ask_movie_id(default=many_found.movies[0].id)
            fmedia_info = movie_srv.format_filename(filename, movie_id=movie_id)

        output_dir = output_dir or filepath.parent
        output_path = output_dir / fmedia_info.dirname / fmedia_info.filename
        # TODO: short-circuit if the formatted name is identical as current filepath
        # TODO: simplify this confirm function
        if not ui.confirm_rename_media(
            output_dir,
            filepath,
            fmedia_info,
            strategy,
            skip=strategy == RenameStrategy.NOOP,
        ):
            continue

        # TODO: not sure if this code should not be in the movie service directly
        match strategy:
            case RenameStrategy.HARDLINK:
                output_path.parent.mkdir(parents=True, exist_ok=True)
                filepath.hardlink_to(output_path)
            case RenameStrategy.MOVE:
                output_path.parent.mkdir(parents=True, exist_ok=True)
                filepath.rename(output_path)
            case RenameStrategy.NOOP:
                pass


if __name__ == "__main__":
    app()
