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