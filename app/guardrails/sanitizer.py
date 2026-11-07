import html
import re

_SQL_PATTERN = re.compile(
    r"(\bdrop\s+table\b|\bdelete\s+from\b|\binsert\s+into\b|;--|\bunion\s+select\b)",
    re.IGNORECASE,
)


def sanitize_text(text: str) -> str:
    text = html.escape(text)
    text = _SQL_PATTERN.sub(lambda m: f"[filtered:{m.group(0)}]", text)
    return text
