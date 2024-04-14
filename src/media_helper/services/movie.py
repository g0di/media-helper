from typing import Any, NamedTuple

from media_helper.core.model import (
    MediaInformation,
)
from media_helper.ports import (
    ManyMoviesFoundError,
    MovieDatabase,
    MovieNotFoundError,
)

from ..core.formatter import PlexMediaFileNameFormatter


class MovieSuggestedFilename(NamedTuple):
    filename: str
    movie_link: str


class MovieService:
    def __init__(self, moviedb: MovieDatabase) -> None:
        self.moviedb = moviedb

    def parse_filename(self, filename: str) -> dict[str, Any]:
        media_info = MediaInformation.from_name(filename)
        return media_info.model_dump(exclude_defaults=True)

    def suggest_filename(
        self, filename: str, movie_id: str | None = None
    ) -> MovieSuggestedFilename:
        media_info = MediaInformation.from_name(filename)
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

        formatter = PlexMediaFileNameFormatter()
        return MovieSuggestedFilename(
            formatter.format_movie_filepath(media_info, movie), movie.link
        )
