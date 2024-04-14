from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from media_helper.core.model import (
    MediaInformation,
    Movie,
)
from media_helper.ports import MovieDatabase, UserInterface

from ..core.formatter import PlexMediaFileNameFormatter


@dataclass
class RenameMovieFileCommand:
    filepaths: list[Path]
    """Path to the movie file to rename"""
    output_dir: Path | None = None
    """Folder where the renamed movie file will be put. Defaults to given file parent directory"""
    strategy: Literal["move", "copy", "hardlink", "noop"] = "noop"
    """Define how the movie file will be renamed"""


class MovieFileRenamer:
    def __init__(self, moviedb: MovieDatabase, ui: UserInterface) -> None:
        self.moviedb = moviedb
        self.ui = ui

    def __call__(self, cmd: RenameMovieFileCommand) -> None:
        for index, filepath in enumerate(cmd.filepaths):
            if not self.ui.confirm_media_handling(filepath, index, len(cmd.filepaths)):
                continue
            renamed_path = self._rename_movie(cmd, index)
            if renamed_path:
                self.ui.print(f"{cmd.strategy} {filepath} -> {renamed_path}")

    def _rename_movie(self, cmd: RenameMovieFileCommand, index: int) -> Path | None:
        filepath = cmd.filepaths[index]
        media_info = MediaInformation.from_filename(filepath)
        if not media_info.title:
            raise ValueError(f"Could not find movie title from file {filepath}")
        movies = self.moviedb.search(
            media_info.title, media_info.year[0] if media_info.year else None
        )
        chosen_movie = self.ui.choose_movie_among(movies)

        while chosen_movie is None:
            chosen_movie = self._ask_movie_id()

        formatter = PlexMediaFileNameFormatter()
        clean_filename = formatter.format_movie_filename(media_info, chosen_movie)
        if not self.ui.confirm_movie_rename(str(clean_filename)):
            return None

        output_dir = cmd.output_dir or filepath.parent
        output_dir = output_dir / formatter.format_movie_dirname(
            media_info, chosen_movie
        )
        target_filepath = output_dir.joinpath(str(clean_filename)).with_suffix(
            filepath.suffix
        )

        if cmd.strategy != "noop":
            output_dir.mkdir(parents=True, exist_ok=True)
        if cmd.strategy == "move":
            filepath.rename(target_filepath)
        if cmd.strategy == "copy":
            # TODO: write chunk by chunk and show a progress bar
            target_filepath.write_bytes(filepath.read_bytes())
        if cmd.strategy == "hardlink":
            filepath.hardlink_to(target_filepath)

        return target_filepath

    def _ask_movie_id(self) -> Movie | None:
        movie_id = self.ui.prompt("Enter TMDB Movie ID")
        movie = self.moviedb.get(movie_id)
        if not movie:
            self.ui.warn(f"There is no movie with id {movie_id}!")
        return movie
