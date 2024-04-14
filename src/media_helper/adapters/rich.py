from pathlib import Path

import rich
import rich.columns
import rich.prompt
from rich.table import Table
from rich.text import Text

from media_helper.core.model import Movie
from media_helper.ports import (
    UserInterface,
)


class RichUserInterface(UserInterface):
    def __init__(self) -> None:
        self._console = rich.console.Console()
        self._prompt = rich.prompt.Prompt(console=self._console)
        self._confirm = rich.prompt.Confirm(console=self._console)

    def confirm(self, msg: str, default: bool = False) -> bool:
        return self._confirm.ask(msg, default=default)

    def print(self, msg: str) -> None:
        self._console.print(msg)

    def prompt(self, msg: str) -> str:
        return self._prompt.ask(msg)

    def confirm_movie_rename(self, new_name: str) -> bool:
        return self._confirm.ask(
            Text.assemble("Rename to ", Text(new_name, style="green")), default=True
        )

    def warn(self, msg: str) -> None:
        self._console.print(msg, style="red bold")

    def confirm_media_handling(
        self, media_filepath: Path, index: int, total_medias: int
    ) -> bool:
        confirm_msg = Text(f"[{index + 1}/{total_medias}] ").append(
            str(media_filepath), style="green"
        )

        return self._confirm.ask(confirm_msg, default=True)

    def choose_movie_among(self, items: list[Movie]) -> Movie | None:
        if not items:
            self.warn("No candidates found!")
            return None
        table = Table(title="Found candidates")
        table.add_column("#", justify="right", no_wrap=True)
        table.add_column("Released", justify="right", style="cyan", no_wrap=True)
        table.add_column("Title", style="magenta")
        table.add_column("Original Title", justify="right", style="green")

        for index, movie in enumerate(items):
            table.add_row(
                str(index + 1),
                str(movie.release_year),
                Text(movie.title, style=f"link {movie.link}"),
                movie.original_title,
            )

        self._console.print(table)

        choice = int(
            self._prompt.ask(
                "Your choice ([italic]0 to manually enter movie ID[/italic])",
                default=1 if items else 0,
                show_choices=True,
                choices=[str(i) for i in range(len(items) + 1)],
            )
        )
        if choice == 0:
            return None
        return items[choice - 1]
