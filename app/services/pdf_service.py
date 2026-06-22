from pypdf import PdfReader


class PDFService:

    def extract_text(
        self,
        file_path: str
    ) -> str:

        reader = PdfReader(file_path)

        text = ""

        for page in reader.pages:

            text += page.extract_text()

        return text


pdf_service = PDFService()