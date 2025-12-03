#PDF → 텍스트
# pdf_utils.py
import pdfplumber
from pdf2image import convert_from_bytes
import pytesseract


def extract_text_from_pdf(pdf_file) -> str:
    """
    pdfplumber로 텍스트 추출을 시도하고,
    텍스트가 너무 적으면 pdf2image + Tesseract로 OCR을 시도한다.
    """
    text = ""
    try:
        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"
    except Exception:
        pass

    # 텍스트가 너무 적으면 OCR 시도
    if len(text) < 50:
        pdf_file.seek(0)
        try:
            images = convert_from_bytes(pdf_file.read())
            text = ""
            for image in images:
                text += pytesseract.image_to_string(image, lang="kor+eng") + "\n"
        except Exception:
            pass

    return text
