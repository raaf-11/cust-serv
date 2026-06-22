from langchain_text_splitters import (
    RecursiveCharacterTextSplitter
)


class ChunkingService:

    def __init__(self):

        self.text_splitter = (
            RecursiveCharacterTextSplitter(
                chunk_size=500,
                chunk_overlap=100
            )
        )

    def chunk_text(
        self,
        text: str
    ) -> list[str]:

        chunks = self.text_splitter.split_text(
            text
        )

        return chunks


chunking_service = ChunkingService()