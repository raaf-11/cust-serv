## Project Description

An enterprise-style AI Customer Support Copilot that uses Hybrid RAG to provide grounded customer support responses from a verified knowledge base. The system combines vector search, BM25 keyword search, and Cross-Encoder reranking to improve retrieval quality, while guardrails help prevent prompt injection, jailbreaks, off-topic requests, and unsupported responses.

The platform also supports human-in-the-loop escalation, ticket management, conversation history, and employee-side support workflows.

##  Project Architecture


                         ┌──────────────────────┐
                         │      React UI        │
                         │ Customer / Employee  │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │      FastAPI         │
                         │      Backend         │
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

**Everything in Docker** (needs a `.env` with `OPENROUTER_API_KEY` and `SECRET_KEY`):

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


## Current Development

## Completed

- FastAPI backend with modular service architecture
- JWT-based authentication and protected routes
- PostgreSQL database integration
- Customer chat sessions and conversation history
- Hybrid RAG pipeline
  - Qdrant vector retrieval
  - Elasticsearch BM25 keyword retrieval
  - Reciprocal Rank Fusion / result merging
  - Cross-Encoder reranking
- Grounded LLM responses using retrieved knowledge
- Groq LLM integration
- Human support ticket management
- Employee support workflow
- Confidence score calculation for retrieval results
- Initial confidence threshold (`0.60`) for identifying potentially low-confidence responses
- Automatically generating support tickets from escalated conversations

### The results folder contain the retireval results and score

###  In Progress

- Automatic human escalation based on confidence score
- Automatic conversation summarization during escalation
- Improving confidence-score calibration using real retrieval results
- Guardrails failed-Hindering the response(Need to fix)
- Knowledge-base learning from verified human resolutions
- Customer feedback and AI response evaluation
- Better Frontend