import difflib
import re
from collections import Counter
from typing import Callable, Iterable

WORD_RE = re.compile(r"[A-Za-z]+")

MIN_WORD_LENGTH = 4

SIMILARITY_CUTOFF = 0.8

COMMON_WORDS = {
    "hello",
    "hey",
    "thanks",
    "thank",
    "please",
    "okay",
    "what",
    "when",
    "where",
    "which",
    "while",
    "why",
    "how",
    "does",
    "doesnt",
    "dont",
    "cant",
    "wont",
    "isnt",
    "whats",
    "hasnt",
    "havent",
    "wasnt",
    "have",
    "with",
    "this",
    "that",
    "there",
    "their",
    "they",
    "them",
    "then",
    "than",
    "your",
    "yours",
    "mine",
    "would",
    "could",
    "should",
    "about",
    "really",
    "very",
    "much",
    "many",
    "some",
    "want",
    "need",
    "help",
    "know",
    "tell",
    "give",
    "work",
    "working",
    "doesn",
    "didn",
    "still",
    "again",
    "just",
    "like",
    "also",
    "from",
    "into",
    "only",
    "other",
    "anyone",
    "someone",
    "human",
    "agent",
    "person",
    "talk",
    "speak",
    "chat",
    "real",
}


INFLECTION_SUFFIXES = ("ed", "es", "ly", "s", "d")


class QueryNormalizer:
    def __init__(
        self,
        text_loader: Callable[[], Iterable[str]] | None = None,
        min_word_length: int = MIN_WORD_LENGTH,
        cutoff: float = SIMILARITY_CUTOFF,
        english_words_loader: Callable[[], Iterable[str]] | None = None,
    ):
        self._text_loader = text_loader
        self._english_loader = english_words_loader
        self._english: set[str] | None = None
        self.min_word_length = min_word_length
        self.cutoff = cutoff
        self._vocab: Counter = Counter()
        self._by_length: dict[int, list[str]] = {}
        self._cache: dict[str, str] = {}

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
        if self._text_loader is None:
            return

        self.build(self._text_loader())

    def _ensure_english(self) -> None:
        if self._english is not None:
            return

        self._english = set()

        if self._english_loader is None:
            return

        try:
            self._english = {w.lower() for w in self._english_loader()}
        except Exception as e:
            print("QueryNormalizer: could not load English words:", repr(e))

    def _ensure_vocab(self) -> bool:
        self._ensure_english()

        if self._vocab:
            return True

        try:
            self.refresh()
        except Exception as e:
            print("QueryNormalizer: could not load vocabulary:", repr(e))
            return False

        return bool(self._vocab)

    def correct_word(self, word: str) -> str:
        lower = word.lower()

        if (
            len(lower) < self.min_word_length
            or lower in self._vocab
            or lower in COMMON_WORDS
            or lower in (self._english or ())
        ):
            return word

        if lower in self._cache:
            return self._cache[lower]

        candidates = []
        for length in range(len(lower) - 2, len(lower) + 3):
            candidates.extend(self._by_length.get(length, []))

        matches = difflib.get_close_matches(lower, candidates, n=5, cutoff=self.cutoff)
        matches = [m for m in matches if not lower.startswith(m)]

        for suffix in INFLECTION_SUFFIXES:
            if lower.endswith(suffix) and len(lower) - len(suffix) >= 4:
                stem = lower[: -len(suffix)]
                matches = [m for m in matches if not m.startswith(stem)]
                break

        if not matches:
            self._cache[lower] = word
            return word

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
