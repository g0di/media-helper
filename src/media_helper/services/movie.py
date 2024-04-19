from typing import Any, NamedTuple

from ..core.formatter import PlexMediaFileNameFormatter
from ..core.model import (
    MediaInformation,
)
from ..ports import (
    ManyMoviesFoundError,
    MovieDatabase,
    MovieNotFoundError,
)


class FormattedMediaInformation(NamedTuple):
    filename: str
    dirname: str
    link: str


class MovieService:
    def __init__(self, moviedb: MovieDatabase) -> None:
        self.moviedb = moviedb
        self.formatter = PlexMediaFileNameFormatter()

    def parse_filename(self, filename: str) -> dict[str, Any]:
        media_info = MediaInformation.from_filename(filename)
        return media_info.model_dump(exclude_defaults=True)

    def format_filename(
        self, filename: str, movie_id: str | None = None
    ) -> FormattedMediaInformation:
        """Format given filename as a movie media using plex naming conventions."""
        media_info = MediaInformation.from_filename(filename)
        if not media_info.title:
            raise MovieNotFoundError(
                "Could not determine movie title from given filename"
            )

        if movie_id:
            movie = self.moviedb.get(movie_id)
            if not movie:
                raise MovieNotFoundError(
                    f"There is no movie having id {movie_id} in the database"
                )
        else:
            movies = self.moviedb.search(
                media_info.title,
                release_year=media_info.year[0] if media_info.year else None,
            )
            if not movies:
                raise MovieNotFoundError(
                    f"Could not find any movie matching {media_info.title!r} in the movie database"
                )
            if len(movies) > 1:
                raise ManyMoviesFoundError(
                    f"Found many movies matching {media_info.title!r}", movies
                )
            movie = movies[0]

        media_info.update_from_movie(movie)
        return FormattedMediaInformation(
            self.formatter.format_movie_filename(media_info),
            self.formatter.format_movie_dirname(media_info),
            movie.link,
        )
