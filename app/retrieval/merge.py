class MergeRetrieverResults:
    def merge(self, *result_lists: list[dict]) -> list[dict]:
        merged = {}

        for result_list in result_lists:
            for document in result_list:
                if "id" not in document:
                    raise ValueError("Retrieved document is missing the 'id' field.")

                doc_id = document["id"]

                if doc_id not in merged:
                    merged[doc_id] = document.copy()

                else:
                    merged[doc_id].update(document)

        return list(merged.values())


merge_results = MergeRetrieverResults()
