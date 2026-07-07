from pathlib import Path
from typing import Protocol


class ArtifactStorage(Protocol):
    backend: str

    def put_file(self, path: Path, object_key: str, content_type: str | None = None) -> dict:
        ...

    def open_file(self, object_key: str):
        ...
