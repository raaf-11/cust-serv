from pathlib import Path
from app.services.embedding_service import (embedding_service)
from app.services.qdrant_service import (qdrant_service)
from app.services.pdf_service import (pdf_service)

class IngestionService:

    def ingest_file(
        self,
        file_path: str,
        source_type: str = "document"
    ):

        text = pdf_service.extract_text(file_path)

        chunks = [
            chunk.strip()
            for chunk in text.split("\n\n")
            if chunk.strip()
        ]

        vectors = embedding_service.embed_batch(
            chunks
        )

        payloads = []

        filename = Path(
            file_path
        ).name

        for index, chunk in enumerate(
            chunks
        ):

            payloads.append(
                {
                    "text": chunk,
                    "document_name": filename,
                    "chunk_index": index,
                    "source_type": source_type
                }
            )

        qdrant_service.store_points(
            vectors,
            payloads
        )


ingestion_service = IngestionService()