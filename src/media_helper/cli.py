from enum import Enum
from pathlib import Path
from typing import Annotated, Optional

import rich
import rich.logging
import rich.prompt
import rich.table
import rich.text
import rich.tree
import typer

from .bootstrap import get_movie_service
from .ports import ManyMoviesFoundError, MovieNotFoundError
from .services.movie import MovieService

console = rich.console.Console()
prompt = rich.prompt.Prompt(console=console)
confirm = rich.prompt.Confirm(console=console)
app = typer.Typer()
movies_app = typer.Typer(help="Movies related commands")

app.add_typer(movies_app, name="movie")


class Strategy(str, Enum):
    COPY = "copy"
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

    table = rich.table.Table(title="Media Information")
    table.add_column("", justify="right", no_wrap=True)
    table.add_column("Value")

    for info, value in media_info.items():
        pretty_value = (
            ", ".join(str(i) for i in value) if isinstance(value, list) else str(value)
        )
        table.add_row(info, pretty_value)

    rich.print(table)


@movies_app.command()
def suggest(
    filename: Annotated[str, typer.Argument(help="File name to clean")],
) -> None:
    """Suggest a clean name for the movie file having given name."""
    clean_name, movie_link = _suggest(filename, srv=get_movie_service())
    rich.print(
        rich.text.Text(clean_name, style="bold"),
        f"[link={movie_link}](See movie)[/link]",
    )


@movies_app.command()
def rename(
    filepaths: Annotated[
        list[Path],
        typer.Argument(
            exists=False,
            file_okay=True,
            resolve_path=True,
            help="Path(s) to the movie(s) file(s) to rename",
        ),
    ],
    strategy: Annotated[
        Strategy,
        typer.Option(
            "-s", "--strategy", help="Define how the file will actually be renamed"
        ),
    ] = Strategy.COPY,
    output_dir: Annotated[
        Optional[Path],
        typer.Option(
            "-o",
            "--output-dir",
            dir_okay=True,
            help="Directory where the renamed file will be put. "
            "If 'own_folder' is also passed, the renamed file will be in its own directory within the given directory",
        ),
    ] = None,
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
    srv = get_movie_service()
    for index, filepath in enumerate(filepaths):
        pos = rich.text.Text(f"[{index}/{len(filepaths)}] ", style="yellow")
        if not confirm.ask(
            rich.text.Text.assemble(pos, (str(filepath.name))), default=True
        ):
            continue
        clean_name, _ = _suggest(filepath.name, srv=srv)
        clean_name = prompt.ask("Confirm name", default=clean_name)
        output_path = Path(output_dir or filepath.parent) / clean_name
        tree = rich.tree.Tree(str(output_path.parent.parent))
        tree.add(str(output_path.parent.name)).add(str(output_path.name))
        console.print(tree)
        # TODO: actually implements the copy/hardlink/rename
        # TODO: display link to movie suggested as well
        # TODO: Always show found movies even if only one to allow to pick a different movie ID
        # Use the first movie in the list as default value
        # TODO: allow to customize the final name?


def _suggest(filename: str, *, srv: MovieService) -> tuple[str, str]:
    try:
        return srv.suggest_filename(filename)
    except MovieNotFoundError as not_found:
        console.print(not_found, style="bold red")
        movie_id = prompt.ask("Enter movie ID")
        return srv.suggest_filename(filename, movie_id=movie_id)
    except ManyMoviesFoundError as many_found:
        table = rich.table.Table(title=str(many_found))
        table.add_column("ID", justify="right", no_wrap=True)
        table.add_column("Released", justify="right", style="cyan", no_wrap=True)
        table.add_column("Title", style="magenta")
        table.add_column("Original Title", justify="right", style="green")

        for movie in many_found.movies:
            table.add_row(
                rich.text.Text(movie.id, style=f"link {movie.link}"),
                str(movie.release_year),
                movie.title,
                movie.original_title,
            )

        console.print(table)
        movie_id = prompt.ask("Enter movie ID")
        return srv.suggest_filename(filename, movie_id=movie_id)


if __name__ == "__main__":
    app()
