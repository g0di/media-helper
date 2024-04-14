from __future__ import annotations

import re
from functools import cached_property, lru_cache
from pathlib import Path
from typing import ClassVar

import PTN
from pydantic import BaseModel, ConfigDict, Field


class Movie(BaseModel):
    id: str
    title: str
    original_title: str
    release_year: int
    source: str
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


class MediaInformation(BaseModel):
    model_config = ConfigDict(frozen=True)

    _EDITION_PATTERN: ClassVar[re.Pattern[str]] = re.compile(
        r"{edition-(.+?)( Edition)?}"
    )
    _PART_PATTERN: ClassVar[re.Pattern[str]] = re.compile(
        r"(cd|disk|disc|dvd|part|pt)([0-9])"
    )
    _SOURCE_PATTERN: ClassVar[re.Pattern[str]] = re.compile(r"{(imdb|tmdb)-(.+?)}")

    # Info that will always be uniques (never lists)
    episode_name: str | None = Field(None, alias="episodeName")
    title: str | None = None

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
    split_name: str | None = None
    source: tuple[str, str] | None = None
    suffix: str
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
    @lru_cache
    def from_name(cls, name: str) -> "MediaInformation":
        """

        Ensure media information properly parse strings
        >>> MediaInformation.from_str("Deadliest.Catch.S00E66.No.Safe.Passage.720p.AMZN.WEB-DL.DDP2.0.H.264-NTb[TGx]")
        MediaInformation(...)
        >>> MediaInformation.from_str("Insecure.S04.COMPLETE.720p.AMZN.WEBRip.x264-GalaxyTV")
        MediaInformation(...)
        >>> MediaInformation.from_str("Vacancy (2007) 720p Bluray Dual Audio [Hindi + English] ⭐800 MB⭐ DD - 2.0 MSub x264 - Shadow (BonsaiHD)")
        MediaInformation(...)
        """
        # Extract edition tags if any (we'll let PTN determine the right edition)
        edition_match = cls._EDITION_PATTERN.search(name)
        if edition_match:
            name = name.replace(edition_match.group(), "")
        # Extract the split name, if any
        split_match = cls._PART_PATTERN.search(name)
        if split_match:
            name = name.replace(split_match.group(), "")
        # Extract the movie info source, if any
        source_match = cls._SOURCE_PATTERN.search(name)
        if source_match:
            name = name.replace(source_match.group(), "")

        content = PTN.parse(name, standardise=True, coherent_types=True)
        content.update(
            split_name=split_match.group() if split_match else None,
            source=source_match.group(1, 2) if source_match else None,
            suffix=Path(name).suffix,
        )
        return cls.model_validate(content)

    @classmethod
    def from_filename(cls, filepath: Path) -> MediaInformation:
        return cls.from_name(filepath.stem)

    @cached_property
    def quality_full(self) -> str:
        items = self.quality + self.resolution
        if self.proper:
            items.append("Proper")
        if self.upscaled:
            items.append("Upscaled")
        if self.widescreen:
            items.append("Widescreen")
        return " ".join(items)

    @cached_property
    def edition_tags(self) -> list[str]:
        tags = []
        if self.directors_cut:
            tags.append("Director's Cut")
        if self.international_cut:
            tags.append("International's Cut")
        if self.unrated:
            tags.append("Unrated")
        if self.remastered:
            tags.append("Remastered")
        if self.limited:
            tags.append("Limited Edition")
        if self.extended:
            tags.append("Extended Edition")
        return tags
