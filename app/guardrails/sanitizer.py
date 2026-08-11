import html
import re

# Matches raw SQL-injection-style payloads riding inside otherwise
# legitimate-looking text (e.g. "12345'; DROP TABLE orders;--").
# We don't try to detect "is this SQL" broadly — that's what
# parameterized queries/ORMs (your SQLAlchemy layer) already prevent
# at the query level. This is specifically about not storing/rendering
# raw dangerous strings that came through chat untouched.
_SQL_PATTERN = re.compile(
    r"(\bdrop\s+table\b|\bdelete\s+from\b|\binsert\s+into\b|;--|\bunion\s+select\b)",
    re.IGNORECASE,
)


def sanitize_text(text: str) -> str:
    """
    Neutralizes dangerous payloads before they're stored in the DB or
    ever rendered in the employee dashboard.

    Two independent defenses, not one:
    1. HTML-escape everything — this is what actually stops XSS
       (<script> tags become inert text, not executable markup) if
       this content is ever rendered as HTML anywhere downstream.
    2. Strip/neutralize obvious SQL-injection-style fragments — this
       is a defense-in-depth backstop. Your SQLAlchemy ORM with
       parameterized queries already prevents SQLi at the query layer;
       this just stops the raw dangerous string from being stored
       verbatim in `conversations` in the first place.
    """
    # 1. HTML-escape — turns <script> into &lt;script&gt;, neutralizing
    # it if ever rendered raw in the employee dashboard.
    text = html.escape(text)

    # 2. Neutralize SQL-injection-style fragments by defanging them,
    # not deleting content wholesale (deleting would silently corrupt
    # legitimate customer messages that happen to contain these words).
    text = _SQL_PATTERN.sub(lambda m: f"[filtered:{m.group(0)}]", text)

    return text