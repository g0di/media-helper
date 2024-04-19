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
