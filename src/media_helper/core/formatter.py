import os
import re

from media_helper.core.model import MediaInformation, Movie


class PlexMediaFileNameFormatter:
    def format_movie_filepath(self, media_info: MediaInformation, movie: Movie) -> str:
        return os.path.join(
            self.format_movie_dirname(media_info, movie),
            self.format_movie_filename(media_info, movie),
        )

    def format_movie_filename(self, media_info: MediaInformation, movie: Movie) -> str:
        parts = [
            self._format_movie_title(movie.title),
            f"({movie.release_year})",
            self._format_movie_source(movie),
        ]
        if media_info.edition_tags:
            parts.append(self._format_movie_edition(media_info.edition_tags))
        if media_info.split_name:
            parts.append(f"- {media_info.split_name}")

        metadata = []
        if media_info.quality_full:
            metadata.append(f"[{media_info.quality_full}]")
        if media_info.is_3d:
            metadata.append("[3D]")
        if media_info.hdr:
            metadata.append("[HDR]")
        if media_info.audio:
            metadata.append(f"[{' '.join(media_info.audio)}]")
        if media_info.language:
            metadata.append(f"[{' '.join(media_info.language)}]")
        if media_info.subtitles:
            metadata.append(f"[{' '.join(media_info.subtitles)}]")
        if media_info.codec:
            metadata.append(f"[{' '.join(media_info.codec)}]")

        if metadata:
            parts.append("".join(metadata))

        return " ".join(parts)

    def format_movie_dirname(self, media_info: MediaInformation, movie: Movie) -> str:
        parts = [
            self._format_movie_title(movie.title),
            f"({movie.release_year})",
            self._format_movie_source(movie),
        ]
        if media_info.edition_tags:
            parts.append(self._format_movie_edition(media_info.edition_tags))

        return " ".join(parts)

    def _format_movie_source(self, movie: Movie) -> str:
        return f"{{{movie.source}-{movie.id}}}"

    def _format_movie_edition(self, edition_tags: list[str]) -> str:
        return f"{{edition-{' '.join(edition_tags)}}}" if edition_tags else ""

    def _format_movie_title(self, title: str) -> str:
        return re.sub(r" ?: ", " - ", title)
