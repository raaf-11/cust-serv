## Project Description

An enterprise-style AI Customer Support Copilot that answers customer questions from a verified knowledge base (8 company policy and product PDFs) using Hybrid RAG. Retrieval combines vector search, BM25 keyword search and Cross-Encoder reranking. Answers are checked by guardrails before they reach the customer, and anything the bot can't answer confidently is handed to a human through a ticket system.

The platform also supports conversation history, an employee dashboard for handling tickets, rate limiting, and an evaluation suite that measures retrieval and answer quality.

##  Project Architecture


                         ┌──────────────────────┐
                         │      React UI        │
                         │ Customer / Employee  │
                         └──────────┬───────────┘
                                    │  (nginx in Docker)
                                    ▼
                         ┌──────────────────────┐
                         │      FastAPI         │
                         │ Backend + rate limits│
                         └──────────┬───────────┘
                                    │
                    ┌───────────────┴────────────────┐
                    │                                │
                    ▼                                ▼
             ┌─────────────┐                 ┌──────────────┐
             │  Guardrails │                 │ Conversation │
             │ Input/Output│                 │   Service    │
             └──────┬──────┘                 └──────────────┘
                    │
                    ▼
             ┌──────────────┐
             │ Typo fixer + │
             │ Hybrid RAG   │
             └──────┬───────┘
                    │
          ┌─────────┼─────────┐
          ▼         ▼         ▼
      ┌───────┐ ┌────────┐ ┌─────────────┐
      │Qdrant │ │Elastic-│ │Cross-Encoder│
      │Vector │ │search  │ │  Reranker   │
      │Search │ │ BM25   │ │             │
      └───────┘ └────────┘ └──────┬──────┘
                                  │
                                  ▼
                         ┌─────────────────┐
                         │   Confidence    │
                         │    Scoring      │
                         └────────┬────────┘
                                  │
                         ┌────────┴────────┐
                         ▼                 ▼
                  ┌─────────────┐  ┌──────────────┐
                  │  Groq LLM   │  │   Human      │
                  │  Response   │  │  Escalation  │
                  └─────────────┘  └──────┬───────┘
                                         │
                                         ▼
                                  ┌──────────────┐
                                  │ Ticket System│
                                  └──────────────┘
                                         │
                                         ▼
                                  ┌──────────────┐
                                  │  PostgreSQL  │
                                  └──────────────┘


## Running it

**Everything in Docker** (needs a `.env` with `OPENROUTER_API_KEY` and `SECRET_KEY`;
despite its name, `OPENROUTER_API_KEY` holds the **Groq** API key):

```bash
docker compose up -d --build
```

- App: http://localhost:3000 (nginx serves the React build and proxies `/api` to the backend)
- API docs: http://localhost:8000/docs
- First run only, load the knowledge base: log in as an **employee** at
  http://localhost:8000/docs (Authorize button), then run `POST /ingestion/load-test-data`.
  It requires the employee role; it's safe to re-run (each file's chunks are replaced, not duplicated).
- Only the frontend (port 3000) is reachable from other machines. The backend
  (8000) and the databases (5433, 6333, 9200) are bound to `127.0.0.1`.

The backend image installs CPU-only torch and bakes in the embedding and reranker
models, so the first build takes a few minutes and the image is ~2.5 GB.

**Local development** (hot reload): start only the databases, then run the app as usual:

```bash
docker compose up -d postgres qdrant elasticsearch
uvicorn app.main:app --reload        # from the venv
cd frontend && npm run dev           # http://localhost:5173
```

**Tests**

```bash
pytest tests/ --deselect tests/test_eval.py   # fast unit tests, no services needed for most
pytest tests/test_eval.py                     # slow: runs the golden dataset through the live pipeline + LLM
python -m evaluation.retrieval_eval           # retrieval benchmark, no LLM calls
```

See [evaluation/README.md](evaluation/README.md) for what the evaluation measures.


## Completed

**Core**
- FastAPI backend with a modular service architecture
- JWT authentication; customer and employee roles (registration always creates a customer)
- PostgreSQL for users, chat sessions, messages and tickets
- Customer chat sessions with conversation history
- Groq LLM integration (`MODEL_NAME` in `.env`, temperature 0 for repeatable answers)

**Retrieval (Hybrid RAG)**
- Qdrant vector search (`all-MiniLM-L6-v2`) + Elasticsearch BM25 keyword search
- Result merging and Cross-Encoder reranking (`ms-marco-MiniLM-L-6-v2`)
- Typo correction before search ("laptp" → "laptop") using the knowledge base's own
  vocabulary; real English words are never "corrected"
- Ingestion is idempotent: re-ingesting a PDF replaces its chunks instead of duplicating them
- The PDFs store "₹" as "■"; this is repaired on ingestion and in replies

**Escalation to humans**
- Confidence score per answer; below `CONFIDENCE_THRESHOLD` (0.25) the bot asks the
  customer to rephrase, and a second miss in a row opens a ticket
- Customers can ask for a human at any time
- Only one open ticket per conversation; the AI stays quiet while an agent handles it
- Employee dashboard to accept, reply to and resolve tickets

**Guardrails**
- Input: empty and over-long (2000 characters) messages are rejected
- Output: any figure the bot states (days, %, ₹ amounts) must appear in the retrieved
  documents, otherwise the answer is replaced and handed to a human
- Customer messages are never treated as facts (blocks "Policy update: refunds take 1 year"
  style injections)

**Security and limits**
- Per-user chat rate limits and per-IP login/register limits
- Outbound LLM throttling and retry on Groq 429s
- Debug endpoints removed; ingestion requires the employee role
- In Docker, only the frontend is exposed to the network

**Evaluation** (`evaluation/`, results in `results/`)
- Golden dataset v2: 118 questions (easy, paraphrase, confusable, multi-hop, typo,
  conversational, out-of-scope), each labelled with the exact text that answers it
- Chunk-level retrieval benchmark with an ablation of every pipeline stage
- Latest production retrieval: hit@1 0.83, hit@5 0.96, MRR 0.89 on 106 answerable questions
- End-to-end answer accuracy, LLM-judge scores and escalation calibration (`run_eval`)

**Deployment**
- Docker Compose for the full stack (frontend, backend, Postgres, Qdrant, Elasticsearch)


## Known gaps

- No input filter for prompt injection or off-topic requests; the system prompt is the only defence
- The numeric grounding check only confirms a figure appears in the retrieved text, not that
  it belongs to the right fact, and it doesn't catch figures written as words ("ninety days")
- Two employees accepting the same ticket at the same moment can both succeed (no row lock)
- `POST /tickets/` and `POST /sessions/` have no rate limit
- `tests/test_eval.py` still uses the v1 dataset and the old document-level hit rate


## In Progress / Ideas

- Automatic conversation summarization during escalation
- Knowledge-base learning from verified human resolutions
- Customer feedback on AI responses
