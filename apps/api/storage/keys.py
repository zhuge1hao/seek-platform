from pathlib import PurePosixPath


def validate_object_key(object_key: str) -> str:
    key = object_key.strip()
    parts = PurePosixPath(key).parts
    if not key or key.startswith("/") or "\\" in key or any(part in {"", ".", ".."} for part in parts):
        raise ValueError("invalid artifact object key")
    return key
