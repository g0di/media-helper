import logging
from datetime import date
from typing import Annotated, Generic, TypeVar

import httpx
from pydantic import BaseModel, BeforeValidator

from media_helper.core.model import Movie
from media_helper.ports import MovieDatabase

T = TypeVar("T")


class TmdbList(BaseModel, Generic[T]):
    page: int
    results: list[T]
    total_pages: int
    total_results: int


class TmdbMovie(BaseModel):
    adult: bool
    backdrop_path: str | None = None
    id: int
    original_language: str
    original_title: str
    overview: str
    popularity: float
    poster_path: str | None = None
    # NOTE: some movies can have an empty str has release_date
    release_date: Annotated[date | None, BeforeValidator(lambda v: v or None)] = None
    title: str
    video: bool
    vote_average: float
    vote_count: int


class TmdbMovieDatabase(MovieDatabase):
    SOURCE = "tmdb"

    def __init__(
        self,
        access_token: str,
        api_base_url: str = "https://api.themoviedb.org",
        web_base_url: str = "https://www.themoviedb.org",
        lang: str = "fr-FR",
    ) -> None:
        self.lang = lang
        self._http = httpx.Client(
            base_url=api_base_url,
            headers={
                "Authorization": "Bearer " + access_token,
                "Accept": "application/json",
            },
            params={"language": lang},
        )
        self.web_base_url = web_base_url
        self._cache_by_id: dict[str, Movie] = {}
        self._logger = logging.getLogger(__name__)

    def close(self) -> None:
        self._http.close()

    def search(self, query: str, release_year: int | None = None) -> list[Movie]:
        raw = self._http.get(
            "/3/search/movie",
            params={
                "query": query,
                "year": release_year,
                "page": 1,
            },
        )
        raw.raise_for_status()
        resp = TmdbList[TmdbMovie].model_validate_json(raw.content)
        movies = [self._parse_movie(movie) for movie in resp.results]
        return [m for m in movies if m is not None]

    def get(self, movie_id: str) -> Movie | None:
        if movie_id in self._cache_by_id:
            return self._cache_by_id[movie_id]

        raw = self._http.get(f"/3/movie/{movie_id}")
        if raw.status_code == 404:
            return None
        raw.raise_for_status()
        movie = TmdbMovie.model_validate(raw.json())
        return self._parse_movie(movie)

    def _parse_movie(self, tmdb_movie: TmdbMovie) -> Movie | None:
        if not tmdb_movie.release_date:
            self._logger.warn(
                "Skipped movie %s because it has no release date", tmdb_movie.id
            )
            return None
        movie = Movie(
            id=str(tmdb_movie.id),
            title=tmdb_movie.title,
            original_title=tmdb_movie.original_title,
            release_year=tmdb_movie.release_date.year
            if tmdb_movie.release_date
            else None,
            source_name=self.SOURCE,
            link=f"{self.web_base_url}/movie/{tmdb_movie.id}?language={self.lang}",
            popularity=tmdb_movie.popularity,
            vote_average=tmdb_movie.vote_average,
            vote_count=tmdb_movie.vote_count,
        )
        self._cache_by_id[movie.id] = movie

        return movie
