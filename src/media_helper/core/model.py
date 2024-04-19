from __future__ import annotations

import re
from pathlib import Path
from typing import Callable, ClassVar

import PTN
from pydantic import BaseModel, Field


class Movie(BaseModel):
    id: str
    title: str
    original_title: str
    release_year: int
    source_name: str
    link: str
    popularity: float
    vote_average: float
    vote_count: int

    def __str__(self) -> str:
        parts = [f"{self.title} ({self.release_year})"]
        if self.original_title != self.title:
            parts.append(self.original_title)
        parts.append(self.link)
        return " - ".join(parts)


Transformer = Callable[[re.Match[str], "MediaInformation"], None]


class MediaInformation(BaseModel):
    transformers: ClassVar[list[tuple[re.Pattern[str], Transformer]]] = []

    # Info that will always be uniques (never lists)
    episode_name: str | None = Field(None, alias="episodeName")
    title: str | None = None

    # Custom info added compared to PTN
    split_name: str | None = None
    source: MediaSource | None = None
    file_ext: str

    # Info that will always be lists
    # see: https://github.com/platelminto/parse-torrent-title?tab=readme-ov-file#types-of-parts
    day: list[int] = Field(default_factory=list)
    month: list[int] = Field(default_factory=list)
    year: list[int] = Field(default_factory=list)
    audio: list[str] = Field(default_factory=list)
    bit_depth: list[int] = Field(default_factory=list, alias="bitDepth")
    codec: list[str] = Field(default_factory=list)
    encoder: list[str] = Field(default_factory=list)
    episode: list[int] = Field(default_factory=list)
    excess: list[str] = Field(default_factory=list)
    filetype: list[str] = Field(default_factory=list)
    fps: list[int] = Field(default_factory=list)
    genre: list[str] = Field(default_factory=list)
    language: list[str] = Field(default_factory=list)
    network: list[str] = Field(default_factory=list)
    quality: list[str] = Field(default_factory=list)
    region: list[str] = Field(default_factory=list)
    resolution: list[str] = Field(default_factory=list)
    sbs: list[str] = Field(default_factory=list)
    season: list[int] = Field(default_factory=list)
    site: list[str] = Field(default_factory=list)
    size: list[str] = Field(default_factory=list)
    subtitles: list[str] = Field(default_factory=list)

    # Flags
    hdr: bool = False
    internal: bool = False
    directors_cut: bool = Field(False, alias="directorsCut")
    international_cut: bool = Field(False, alias="internationalCut")
    readnfo: bool = False
    extended: bool = False
    documentary: bool = False
    hardcoded: bool = False
    limited: bool = False
    proper: bool = False
    remastered: bool = False
    remux: bool = False
    repack: bool = False
    untouched: bool = False
    upscaled: bool = False
    widescreen: bool = False
    unrated: bool = False
    is_3d: bool = Field(False, alias="3d")

    @classmethod
    def search(cls, pattern: str) -> Callable[[Transformer], None]:
        def wrapper(fn: Transformer) -> None:
            cls.transformers.append((re.compile(pattern), fn))

        return wrapper

    @classmethod
    def from_filename(cls, name: str) -> "MediaInformation":
        """Extract media information from given filename.

        Ensure media information properly parse strings
        >>> MediaInformation.from_str("Deadliest.Catch.S00E66.No.Safe.Passage.720p.AMZN.WEB-DL.DDP2.0.H.264-NTb[TGx]")
        MediaInformation(...)
        >>> MediaInformation.from_str("Insecure.S04.COMPLETE.720p.AMZN.WEBRip.x264-GalaxyTV")
        MediaInformation(...)
        >>> MediaInformation.from_str("Vacancy (2007) 720p Bluray Dual Audio [Hindi + English] ⭐800 MB⭐ DD - 2.0 MSub x264 - Shadow (BonsaiHD)")
        MediaInformation(...)
        """
        matched_transformers: list[tuple[re.Match[str], Transformer]] = []
        for pattern, transformer in cls.transformers:
            match = pattern.search(name)
            if not match:
                continue
            # Removed matched content to avoid duplicate matches
            name = name.replace(match.group(), "")
            matched_transformers.append((match, transformer))

        content = PTN.parse(name, standardise=True, coherent_types=True)
        content.update(file_ext=Path(name).suffix)
        info = cls.model_validate(content)

        for match, transformer in matched_transformers:
            transformer(match, info)

        return info

    def update_from_movie(self, movie: Movie) -> None:
        self.title = movie.title
        self.year = [movie.release_year]
        self.source = MediaSource(name=movie.source_name, media_id=movie.id)


class MediaSource(BaseModel):
    name: str
    media_id: str


@MediaInformation.search(r"(cd|disk|disc|dvd|part|pt)([0-9])")
def _handle_split_name(match: re.Match[str], media_info: MediaInformation) -> None:
    media_info.split_name = match.group()


@MediaInformation.search(r"{(imdb|tmdb)-(.+?)}")
def _handle_db_source(match: re.Match[str], media_info: MediaInformation) -> None:
    media_info.source = MediaSource(name=match.group(1), media_id=match.group(2))


@MediaInformation.search(r"(Multi|MULTI|MULTi)")
def _handle_multi_language(match: re.Match[str], media_info: MediaInformation) -> None:
    media_info.language.append("Multi")


@MediaInformation.search(r"HDLight")
def _handle_additional_quality(
    match: re.Match[str], media_info: MediaInformation
) -> None:
    media_info.quality.append("HDLight")


@MediaInformation.search(r"VOSTFR")
def _handle_vostfr(match: re.Match[str], media_info: MediaInformation) -> None:
    media_info.subtitles.append("VOSTFR")


@MediaInformation.search(r"(VFF|VFI|VF2)")
def _handle_vff_vfi(match: re.Match[str], media_info: MediaInformation) -> None:
    media_info.language.append("French")
