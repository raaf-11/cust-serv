# Marks app/guardrails as a package. Intentionally empty —
# imports are explicit throughout (e.g. `from app.guardrails.exceptions
# import GuardrailViolation`) rather than re-exported here, so it's
# always obvious which submodule a symbol comes from.