import re
from pathlib import Path


class QADocumentParseError(RuntimeError):
    pass


SUPPORTED_EXTENSIONS = {".txt", ".md", ".docx"}


def _clean(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _read_text(path: Path) -> str:
    for encoding in ("utf-8", "gbk"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    raise QADocumentParseError("文档编码无法识别，请使用 UTF-8 或 GBK 文本。")


def _read_docx(path: Path) -> str:
    try:
        from docx import Document
    except Exception as exc:
        raise QADocumentParseError("docx 解析依赖不可用，请安装 python-docx。") from exc
    try:
        document = Document(str(path))
        return "\n".join(paragraph.text for paragraph in document.paragraphs)
    except Exception as exc:
        raise QADocumentParseError("docx 文档解析失败。") from exc


def parse_document(path: Path) -> tuple[str, str]:
    extension = path.suffix.lower()
    if extension not in SUPPORTED_EXTENSIONS:
        raise QADocumentParseError("仅支持 txt、md、docx 文档入库。")
    text = _read_docx(path) if extension == ".docx" else _read_text(path)
    cleaned = _clean(text)
    if not cleaned:
        raise QADocumentParseError("文档内容为空，无法入库。")
    return cleaned, extension.lstrip(".")
