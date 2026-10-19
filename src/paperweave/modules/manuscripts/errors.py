"""Manuscript domain errors."""


class ManuscriptConflictError(Exception):
    def __init__(self, current_version: int | None) -> None:
        self.current_version = current_version
        super().__init__(f"Manuscript version conflict; current version is {current_version}.")


class ManuscriptAlreadyExistsError(Exception):
    """A project already has its single MVP manuscript."""
