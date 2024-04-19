from media_helper.core.model import MediaInformation


class PlexMediaFileNameFormatter:
    def format_movie_filename(self, media: MediaInformation) -> str:
        parts = [
            self._format_movie_title(media),
            self._format_movie_release_year(media),
            self._format_media_source(media),
            self._format_movie_edition(media),
            self._format_movie_split_name(media.split_name),
            self._format_media_metadata(media),
        ]
        return " ".join(p for p in parts if p) + media.file_ext

    def format_movie_dirname(self, media: MediaInformation) -> str:
        parts = [
            self._format_movie_title(media),
            self._format_movie_release_year(media),
            self._format_media_source(media),
            self._format_movie_edition(media),
        ]
        return " ".join(p for p in parts if p)

    def _format_movie_title(self, media: MediaInformation) -> str:
        if not media.title:
            raise ValueError("Media has no title")
        title_parts = media.title.replace(":", " - ").split()
        return " ".join(title_parts)

    def _format_movie_release_year(self, media: MediaInformation) -> str:
        if not media.year:
            raise ValueError("Media has no release year")
        return f"({media.year[0]})"

    def _format_media_source(self, media: MediaInformation) -> str:
        if not media.source:
            return ""
        return f"{{{media.source.name}-{media.source.media_id}}}"

    def _format_movie_edition(self, media: MediaInformation) -> str:
        tags = []
        if media.directors_cut:
            tags.append("Director's Cut")
        if media.international_cut:
            tags.append("International's Cut")
        if media.unrated:
            tags.append("Unrated")
        if media.remastered:
            tags.append("Remastered")
        if media.limited:
            tags.append("Limited Edition")
        if media.extended:
            tags.append("Extended Edition")

        tags_str = " ".join(tags)
        return f"{{edition-{tags_str}}}" if tags else ""

    def _format_movie_split_name(self, split_name: str | None) -> str:
        return f"- {split_name}" if split_name else ""

    def _format_media_metadata(self, media: MediaInformation) -> str:
        metadata = [
            self._format_media_quality(media),
            "3D" if media.is_3d else None,
            "HDR" if media.hdr else None,
            " ".join(media.audio),
            " ".join(media.language),
            " ".join(media.subtitles),
            " ".join(media.codec),
        ]
        return "".join(f"[{m}]" for m in metadata if m)

    def _format_media_quality(self, media: MediaInformation) -> str:
        items = media.quality + media.resolution
        if media.proper:
            items.append("Proper")
        if media.upscaled:
            items.append("Upscaled")
        if media.widescreen:
            items.append("Widescreen")
        return " ".join(items)
