from functools import lru_cache

from .adapters.tmdb import TmdbMovieDatabase
from .config import Settings
from .ports import MovieDatabase
from .services.movie import MovieService


@lru_cache
def get_settings() -> Settings:
    return Settings()


@lru_cache
def get_movie_db() -> MovieDatabase:
    return TmdbMovieDatabase(
        access_token=get_settings().tmdb_access_token.get_secret_value()
    )


def get_movie_service() -> MovieService:
    return MovieService(get_movie_db())
