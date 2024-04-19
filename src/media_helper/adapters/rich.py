from pathlib import Path
from typing import Any, Callable, Iterator

from rich.console import Console
from rich.prompt import Confirm, Prompt
from rich.table import Table
from rich.text import Text
from rich.tree import Tree

from ..core.model import Movie
from ..services.movie import FormattedMediaInformation, MovieService


class RichUserInterface:
    def __init__(self, movie_srv: MovieService) -> None:
        self.movie_srv = movie_srv
        self.console = Console()
        self.confirm = Confirm(console=self.console)

    def iterpaths(
        self, filepaths: list[Path], skipif: Callable[[Path], str] | None = None
    ) -> Iterator[Path]:
        for index, filepath in enumerate(filepaths):
            msg = Text(f"[{index + 1}/{len(filepaths)}] ", style="yellow").append(
                Text(filepath.name)
            )
            skip_reason = skipif(filepath) if skipif else False
            if skip_reason:
                self.console.print(msg, f"- {skip_reason}")
            elif self.confirm.ask(msg, default=True):
                yield filepath

    def print_media_information(self, media_info: dict[str, Any]) -> None:
        table = Table(title="Media Information")
        table.add_column("", justify="right", no_wrap=True)
        table.add_column("Value")

        for info, value in media_info.items():
            table.add_row(info, self.format(value))

        self.console.print(table)

    def confirm_rename_media(
        self,
        output_dir: Path,
        filepath: Path,
        fmedia_info: FormattedMediaInformation,
        strategy: str,
        *,
        skip: bool = False,
    ) -> bool:
        self.console.print(
            Text(strategy.capitalize(), style="yellow bold"),
            Text(str(filepath)),
            Text("->", style="yellow bold"),
            self._get_formatted_media_info_tree(fmedia_info, output_dir=output_dir),
        )
        return skip or self.confirm.ask("Proceed?", default=True)

    def print_formatted_media_info(
        self, fmedia_info: FormattedMediaInformation, output_dir: Path | None = None
    ) -> None:
        tree = self._get_formatted_media_info_tree(fmedia_info, output_dir)
        self.console.print(tree)

    def _get_formatted_media_info_tree(
        self, fmedia_info: FormattedMediaInformation, output_dir: Path | None = None
    ) -> Tree:
        if output_dir:
            tree = Tree(str(output_dir.resolve().absolute())).add(fmedia_info.dirname)
        else:
            tree = Tree(fmedia_info.dirname)

        tree.add(fmedia_info.filename, style=f"link {fmedia_info.link}")
        return tree

    def print_movies(self, msg: Any, movies: list[Movie]) -> None:
        table = Table(title=str(msg))
        table.add_column("ID", justify="right", no_wrap=True)
        table.add_column("Released", style="cyan", no_wrap=True)
        table.add_column("Title", style="magenta")
        table.add_column("Original Title", style="green")
        table.add_column("Popularity", justify="right")
        table.add_column("Vote Average", justify="right")
        table.add_column("Vote Count", justify="right")

        for movie in movies:
            table.add_row(
                Text(movie.id, style=f"link {movie.link}"),
                str(movie.release_year),
                movie.title,
                movie.original_title,
                str(movie.popularity),
                f"{int(movie.vote_average * 10)}%",
                str(movie.vote_count),
            )

        self.console.print(table)

    def ask_movie_id(self, default: str | None = None) -> str | None:
        return Prompt.ask("Enter movie ID", default=default)

    def error(self, message: Any) -> None:
        self.console.print(str(message), style="bold red")

    def warn(self, *messages: Any) -> None:
        self.console.print(*(str(m) for m in messages), style="bold yellow")

    def format(self, value: Any) -> str:
        return self.format_list(value) if isinstance(value, list) else str(value)

    def format_list(self, list_: list[Any]) -> str:
        return ", ".join(str(i) for i in list_)
