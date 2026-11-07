import uuid
from pathlib import Path

from app.services.embedding_service import embedding_service
from app.services.qdrant_service import qdrant_service
from app.services.pdf_service import pdf_service
from app.services.chunking_service import chunking_service
from app.services.elasticsearch_service import elasticsearch_service


class IngestionService:
    def ingest_file(self, file_path: str, source_type: str = "document"):
        text = pdf_service.extract_text(file_path)
        chunks = chunking_service.chunk_text(text)
        print("Number of chunks:", len(chunks))
        filename = Path(file_path).name

        if not chunks:
            print(f"No text extracted from {filename}; nothing ingested.")
            return

        vectors = embedding_service.embed_batch(chunks)
        payloads = []
        qdrant_service.delete_document(filename)
        elasticsearch_service.delete_document(filename)

        for index, chunk in enumerate(chunks):
            payloads.append(
                {
                    "id": str(uuid.uuid5(uuid.NAMESPACE_URL, f"{filename}#{index}")),
                    "text": chunk,
                    "document_name": filename,
                    "chunk_index": index,
                    "source_type": source_type,
                }
            )

        qdrant_service.store_points(vectors, payloads)
        elasticsearch_service.index_chunks(payloads)
        print(f"Ingested {len(payloads)} chunks into Qdrant and Elasticsearch.")
        from app.services.retrieval_service import query_normalizer

        query_normalizer.refresh()


ingestion_service = IngestionService()
