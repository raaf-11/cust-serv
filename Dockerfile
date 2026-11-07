# Backend: FastAPI + retrieval models.
FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    HF_HOME=/opt/hf-cache

WORKDIR /app

# requirements.txt is UTF-16 (a Windows `pip freeze > ...`) and pins
# pywin32, which only exists on Windows. Convert and filter it here rather
# than editing the file. torch is installed first from the CPU-only index:
# the default Linux wheel pulls in ~3 GB of CUDA libraries we don't use.
COPY requirements.txt .
RUN python -c "import pathlib; t = pathlib.Path('requirements.txt').read_text(encoding='utf-16'); \
pathlib.Path('/tmp/req.txt').write_text('\n'.join(l for l in t.splitlines() if l.strip() and not l.lower().startswith('pywin32')))" \
 && pip install torch==2.12.1 --index-url https://download.pytorch.org/whl/cpu \
 && pip install -r /tmp/req.txt

# Bake the embedding + reranker models into the image so the container
# starts offline and doesn't re-download ~200 MB on every fresh run.
RUN python -c "from sentence_transformers import SentenceTransformer, CrossEncoder; \
SentenceTransformer('all-MiniLM-L6-v2'); CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')"

COPY app ./app
COPY data ./data

EXPOSE 8000

# One worker on purpose: the rate limiter keeps its counters in memory
# unless REDIS_URL is set (see app/core/config.py).
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
