class MergeRetrieverResults:
    """
    Merges results from multiple retrievers and removes duplicates.

    If the same document is returned by multiple retrievers,
    their metadata (e.g., vector_score, bm25_score) is merged.
    """

    def merge(self, *result_lists: list[dict]) -> list[dict]:

        merged = {}

        for result_list in result_lists:

            for document in result_list:

                if "id" not in document:
                    raise ValueError(
                        "Retrieved document is missing the 'id' field."
                    )

                doc_id = document["id"]

                if doc_id not in merged:
                    merged[doc_id] = document.copy()

                else:
                    # Merge metadata from different retrievers
                    merged[doc_id].update(document)

        return list(merged.values())


merge_results = MergeRetrieverResults()