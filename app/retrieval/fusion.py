class ReciprocalRankFusion:
    """
    Implements Reciprocal Rank Fusion (RRF).

    Combines multiple ranked retrieval lists into a single ranking.
    """

    def __init__(self, k: int = 60):
        self.k = k

    def fuse(
        self,
        *ranked_lists: list[dict]
    ) -> list[dict]:

        scores = {}

        documents = {}

        for ranked_list in ranked_lists:

            for rank, document in enumerate(ranked_list, start=1):

                doc_id = document["id"]

                documents[doc_id] = document

                score = 1 / (self.k + rank)

                scores[doc_id] = scores.get(doc_id, 0) + score

        fused_results = []

        for doc_id, score in scores.items():

            document = documents[doc_id].copy()

            document["rrf_score"] = score

            fused_results.append(document)

        fused_results.sort(
            key=lambda x: x["rrf_score"],
            reverse=True
        )

        return fused_results


rrf = ReciprocalRankFusion()