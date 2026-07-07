import os

from storage.local import LocalArtifactStorage
from storage.s3 import S3ArtifactStorage


def provider():
    backend = os.getenv("ARTIFACT_STORAGE_BACKEND", "local").lower()
    if backend == "s3":
        return S3ArtifactStorage()
    storage = LocalArtifactStorage()
    storage.backend = backend if backend in {"local", "local_shared"} else "local"
    return storage
