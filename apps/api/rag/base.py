from typing import Protocol


class RagProvider(Protocol):
    backend: str

    def health_check(self) -> dict:
        ...
