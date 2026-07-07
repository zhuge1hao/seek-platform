import hashlib
from pathlib import Path

from storage.keys import validate_object_key


class LocalArtifactStorage:
    backend = "local"

    def put_file(self, path: Path, object_key: str, content_type: str | None = None) -> dict:
        validate_object_key(object_key)
        return {"storage_backend": self.backend, "object_key": str(path), "checksum": sha256(path), "content_type": content_type}

    def open_file(self, object_key: str):
        return Path(object_key).open("rb")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
