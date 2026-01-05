from pypdf import PdfReader
from pdf2image import convert_from_path
import pytesseract
import tempfile, os

OCR_MIN_TEXT_CHARS = 80
OCR_DPI = 220
OCR_LANG = "eng"

def extract_pages(pdf_bytes: bytes):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as f:
        f.write(pdf_bytes)
        path = f.name

    reader = PdfReader(path)
    pages = len(reader.pages)
    texts, ocr_pages = [], []

    for i, page in enumerate(reader.pages):
        raw = (page.extract_text() or "").strip()
        if len(raw) < OCR_MIN_TEXT_CHARS:
            images = convert_from_path(path, dpi=OCR_DPI,
                                       first_page=i+1, last_page=i+1)
            ocr = pytesseract.image_to_string(images[0], lang=OCR_LANG)
            if len(ocr) > len(raw):
                raw = ocr
                ocr_pages.append(i+1)
        texts.append(raw)

    os.remove(path)
    full = "\n\n".join(texts)
    return texts, pages, len(full.split()), ocr_pages
