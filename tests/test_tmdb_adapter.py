from collections.abc import Iterator

import pytest
from media_helper.adapters.tmdb import TmdbMovieDatabase
from media_helper.config import Settings
from media_helper.core.model import Movie


@pytest.fixture
def sut(settings: Settings) -> Iterator[TmdbMovieDatabase]:
    client = TmdbMovieDatabase(
        access_token=settings.tmdb_access_token.get_secret_value()
    )
    yield client
    client.close()


def test_get_movie_by_id_returns_movie_with_correct_info(
    sut: TmdbMovieDatabase,
) -> None:
    movie = sut.get("174316")

    # TODO: fix this test later on
    assert movie == Movie(  # type: ignore
        id="174316",
        title="Tout pour lui plaire",
        original_title="A Case of You",
        release_year=2013,
        source_name="tmdb",
        link="https://www.themoviedb.org/movie/174316-a-case-of-you",
    )


def test_search_movie(sut: TmdbMovieDatabase) -> None:
    movies = sut.search("Black Swan", release_year=2010)

    # NOTE: not so much we can test here...
    assert movies
