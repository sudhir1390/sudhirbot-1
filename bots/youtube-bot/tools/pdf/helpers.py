import fitz  # PyMuPDF
from shared.utils import trim_to_budget

MAX_PAGES  = 200
MAX_TOKENS = 178_000


def extract_text(pdf_bytes: bytes) -> tuple[str, int, int, bool, bool]:
    """
    Extract text from PDF bytes.

    Returns:
        text          (str)  — extracted and token-trimmed text
        total_pages   (int)  — total pages in the PDF
        extracted     (int)  — pages actually extracted (capped at MAX_PAGES)
        page_warning  (bool) — True if PDF exceeded MAX_PAGES
        token_warning (bool) — True if text was trimmed to fit token budget
    """
    doc          = fitz.open(stream=pdf_bytes, filetype="pdf")
    total_pages  = len(doc)
    page_warning = total_pages > MAX_PAGES
    extracted    = min(total_pages, MAX_PAGES)

    raw_text = ""
    for i in range(extracted):
        raw_text += doc[i].get_text()

    trimmed       = trim_to_budget(raw_text, MAX_TOKENS)
    token_warning = len(trimmed) < len(raw_text)

    return trimmed, total_pages, extracted, page_warning, token_warning


def fmt_load_message(filename: str, total_pages: int, extracted: int,
                     page_warning: bool, token_warning: bool) -> str:
    """
    Build the confirmation message shown to the user after a PDF is loaded.
    Warnings are appended only when relevant.
    """
    lines = [f"📄 *{filename}* ({total_pages} pages)"]

    if page_warning:
        ignored = total_pages - extracted
        lines.append(
            f"⚠️ Only first {extracted} of {total_pages} pages processed "
            f"— remaining {ignored} pages ignored."
        )

    if token_warning:
        lines.append(
            "⚠️ Content was trimmed to fit Claude's limit "
            "— very end of document may be missing."
        )

    lines.append("\nAsk me anything!")
    return "\n".join(lines)
