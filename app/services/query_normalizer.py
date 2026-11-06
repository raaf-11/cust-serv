"""
Typo correction for user queries, using the knowledge base's own vocabulary.

Why this exists
---------------
"laptp" is not a word, so:
  * Elasticsearch BM25 finds nothing for it (exact token match), and
  * the MiniLM embedding splits it into meaningless word-pieces,
which drags every retrieval score down and used to trigger escalation.

We build a vocabulary from every chunk that was ingested and snap unknown
words in the query to the closest known word ("laptp" -> "laptop",
"warrenty" -> "warranty"). Because the vocabulary comes from our own
documents, we only ever "correct" towards words the KB can actually answer
about, and a word that is already known is never touched.

This module has no heavy imports so it can be unit-tested on its own.
"""

import difflib
import re
from collections import Counter
from typing import Callable, Iterable

WORD_RE = re.compile(r"[A-Za-z]+")

# Short words are too ambiguous to correct safely ("hte" vs "the" is
# harmless, but "ram"/"rom"/"run" style swaps are not).
MIN_WORD_LENGTH = 4

# difflib similarity ratio required to accept a correction. 0.8 lets one
# missing/extra/swapped letter through on 5+ letter words but rejects
# unrelated words ("hello" vs "help" = 0.67).
SIMILARITY_CUTOFF = 0.8

# Everyday words that may not appear in the PDFs but must never be
# "corrected" into a KB word.
COMMON_WORDS = {
    "hello", "hey", "thanks", "thank", "please", "okay", "what", "when",
    "where", "which", "while", "why", "how", "does", "doesnt", "dont",
    "cant", "wont", "isnt", "whats", "hasnt", "havent", "wasnt", "have", "with", "this", "that", "there",
    "their", "they", "them", "then", "than", "your", "yours", "mine",
    "would", "could", "should", "about", "really", "very", "much",
    "many", "some", "want", "need", "help", "know", "tell", "give",
    "work", "working", "doesn", "didn", "still", "again", "just",
    "like", "also", "from", "into", "only", "other", "anyone", "someone",
    "human", "agent", "person", "talk", "speak", "chat", "real",
}


INFLECTION_SUFFIXES = ("ed", "es", "ly", "s", "d")


class QueryNormalizer:

    def __init__(
        self,
        text_loader: Callable[[], Iterable[str]] | None = None,
        min_word_length: int = MIN_WORD_LENGTH,
        cutoff: float = SIMILARITY_CUTOFF,
    ):
        self._text_loader = text_loader
        self.min_word_length = min_word_length
        self.cutoff = cutoff
        self._vocab: Counter = Counter()
        self._by_length: dict[int, list[str]] = {}
        self._cache: dict[str, str] = {}

    # ------------------------------------------------------------------
    # Vocabulary
    # ------------------------------------------------------------------

    def build(self, texts: Iterable[str]) -> None:
        vocab = Counter()

        for text in texts:
            vocab.update(w.lower() for w in WORD_RE.findall(text))

        self._vocab = vocab
        self._by_length = {}

        for word in vocab:
            self._by_length.setdefault(len(word), []).append(word)

        self._cache = {}

    def refresh(self) -> None:
        """Rebuild from the loader (call after ingesting new documents)."""

        if self._text_loader is None:
            return

        self.build(self._text_loader())

    def _ensure_vocab(self) -> bool:
        if self._vocab:
            return True

        try:
            self.refresh()
        except Exception as e:  # KB unreachable: fail open, never block chat
            print("QueryNormalizer: could not load vocabulary:", repr(e))
            return False

        return bool(self._vocab)

    # ------------------------------------------------------------------
    # Correction
    # ------------------------------------------------------------------

    def correct_word(self, word: str) -> str:
        lower = word.lower()

        if (
            len(lower) < self.min_word_length
            or lower in self._vocab
            or lower in COMMON_WORDS
        ):
            return word

        if lower in self._cache:
            return self._cache[lower]

        # Only compare against words of similar length (fast + safer).
        candidates = []
        for length in range(len(lower) - 2, len(lower) + 3):
            candidates.extend(self._by_length.get(length, []))

        matches = difflib.get_close_matches(
            lower, candidates, n=5, cutoff=self.cutoff
        )

        # A candidate that is just a prefix of the word ("arrived" ->
        # "arrive", "slowly" -> "slow") means the word is a real inflection
        # we simply haven't seen, not a typo. Leave it alone.
        matches = [m for m in matches if not lower.startswith(m)]

        # Same idea for real inflections that only differ in their ending
        # ("arrived" vs "arrives"): if the word ends in a common suffix and
        # the candidate shares the whole stem, it's not a typo.
        for suffix in INFLECTION_SUFFIXES:
            if lower.endswith(suffix) and len(lower) - len(suffix) >= 4:
                stem = lower[: -len(suffix)]
                matches = [m for m in matches if not m.startswith(stem)]
                break

        if not matches:
            self._cache[lower] = word
            return word

        # Best similarity first; break ties with how common the word is in
        # the KB. Sorting makes the choice fully deterministic.
        best = max(
            matches,
            key=lambda m: (
                difflib.SequenceMatcher(None, lower, m).ratio(),
                self._vocab[m],
                m,
            ),
        )

        self._cache[lower] = best
        return best

    def normalize(self, query: str) -> str:
        if not query or not self._ensure_vocab():
            return query

        return WORD_RE.sub(lambda m: self.correct_word(m.group(0)), query)
