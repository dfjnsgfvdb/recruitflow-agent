import re
from typing import Tuple

MAX_RESUME_TEXT_LENGTH = 30000


def extract_text_from_pdf(file_path: str) -> Tuple[str, str]:
    """低成本 PDF 文本抽取：先用 pypdf，文本不足时用 pdfplumber 兜底；不做 OCR。"""
    errors = []
    pypdf_text = ""
    try:
        from pypdf import PdfReader

        reader = PdfReader(file_path)
        parts = []
        for page in reader.pages:
            parts.append(page.extract_text() or "")
        pypdf_text = _clean_resume_text("\n".join(parts))
    except Exception as exc:
        errors.append(f"pypdf 抽取失败: {exc}")

    if len(pypdf_text) >= 200:
        return pypdf_text[:MAX_RESUME_TEXT_LENGTH], "pypdf"

    plumber_text = ""
    try:
        import pdfplumber

        parts = []
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                parts.append(page.extract_text() or "")
        plumber_text = _clean_resume_text("\n".join(parts))
    except Exception as exc:
        errors.append(f"pdfplumber 抽取失败: {exc}")

    best_text = plumber_text if len(plumber_text) > len(pypdf_text) else pypdf_text
    if best_text:
        parser_name = "pdfplumber" if best_text == plumber_text else "pypdf"
        return best_text[:MAX_RESUME_TEXT_LENGTH], parser_name

    if len(errors) < 2:
        # PDF 结构可读但没有可抽取文本，通常是扫描件或图片型简历，由上层标记 NEED_OCR。
        return "", "pypdf/pdfplumber"

    raise RuntimeError("; ".join(errors) or "PDF 未抽取到可用文本")


def _clean_resume_text(text: str) -> str:
    text = text.replace("\u0000", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()
