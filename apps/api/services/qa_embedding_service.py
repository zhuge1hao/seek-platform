import os
import threading
from pathlib import Path
from typing import Any

from services.config_backup_service import resolve_runtime_path


class QAEmbeddingError(RuntimeError):
    pass


_MODEL = None
_LOCK = threading.Lock()


def _model_path() -> Path:
    return resolve_absolute_model_path()


def embedding_model_path() -> str:
    return os.getenv("BGE_SMALL_ZH_MODEL_PATH", "./models/bge-small-zh")


def get_configured_model_path() -> str:
    return embedding_model_path()


def resolve_absolute_model_path() -> Path:
    return resolve_runtime_path(get_configured_model_path())


def is_model_loaded() -> bool:
    return _MODEL is not None


def _setup_hint() -> str:
    return "请将模型放到 ./models/bge-small-zh 或修改 .env 中的 BGE_SMALL_ZH_MODEL_PATH。"


def _load_model():
    global _MODEL
    if _MODEL is not None:
        return _MODEL
    with _LOCK:
        if _MODEL is not None:
            return _MODEL
        path = _model_path()
        if not path.exists():
            raise QAEmbeddingError("模型目录不存在")
        try:
            from sentence_transformers import SentenceTransformer

            _MODEL = SentenceTransformer(str(path))
            return _MODEL
        except ImportError as exc:
            raise QAEmbeddingError("sentence-transformers 未安装，请先安装后端依赖。") from exc
        except Exception as exc:
            raise QAEmbeddingError("bge-small-zh 模型不可用，请检查 BGE_SMALL_ZH_MODEL_PATH。") from exc


def get_model_status(include_load_check: bool = False) -> dict[str, Any]:
    path = _model_path()
    error = ""
    loadable = False
    dimension: int | None = None
    if not path.exists():
        error = "模型目录不存在"
    elif include_load_check:
        try:
            vector = embed_text("测试")
            loadable = True
            dimension = len(vector)
        except QAEmbeddingError as exc:
            error = str(exc)
    return {
        "name": "bge-small-zh",
        "configured_path": get_configured_model_path(),
        "absolute_path": str(path),
        "exists": path.exists(),
        "loadable": loadable,
        "dimension": dimension,
        "loaded": is_model_loaded(),
        "error": error,
        "setup_hint": "" if path.exists() and not error else _setup_hint(),
    }


def embed_text(text: str) -> list[float]:
    model = _load_model()
    value = model.encode(text or "", normalize_embeddings=True)
    return [float(item) for item in value.tolist()]


def embed_texts(texts: list[str]) -> list[list[float]]:
    model = _load_model()
    values = model.encode(texts, normalize_embeddings=True)
    return [[float(item) for item in row.tolist()] for row in values]


def test_embedding(text: str) -> dict[str, Any]:
    vector = embed_text(text)
    return {
        "status": "success",
        "model": "bge-small-zh",
        "dimension": len(vector),
        "preview": [round(float(item), 6) for item in vector[:5]],
        "text_length": len(text),
    }
