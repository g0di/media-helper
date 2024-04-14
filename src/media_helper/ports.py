from pathlib import Path
from typing import ClassVar, Protocol

from media_helper.core.model import Movie


class MovieNotFoundError(Exception):
    pass


class ManyMoviesFoundError(Exception):
    def __init__(self, msg: str, movies: list[Movie]) -> None:
        super().__init__(msg)
        self.movies = movies


class MovieDatabase(Protocol):
    SOURCE: ClassVar[str]

    def search(self, query: str, release_year: int | None = None) -> list[Movie]: ...
    def get(self, id: str) -> Movie | None: ...


class UserInterface(Protocol):
    def confirm(self, msg: str, default: bool = ...) -> bool: ...

    def print(self, msg: str) -> None: ...

    def choose_movie_among(self, items: list[Movie]) -> Movie | None: ...

    def confirm_movie_rename(self, new_name: str) -> bool: ...

    def confirm_media_handling(
        self, media_filepath: Path, index: int, total_medias: int
    ) -> bool: ...

    def prompt(self, msg: str) -> str: ...

    def warn(self, msg: str) -> None: ...
