import re

from pypdf import PdfReader

_RUPEE_PLACEHOLDER = re.compile(r"■(?=\s?\d)")


def fix_rupee_symbol(text: str) -> str:
    return _RUPEE_PLACEHOLDER.sub("₹", text)


class PDFService:
    def extract_text(self, file_path: str) -> str:
        reader = PdfReader(file_path)
        text = ""

        for page in reader.pages:
            text += page.extract_text()

        return fix_rupee_symbol(text)


pdf_service = PDFService()
