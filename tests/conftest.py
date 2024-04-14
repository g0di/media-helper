import pytest
from media_helper.config import Settings


@pytest.fixture(scope="session")
def settings() -> Settings:
    return Settings()
