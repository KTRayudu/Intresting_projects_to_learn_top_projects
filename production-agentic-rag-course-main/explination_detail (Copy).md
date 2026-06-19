# Production Agentic RAG System — Complete End-to-End Explanation

> **Confirmation:** YES, this code is exactly related to a Production Agentic RAG (Retrieval-Augmented Generation) system built for academic paper research. It fetches papers from arXiv, processes them, stores them with search indexes, and lets you ask AI-powered questions. Built in 7 weeks, evolving from basic infrastructure to a full agentic AI system with Telegram bot.

---

## TABLE OF CONTENTS

1. [What Is This System? (Simple Explanation)](#1-what-is-this-system)
2. [Big Picture — How It All Works Together](#2-big-picture)
3. [Project Folder Structure — Every File Explained](#3-folder-structure)
4. [Week-by-Week Journey (What Was Added Each Week)](#4-week-by-week-journey)
5. [Infrastructure (compose.yml) — All Services Explained](#5-infrastructure)
6. [Configuration (src/config.py) — Every Setting Explained](#6-configuration)
7. [Application Entry Point (src/main.py) — Line by Line](#7-main-application)
8. [Data Ingestion Pipeline (Airflow DAGs)](#8-data-ingestion-pipeline)
9. [Search System (OpenSearch) — BM25 and Hybrid](#9-search-system)
10. [Text Chunking (src/services/indexing/text_chunker.py)](#10-text-chunking)
11. [LLM Integration (Ollama)](#11-llm-integration)
12. [RAG Endpoints (src/routers/ask.py)](#12-rag-endpoints)
13. [Caching System (Redis)](#13-caching-system)
14. [Monitoring (Langfuse)](#14-monitoring-langfuse)
15. [Agentic RAG — The Intelligence Layer (Week 7)](#15-agentic-rag)
16. [Telegram Bot](#16-telegram-bot)
17. [How to Run the System — Step by Step](#17-how-to-run)
18. [What Results You Get — Expected Outputs](#18-expected-results)
19. [Different Ways to Do Each Part (Alternatives)](#19-alternative-approaches)
20. [Comparison Tables — All Key Differences](#20-comparison-tables)
21. [Cheat Sheet — Quick Reference](#21-cheat-sheet)
22. [Summary](#22-summary)
23. [Conclusion](#23-conclusion)

---

## 1. WHAT IS THIS SYSTEM?

### Simple Explanation (For Someone New to Coding)

Imagine you have thousands of academic research papers about Artificial Intelligence. You want to ask questions like "How does BERT work?" or "What are transformer architectures?" and get accurate answers with sources.

**Without this system:** You'd have to read every paper yourself. Takes weeks.

**With this system:** You type a question → the AI finds relevant paper sections → the AI reads them → the AI answers you in seconds.

This is called **RAG = Retrieval-Augmented Generation**:
- **Retrieval**: Finding the right paper sections ("retrieving" them from a database)
- **Augmented**: Giving those sections to an AI as extra context ("augmenting" the AI's knowledge)
- **Generation**: The AI generates (writes) an answer using that context

### What Makes It "Agentic"?

A normal RAG system just searches and answers. An **Agentic RAG** is smarter:
- It **checks** if your question is even about research papers (guardrail)
- It **grades** whether the found documents are actually relevant
- If not relevant, it **rewrites your question** and tries again
- It **tracks its reasoning** so you can see what it did

### What Makes It "Production"?

"Production" means it's built like a real company product, not a homework project:
- Multiple services running together (Docker containers)
- Automated daily data fetching (Airflow)
- Caching to avoid repeating expensive AI calls (Redis)
- Monitoring to track performance and costs (Langfuse)
- Telegram bot for mobile access

---

## 2. BIG PICTURE — HOW IT ALL WORKS TOGETHER

```
┌─────────────────────────────────────────────────────────────────────┐
│                     USER ASKS A QUESTION                            │
│            (via API / Gradio UI / Telegram bot)                     │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    FASTAPI APPLICATION (Port 8000)                  │
│                    src/main.py + src/routers/                       │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                ┌────────────┼────────────┐
                │            │            │
                ▼            ▼            ▼
         /ask endpoint  /stream     /agentic-ask
         (simple RAG)  (streaming)  (intelligent RAG)
                │            │            │
                └────────────┴────────────┘
                             │
                    ┌────────▼────────┐
                    │  REDIS CACHE    │  ← Check first (instant)
                    │  (Port 6379)    │
                    └────────┬────────┘
                             │ (cache miss)
                    ┌────────▼────────┐
                    │   OPENSEARCH    │  ← Find relevant paper chunks
                    │  (Port 9200)    │  ← BM25 + Vector (hybrid)
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │     OLLAMA      │  ← Local AI model answers
                    │  (Port 11434)   │  ← llama3.2
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │    LANGFUSE     │  ← Track everything
                    │  (Port 3001)    │  ← Monitor performance
                    └─────────────────┘

═══════════════════ BACKGROUND DATA PIPELINE ═══════════════════

┌─────────────────────────────────────────────────────────────────────┐
│                   AIRFLOW (Port 8080) — Runs Daily                  │
│                                                                     │
│  arXiv API → Download PDFs → Parse PDFs → Store in PostgreSQL       │
│            → Chunk text → Generate Embeddings → Index in OpenSearch │
└─────────────────────────────────────────────────────────────────────┘
```

### Data Flow — Step by Step

**Step 1: Paper Ingestion (Automatic, Daily)**
```
arXiv.org API → download PDF → Docling parses PDF → 
extract text/sections → PostgreSQL stores metadata → 
split into chunks (600 words each) → Jina AI generates 
embeddings (1024-dimension vectors) → OpenSearch indexes 
both the text AND the vector
```

**Step 2: User Asks a Question**
```
User types question → FastAPI receives it → 
Check Redis cache (if found, return immediately) →
Generate embedding for the question (Jina AI) →
OpenSearch hybrid search (keyword + semantic) →
Top-k most relevant paper chunks returned →
Build prompt: "Here are papers: [chunks]. Answer: [question]" →
Ollama (local AI) generates answer →
Return answer + source URLs
```

---

## 3. PROJECT FOLDER STRUCTURE — EVERY FILE EXPLAINED

```
production-agentic-rag-course-main/
│
├── compose.yml              ← Docker: defines all 15 services and how they connect
├── Dockerfile               ← How to build the FastAPI API container
├── .env.example             ← Template for all configuration variables
├── .env.test                ← Test environment configuration
├── pyproject.toml           ← Python project metadata, dependencies, tool settings
├── Makefile                 ← Shortcuts: "make start", "make test", etc.
├── gradio_launcher.py       ← Launches the web chat interface on port 7861
├── README.md                ← Documentation
│
├── src/                     ← Main application source code
│   ├── main.py              ← FastAPI app entry point — creates app, starts services
│   ├── config.py            ← All settings loaded from .env file
│   ├── database.py          ← PostgreSQL database setup with SQLAlchemy
│   ├── dependencies.py      ← Dependency injection — passes services to endpoints
│   ├── exceptions.py        ← Custom error types (OllamaConnectionError, etc.)
│   ├── middlewares.py       ← Request/response middleware
│   ├── gradio_app.py        ← Gradio web UI definition
│   │
│   ├── models/              ← Database table definitions
│   │   └── paper.py         ← Paper table: arxiv_id, title, abstract, etc.
│   │
│   ├── schemas/             ← Data validation with Pydantic
│   │   ├── api/
│   │   │   ├── ask.py       ← AskRequest (query, top_k, use_hybrid) + AskResponse
│   │   │   ├── health.py    ← HealthResponse schema
│   │   │   └── search.py    ← HybridSearchRequest + SearchResponse
│   │   ├── arxiv/
│   │   │   └── paper.py     ← ArxivPaper schema from API response
│   │   ├── embeddings/
│   │   │   └── jina.py      ← JinaEmbeddingRequest/Response schemas
│   │   ├── indexing/
│   │   │   └── models.py    ← TextChunk + ChunkMetadata schemas
│   │   └── ollama.py        ← RAGResponse schema
│   │
│   ├── routers/             ← API endpoints (URL handlers)
│   │   ├── ping.py          ← GET /health → checks all services
│   │   ├── ask.py           ← POST /ask and POST /stream → RAG question answering
│   │   ├── hybrid_search.py ← POST /hybrid-search → search without LLM
│   │   └── agentic_ask.py   ← POST /agentic-ask → intelligent multi-step RAG
│   │
│   ├── db/                  ← Database access layer
│   │   ├── factory.py       ← Creates database connection
│   │   └── interfaces/
│   │       ├── base.py      ← Abstract database interface
│   │       └── postgresql.py← PostgreSQL-specific implementation
│   │
│   ├── repositories/        ← Database query functions
│   │   └── paper.py         ← save_paper(), get_paper(), list_papers()
│   │
│   └── services/            ← Business logic — the core of the system
│       │
│       ├── arxiv/           ← Fetches papers from arXiv API
│       │   ├── client.py    ← Makes HTTP requests to arXiv, parses XML
│       │   └── factory.py   ← Creates ArxivClient instance
│       │
│       ├── pdf_parser/      ← Parses PDF files into structured text
│       │   ├── parser.py    ← PDF parser interface
│       │   ├── docling.py   ← Uses Docling library for PDF parsing
│       │   └── factory.py   ← Creates PDF parser instance
│       │
│       ├── indexing/        ← Prepares text for search indexing
│       │   ├── text_chunker.py  ← Splits long papers into 600-word chunks
│       │   ├── hybrid_indexer.py← Orchestrates chunking + embedding + indexing
│       │   └── factory.py   ← Creates indexing service
│       │
│       ├── embeddings/      ← Converts text to vectors (numbers)
│       │   ├── jina_client.py   ← Calls Jina AI API for 1024-dim embeddings
│       │   └── factory.py   ← Creates embeddings service
│       │
│       ├── opensearch/      ← Search engine client
│       │   ├── client.py    ← OpenSearchClient: search, index, delete
│       │   ├── query_builder.py ← Builds BM25 and hybrid search queries
│       │   ├── index_config_hybrid.py ← Index mappings and RRF pipeline config
│       │   └── factory.py   ← Creates OpenSearch client
│       │
│       ├── ollama/          ← Local AI model (LLM) client
│       │   ├── client.py    ← Sends prompts to Ollama, gets AI responses
│       │   ├── prompts.py   ← Prompt building logic
│       │   ├── prompts/
│       │   │   └── rag_system.txt ← The system prompt for academic paper QA
│       │   └── factory.py   ← Creates Ollama client
│       │
│       ├── cache/           ← Redis caching service
│       │   ├── client.py    ← CacheClient: get/set responses by hash key
│       │   └── factory.py   ← Creates cache client
│       │
│       ├── langfuse/        ← Monitoring and observability
│       │   ├── client.py    ← LangfuseTracer: creates traces and spans
│       │   ├── tracer.py    ← RAGTracer: high-level tracing helpers
│       │   └── factory.py   ← Creates Langfuse tracer
│       │
│       ├── telegram/        ← Telegram bot
│       │   ├── bot.py       ← TelegramBot: handles commands and messages
│       │   └── factory.py   ← Creates Telegram bot if token is configured
│       │
│       ├── metadata_fetcher.py ← Orchestrates the full paper ingestion pipeline
│       │
│       └── agents/          ← Agentic RAG (Week 7) — the intelligent layer
│           ├── agentic_rag.py   ← AgenticRAGService: builds and runs LangGraph
│           ├── state.py     ← AgentState: what data flows between nodes
│           ├── context.py   ← Context: dependencies passed to nodes
│           ├── config.py    ← GraphConfig: agent configuration
│           ├── models.py    ← GuardrailScoring, GradingResult, SourceItem
│           ├── prompts.py   ← All LLM prompts for agent nodes
│           ├── tools.py     ← create_retriever_tool() for document lookup
│           └── nodes/       ← Each step in the agent workflow
│               ├── guardrail_node.py     ← Scores if question is in-domain
│               ├── retrieve_node.py      ← Creates tool call to fetch documents
│               ├── grade_documents_node.py ← LLM grades if docs are relevant
│               ├── rewrite_query_node.py   ← LLM rewrites query if needed
│               ├── generate_answer_node.py ← LLM generates final answer
│               ├── out_of_scope_node.py    ← Handles off-topic questions
│               └── utils.py              ← Helper: get_latest_query(), etc.
│
├── airflow/                 ← Automated workflow orchestration
│   ├── Dockerfile           ← How to build the Airflow container
│   ├── entrypoint.sh        ← Startup script for Airflow
│   ├── requirements-airflow.txt ← Python packages needed by Airflow
│   ├── dags/
│   │   ├── arxiv_paper_ingestion.py ← Main DAG: runs daily paper pipeline
│   │   ├── hello_world_dag.py       ← Simple test DAG
│   │   └── arxiv_ingestion/         ← Modular pipeline tasks
│   │       ├── setup.py    ← Environment setup task
│   │       ├── fetching.py ← Downloads papers from arXiv
│   │       ├── indexing.py ← Chunks, embeds, and indexes papers
│   │       └── reporting.py ← Generates daily summary report
│   └── README.md
│
├── notebooks/               ← Weekly learning Jupyter notebooks
│   ├── week1/               ← Infrastructure setup exercises
│   ├── week2/               ← ArXiv API + PDF parsing exercises
│   ├── week3/               ← OpenSearch + BM25 exercises
│   ├── week4/               ← Chunking + hybrid search exercises
│   ├── week5/               ← Complete RAG exercises
│   ├── week6/               ← Caching + monitoring exercises
│   └── week7/               ← Agentic RAG exercises
│
├── tests/                   ← Automated tests
│   ├── unit/                ← Fast tests that test individual functions
│   ├── api/                 ← Tests for HTTP endpoints
│   └── integration/         ← Tests that require running services
│
└── static/                  ← Images used in README
    ├── week1_infra_setup.png
    ├── week2_data_ingestion_flow.png
    └── ... (architecture diagrams for each week)
```

---

## 4. WEEK-BY-WEEK JOURNEY (WHAT WAS ADDED EACH WEEK)

### Week 1 — Infrastructure Foundation

**What was there before:** Nothing. Empty project.

**What was added:**
- `compose.yml` with Docker services: FastAPI, PostgreSQL, OpenSearch, Airflow, Ollama
- `src/main.py` — Basic FastAPI app with health check
- `src/config.py` — Configuration management
- `src/models/paper.py` — Database table for papers
- `src/routers/ping.py` — `/health` endpoint

**What it does:** Sets up all the "buildings" (services) but nothing is working yet. Like building a city's infrastructure — roads, electricity, buildings — before anyone moves in.

**Key result:** `curl http://localhost:8000/api/v1/health` returns `{"status": "healthy"}`

---

### Week 2 — Data Ingestion Pipeline

**What was added:**
- `src/services/arxiv/client.py` — Fetches paper metadata from arXiv API
- `src/services/pdf_parser/docling.py` — Parses PDF files into structured text
- `src/services/metadata_fetcher.py` — Orchestrates the full ingestion
- `airflow/dags/arxiv_paper_ingestion.py` — Automated daily pipeline
- `src/repositories/paper.py` — Save/get papers from PostgreSQL

**What it does:** Like a librarian who goes online every day, downloads new research papers, extracts the text, and files them in the library (PostgreSQL database).

**Key result:** PostgreSQL fills up with paper records. Airflow dashboard shows green checkmarks.

---

### Week 3 — Keyword Search (BM25)

**What was added:**
- `src/services/opensearch/client.py` — OpenSearch connection and search
- `src/services/opensearch/query_builder.py` — Builds BM25 search queries
- `src/routers/hybrid_search.py` — `/search` endpoint
- Papers indexed in OpenSearch with title, abstract, full text

**What it does:** Like a library index — type keywords, get matching papers. BM25 is the algorithm that calculates relevance scores based on word frequency.

**Key result:** `POST /search` with `{"query": "transformer attention"}` returns ranked paper list.

---

### Week 4 — Chunking + Hybrid Search (Semantic + Keyword)

**What was added:**
- `src/services/indexing/text_chunker.py` — Splits papers into 600-word chunks
- `src/services/embeddings/jina_client.py` — Gets 1024-dim vectors for text
- `src/services/opensearch/index_config_hybrid.py` — Hybrid index with vector field
- `src/services/indexing/hybrid_indexer.py` — Orchestrates chunk indexing
- OpenSearch RRF (Reciprocal Rank Fusion) pipeline for merging results

**What it does:** Instead of searching entire papers, each paper is split into smaller pieces (chunks). Each chunk gets a "fingerprint" (embedding vector) that represents its meaning. When you search, both keyword matching AND meaning matching happen, and results are merged.

**Key difference from Week 3:**
- Week 3: Searches "does this document contain the word transformer?"
- Week 4: Searches "does this document MEAN something about transformer architectures?" — even without those exact words

**Key result:** `POST /hybrid-search` now returns more semantically relevant results.

---

### Week 5 — Complete RAG with LLM

**What was added:**
- `src/services/ollama/client.py` — Talks to local Llama3.2 AI model
- `src/services/ollama/prompts.py` — Builds the prompt with paper context
- `src/routers/ask.py` — `/ask` and `/stream` endpoints
- `src/gradio_app.py` — Web chat interface

**What it does:** Now instead of just finding papers, the system reads the found chunks and **generates an answer**. The prompt looks like:

```
Here are relevant research papers:
[chunk 1: "Transformers use attention mechanisms..."]
[chunk 2: "BERT is a transformer-based model..."]

User question: "How does BERT work?"
Answer:
```

The AI (Ollama/Llama) reads this and writes an answer.

**Key result:** `POST /ask` with `{"query": "How does BERT work?"}` returns a full written answer with sources.

---

### Week 6 — Production Monitoring and Caching

**What was added:**
- `src/services/cache/client.py` — Redis exact-match cache
- `src/services/langfuse/` — Full tracing with Langfuse
- Redis service in compose.yml
- Langfuse + ClickHouse + MinIO services in compose.yml
- Cache checks in `src/routers/ask.py`

**What it does:**
- **Cache:** If someone asks the same question, return the stored answer instantly (no AI call needed). 150-400x speedup.
- **Langfuse:** Records every AI call — how long it took, how many tokens, what the prompt was. Like a black box recorder for your AI.

**Key result:** Second identical question returns instantly. Langfuse dashboard shows all traces.

---

### Week 7 — Agentic RAG with LangGraph + Telegram

**What was added:**
- `src/services/agents/` — Complete LangGraph-based agent system
- 6 intelligent nodes (guardrail, retrieve, grade, rewrite, generate, out_of_scope)
- `src/routers/agentic_ask.py` — `/agentic-ask` endpoint
- `src/services/telegram/` — Telegram bot
- Langfuse tracing in every node

**What it does:** The agent is like a smart researcher:
1. First checks if your question is about CS/AI/ML papers (guardrail)
2. Searches for relevant papers (retrieve)
3. Asks itself: "Are these papers actually relevant?" (grade)
4. If not relevant, rewrites your question and searches again (rewrite)
5. If relevant, writes a comprehensive answer (generate)
6. If out of scope, politely declines and explains why

---

## 5. INFRASTRUCTURE (compose.yml) — ALL SERVICES EXPLAINED

The `compose.yml` file is like a blueprint for a city. It defines 15 services (containers), each running in isolation but connected by a network.

### Service 1: api (FastAPI)

```yaml
api:
  build: .                    # Build from Dockerfile in current directory
  container_name: rag-api     # Name the container "rag-api"
  ports:
    - "8000:8000"             # Map host port 8000 to container port 8000
  depends_on:                 # Don't start until these are ready:
    postgres:
      condition: service_healthy
    opensearch:
      condition: service_healthy
    redis:
      condition: service_healthy
```

**What it does:** Runs the main Python FastAPI application. The `depends_on` ensures PostgreSQL, OpenSearch, and Redis are healthy before the API starts. If you miss this, the API would crash because the database isn't ready yet.

**healthcheck:** Every 30 seconds it calls its own `/health` endpoint to verify it's working.

### Service 2: postgres (PostgreSQL 16)

```yaml
postgres:
  image: postgres:16-alpine          # Official PostgreSQL image, alpine = small
  environment:
    - POSTGRES_DB=rag_db             # Create database named "rag_db"
    - POSTGRES_USER=rag_user         # Username
    - POSTGRES_PASSWORD=rag_password # Password
  volumes:
    - postgres_data:/var/lib/postgresql/data  # Persist data across restarts
```

**What it stores:** Paper metadata — arxiv_id, title, abstract, authors, publication date, PDF URL, parsed text, sections.

**Why PostgreSQL:** Structured relational data. Good for: "Get all papers published after January 2024 in the cs.AI category."

### Service 3: opensearch (OpenSearch 2.19)

```yaml
opensearch:
  image: opensearchproject/opensearch:2.19.0
  environment:
    - discovery.type=single-node           # Single server (not a cluster)
    - OPENSEARCH_JAVA_OPTS=-Xms512m -Xmx512m  # 512MB Java heap
    - DISABLE_SECURITY_PLUGIN=true         # No auth (development only!)
  ports:
    - "9200:9200"    # REST API
    - "9600:9600"    # Performance analyzer
```

**What it stores:** Paper chunks with their embeddings (1024-dimension vectors). Supports BM25 keyword search AND kNN (k-Nearest Neighbor) vector search.

**Why OpenSearch (not PostgreSQL for search):** Specialized search engine optimized for full-text search with relevance scoring. PostgreSQL can do search but OpenSearch is 100x better at it.

### Service 4: opensearch-dashboards

```yaml
opensearch-dashboards:
  image: opensearchproject/opensearch-dashboards:2.19.0
  ports:
    - "5601:5601"    # Web UI
```

**What it does:** A web interface to visually browse your OpenSearch indexes, run queries, see document counts.

### Service 5: airflow (Apache Airflow 3.0)

```yaml
airflow:
  build:
    context: ./airflow       # Build from airflow/Dockerfile
  volumes:
    - ./airflow/dags:/opt/airflow/dags  # Mount DAG files
    - ./src:/opt/airflow/src            # Mount source code (DAGs use it)
  ports:
    - "8080:8080"            # Web UI
```

**What it does:** Runs automated workflows (DAGs). Every weekday at 6 AM UTC, it runs the paper ingestion pipeline. Like a cron job but with a web UI, retry logic, dependency management.

### Service 6: ollama (Local LLM)

```yaml
ollama:
  image: ollama/ollama:0.11.2
  ports:
    - "11434:11434"          # REST API
  volumes:
    - ollama_data:/root/.ollama   # Persist downloaded models
```

**What it does:** Runs AI language models locally. No API key needed, no data sent to cloud. The default model is `llama3.2:1b` (1 billion parameters — small and fast for development).

**Why local LLM:** Privacy (your research stays local), cost (no API fees), no rate limits.

### Service 7: redis

```yaml
redis:
  image: redis:7-alpine
  command: redis-server --appendonly yes --maxmemory 256mb --maxmemory-policy allkeys-lru
  ports:
    - "6379:6379"
```

**What it stores:** Cached RAG responses as JSON. Key = SHA256 hash of request. TTL = 6 hours.

**`--appendonly yes`:** Persist cache to disk so it survives restarts.

**`--maxmemory 256mb --maxmemory-policy allkeys-lru`:** Maximum 256MB. When full, remove least-recently-used items.

### Services 8-13: Langfuse Stack

Langfuse needs 5 services to run:

| Service | Purpose |
|---------|---------|
| `langfuse-web` | Web dashboard (port 3001) |
| `langfuse-worker` | Background processing |
| `langfuse-postgres` | Langfuse's own database (port 5433) |
| `langfuse-redis` | Langfuse's own cache (port 6380) |
| `langfuse-minio` | Object storage for event data (like S3) |
| `clickhouse` | Analytics database for traces (port 8123) |

**Why so many?** Langfuse is a complex observability platform. It uses ClickHouse for time-series analytics (fast for millions of trace records) and MinIO to store raw event payloads.

### Networks and Volumes

```yaml
networks:
  rag-network:
    driver: bridge   # All containers share this virtual network
                     # They can reach each other by service name
                     # (e.g., "postgres" instead of "localhost:5432")

volumes:
  postgres_data:     # Named volumes persist data even after "docker compose down"
  opensearch_data:   # To delete data: "docker compose down --volumes"
  ollama_data:
  redis_data:
  ...
```

---

## 6. CONFIGURATION (src/config.py) — EVERY SETTING EXPLAINED

The config file uses **Pydantic Settings** — a library that reads environment variables and validates them. Each setting class maps to a prefix in the `.env` file.

### How It Works

```python
class ArxivSettings(BaseConfigSettings):
    model_config = SettingsConfigDict(
        env_prefix="ARXIV__",   # All settings start with ARXIV__
    )
    base_url: str = "https://export.arxiv.org/api/query"  # Default value
    max_results: int = 15       # Fetch max 15 papers per run
    rate_limit_delay: float = 3.0  # Wait 3 seconds between API calls
```

**In `.env` file:**
```
ARXIV__MAX_RESULTS=25          # Override to fetch 25 papers
ARXIV__RATE_LIMIT_DELAY=5.0   # Slower for rate limiting
```

### ArxivSettings — arXiv API Configuration

| Setting | Default | Explanation |
|---------|---------|-------------|
| `base_url` | arXiv API URL | Where to fetch paper metadata |
| `pdf_cache_dir` | `./data/arxiv_pdfs` | Where to temporarily store downloaded PDFs |
| `rate_limit_delay` | 3.0 seconds | Pause between downloads (arXiv rate limit) |
| `max_results` | 15 | Papers fetched per Airflow run |
| `search_category` | `cs.AI` | Only fetch Computer Science / AI papers |
| `max_concurrent_downloads` | 5 | Download up to 5 PDFs at once |
| `max_concurrent_parsing` | 1 | Parse one PDF at a time (CPU-intensive) |

### ChunkingSettings — Text Splitting Configuration

| Setting | Default | Explanation |
|---------|---------|-------------|
| `chunk_size` | 600 words | Each chunk is 600 words |
| `overlap_size` | 100 words | Adjacent chunks share 100 words |
| `min_chunk_size` | 100 words | Ignore tiny chunks |
| `section_based` | True | Prefer section-based over word-based chunking |

**Why 600 words?** Large enough to contain a complete thought. Small enough that the LLM can fit many chunks in its context window. Too large = fewer relevant chunks. Too small = chunks lose context.

**Why 100-word overlap?** When a sentence is split across chunks, each chunk still has enough context to understand it. Prevents losing information at boundaries.

### OpenSearchSettings — Search Engine Configuration

| Setting | Default | Explanation |
|---------|---------|-------------|
| `host` | `http://localhost:9200` | OpenSearch REST API URL |
| `index_name` | `arxiv-papers` | Base name for indexes |
| `chunk_index_suffix` | `chunks` | Full index: `arxiv-papers-chunks` |
| `vector_dimension` | 1024 | Jina embeddings are 1024 numbers |
| `vector_space_type` | `cosinesimil` | Similarity metric (cosine = angle between vectors) |
| `rrf_pipeline_name` | `hybrid-rrf-pipeline` | Name of the RRF fusion pipeline |

### Settings — Main Application Configuration

| Setting | Default | Explanation |
|---------|---------|-------------|
| `postgres_database_url` | `postgresql://rag_user:...` | Full database connection string |
| `ollama_host` | `http://localhost:11434` | Where Ollama runs |
| `ollama_model` | `llama3.2:1b` | Which AI model to use |
| `jina_api_key` | `""` | Jina AI API key (free tier available) |

### `get_settings()` Function (Line 196-197)

```python
def get_settings() -> Settings:
    return Settings()
```

**Why a function instead of a global?** Each call creates a fresh `Settings()` instance, reading from environment. This makes testing easy — you can set different env vars for tests. Also, FastAPI uses dependency injection with this pattern.

---

## 7. MAIN APPLICATION (src/main.py) — LINE BY LINE

```python
# Lines 1-18: Imports
import logging          # Python's built-in logging system
import os              # Access environment variables
from contextlib import asynccontextmanager  # For the lifespan pattern

import uvicorn         # ASGI server (runs FastAPI efficiently with async)
from fastapi import FastAPI  # The web framework
from src.config import get_settings
from src.db.factory import make_database
# ... more imports for each service
```

**What is uvicorn?** An ASGI (Asynchronous Server Gateway Interface) server. It's the engine that receives HTTP requests and passes them to FastAPI. Like how Apache/Nginx is to Django.

### Lines 21-25: Logging Setup

```python
logging.basicConfig(
    level=logging.INFO,                                     # Show INFO and above
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    # Output: "2024-01-15 10:30:00 - src.main - INFO - Starting RAG API..."
)
logger = logging.getLogger(__name__)  # Logger for this specific file
```

**Log levels (low to high):** DEBUG < INFO < WARNING < ERROR < CRITICAL

Setting `level=INFO` means DEBUG messages are hidden (too verbose), but INFO/WARNING/ERROR/CRITICAL are shown.

### Lines 28-103: The Lifespan Context Manager

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- STARTUP CODE (runs before first request) ---
    settings = get_settings()
    app.state.settings = settings     # Store on app.state so endpoints can access
    
    database = make_database()
    app.state.database = database     # Create DB connection pool
    
    opensearch_client = make_opensearch_client()
    app.state.opensearch_client = opensearch_client
    
    if opensearch_client.health_check():
        setup_results = opensearch_client.setup_indices(force=False)
        # Creates index if it doesn't exist (force=False means don't recreate)
    
    # Initialize ALL services and store them on app.state
    app.state.arxiv_client = make_arxiv_client()
    app.state.pdf_parser = make_pdf_parser_service()
    app.state.embeddings_service = make_embeddings_service()
    app.state.ollama_client = make_ollama_client()
    app.state.langfuse_tracer = make_langfuse_tracer()
    app.state.cache_client = make_cache_client(settings)
    
    # Telegram bot (only if TELEGRAM__BOT_TOKEN is set)
    telegram_service = make_telegram_service(...)
    if telegram_service:
        await telegram_service.start()  # async: non-blocking start
    
    yield  # ← THIS IS THE "WHILE RUNNING" POINT
           # The app serves requests between yield and the code below
    
    # --- SHUTDOWN CODE (runs when app stops) ---
    if hasattr(app.state, "telegram_service"):
        await telegram_service.stop()
    
    database.teardown()  # Close all database connections
```

**Why `asynccontextmanager`?** This pattern (called lifespan in FastAPI) ensures services are started BEFORE requests arrive and cleaned up AFTER the last request. The `yield` is where the app lives. Code before yield = startup. Code after yield = shutdown.

**Why `app.state`?** FastAPI provides `app.state` as a shared storage. Services stored here are accessible from endpoints via dependency injection.

### Lines 106-111: Create FastAPI App

```python
app = FastAPI(
    title="arXiv Paper Curator API",
    description="Personal arXiv CS.AI paper curator with RAG capabilities",
    version=os.getenv("APP_VERSION", "0.1.0"),
    lifespan=lifespan,        # Connect our startup/shutdown logic
)
```

**What FastAPI does:** Automatically creates:
- Interactive API documentation at `http://localhost:8000/docs`
- OpenAPI schema at `http://localhost:8000/openapi.json`
- Request/response validation using your Pydantic schemas

### Lines 113-118: Register Routes

```python
app.include_router(ping.router, prefix="/api/v1")
# → Adds: GET /api/v1/health

app.include_router(hybrid_search.router, prefix="/api/v1")
# → Adds: POST /api/v1/hybrid-search/

app.include_router(ask_router, prefix="/api/v1")
# → Adds: POST /api/v1/ask

app.include_router(stream_router, prefix="/api/v1")
# → Adds: POST /api/v1/stream

app.include_router(agentic_ask.router)
# → Adds: POST /agentic-ask (note: no /api/v1 prefix)
```

**Why `prefix="/api/v1"`?** Versioning. If you change the API in the future, you can add `/api/v2` while keeping v1 working for existing users.

---

## 8. DATA INGESTION PIPELINE (AIRFLOW DAGs)

### How Airflow Works

Apache Airflow is a **workflow scheduler**. You define a DAG (Directed Acyclic Graph) — a sequence of tasks with dependencies. Airflow runs them on a schedule and handles retries.

### The Main DAG (airflow/dags/arxiv_paper_ingestion.py)

```python
dag = DAG(
    "arxiv_paper_ingestion",
    schedule="0 6 * * 1-5",    # Cron: minute=0, hour=6, day=*, month=*, weekday=1-5
                                # = Every weekday at 6 AM UTC
    max_active_runs=1,          # Only one run at a time (no parallel runs)
    catchup=False,              # Don't run missed dates from the past
)
```

**Cron syntax:** `0 6 * * 1-5` means:
- `0` → at minute 0 (top of the hour)
- `6` → at 6 AM
- `*` → every day of month
- `*` → every month
- `1-5` → Monday through Friday

### Task Pipeline (Sequential)

```
setup_task → fetch_task → index_hybrid_task → report_task → cleanup_task
```

Each `>>` means "this task must complete before the next one starts."

**setup_task (setup.py):** Validates environment — are all environment variables set? Is OpenSearch accessible?

**fetch_task (fetching.py):** 
1. Calls arXiv API: `https://export.arxiv.org/api/query?search_query=cat:cs.AI&max_results=15`
2. Parses XML response (arXiv returns Atom/XML format)
3. For each paper: downloads PDF if not already downloaded
4. Runs Docling PDF parser to extract text and sections
5. Saves paper record to PostgreSQL

**index_hybrid_task (indexing.py):**
1. Fetches all papers from PostgreSQL not yet indexed
2. Runs TextChunker to split each paper into 600-word chunks
3. For each chunk: calls Jina AI API to get 1024-dim embedding
4. Bulk indexes all chunks to OpenSearch with their embeddings

**report_task (reporting.py):**
1. Counts papers processed today
2. Counts total papers in database
3. Counts total chunks in OpenSearch
4. Logs a daily summary report

**cleanup_task (BashOperator):**
```bash
find /tmp -name "*.pdf" -type f -mtime +30 -delete
# Delete PDF files older than 30 days from /tmp
```

---

## 9. SEARCH SYSTEM (OPENSEARCH) — BM25 AND HYBRID

### What Is BM25?

BM25 (Best Match 25) is a ranking algorithm used by search engines. It answers: "How relevant is this document to this query?"

**The formula considers:**
1. **Term Frequency (TF):** How often does the search term appear in the document? More occurrences = more relevant. But with diminishing returns (100 occurrences isn't 10x better than 10).
2. **Inverse Document Frequency (IDF):** How rare is the term across all documents? Rare terms are more informative. "the" appears everywhere — low IDF. "transformer" is more specific — higher IDF.
3. **Document Length Normalization:** Short documents that contain the term are ranked higher than long documents with the same number of occurrences.

### QueryBuilder (src/services/opensearch/query_builder.py) — How Queries Are Built

```python
def _build_text_query(self) -> Dict[str, Any]:
    return {
        "multi_match": {
            "query": self.query,              # The search text
            "fields": ["chunk_text^3",        # chunk_text score multiplied by 3
                       "title^2",             # title score multiplied by 2
                       "abstract^1"],         # abstract score multiplied by 1
            "type": "best_fields",            # Use highest-scoring field
            "operator": "or",                 # Match ANY of the query terms
            "fuzziness": "AUTO",              # Allow spelling mistakes (1-2 chars)
            "prefix_length": 2,              # First 2 chars must match exactly
        }
    }
```

**Field boosting (`^3`, `^2`, `^1`):** A match in `chunk_text` is 3x more valuable than a match in `abstract`. If your query word appears in the actual paper text, it's more relevant than just in the abstract.

**`type: best_fields`:** If a document matches multiple fields, use the score from the highest-scoring field (not the sum). Good for when the same term appears in both title and abstract — we don't want to double-count.

**`fuzziness: AUTO`:** For short words (1-2 chars), no fuzzy matching. For medium words (3-5 chars), allow 1 typo. For long words (6+ chars), allow 2 typos. "transfomrer" still matches "transformer".

### Hybrid Search — Combining BM25 and Vector Search

**The problem with BM25 alone:**
- Query: "attention mechanism in neural networks"
- Document: "self-attention heads compute dot products of queries and keys"
- BM25 score: LOW (none of the query words exactly match the document)
- But the document IS relevant!

**The problem with vector search alone:**
- Query: "BERT paper 2018"
- Document: "BERT: Pre-training of Deep Bidirectional Transformers (2018)"
- Vector score: OK but not great (specific date and acronym don't embed well)
- BM25 score: HIGH (exact keyword match)

**Solution — Hybrid with RRF:**

Hybrid search runs BOTH queries and merges results using Reciprocal Rank Fusion (RRF):

```python
hybrid_query = {
    "hybrid": {
        "queries": [
            bm25_query,                              # Keyword search result
            {"knn": {"embedding": {                  # Vector search result
                "vector": query_embedding,           # 1024-dim query vector
                "k": size * 2                        # Get 2x results for better recall
            }}}
        ]
    }
}

response = self.client.search(
    index=self.index_name,
    body=search_body,
    params={"search_pipeline": "hybrid-rrf-pipeline"}  # Apply RRF fusion
)
```

**RRF Formula:** `score = sum(1 / (rank + 60))` for each list.
- If a document is rank 1 in both lists: `1/(1+60) + 1/(1+60) = 0.0328`
- If a document is rank 1 in BM25 but rank 100 in vector: `1/(1+60) + 1/(100+60) = 0.0228`
- Documents appearing in BOTH lists with high ranks get the best final scores

### search_unified() — The Master Search Method

```python
def search_unified(
    self,
    query: str,
    query_embedding: Optional[List[float]] = None,  # If None, BM25 only
    size: int = 10,           # Return top 10 results
    use_hybrid: bool = True,  # Whether to use vector search
    min_score: float = 0.0,   # Filter out low-score results
) -> Dict[str, Any]:
    
    if not query_embedding or not use_hybrid:
        return self._search_bm25_only(...)   # Fall back to BM25
    
    return self._search_hybrid_native(...)   # Use hybrid
```

This is the Swiss Army knife of search. One method handles all cases: BM25 only, vector only (via `search_chunks_vector()`), or hybrid.

---

## 10. TEXT CHUNKING (src/services/indexing/text_chunker.py)

### Why Chunk?

Papers are typically 5,000-20,000 words. An LLM context window can hold maybe 2,000-4,000 words. If you feed an entire paper to the LLM, it won't fit. Even if it fits, the LLM can't focus on what's relevant.

**Solution:** Split papers into smaller, semantically meaningful pieces. Search for the most relevant chunks, not the whole paper.

### Section-Based vs Word-Based Chunking

The `chunk_paper()` method uses a hierarchy:

```
1. Try section-based chunking (preferred)
   ↓ If sections exist AND work correctly
   
2. Fall back to word-based chunking
   ↓ If no sections or section parsing fails
```

**Section-based chunking strategy:**
```
For each section in the paper:
  
  If section < 100 words (tiny):
    → Collect it, combine with adjacent tiny sections
  
  If section is 100-800 words (ideal):
    → Use as single chunk: title + abstract header + section content
  
  If section > 800 words (too large):
    → Split with traditional word-based chunking
    → Each sub-chunk gets: title + abstract header + section excerpt
```

**Why keep title + abstract in every chunk?**

When OpenSearch searches chunk text, it needs context. A chunk about "Experiments show 94.5% accuracy" is meaningless without knowing it's about BERT. Adding the title and abstract header ensures each chunk is self-contained and searchable.

### Word-Based Chunking Algorithm

```python
while current_position < len(words):
    chunk_start = current_position
    chunk_end = min(current_position + chunk_size, len(words))  # 600 words
    
    chunk_words = words[chunk_start:chunk_end]
    chunks.append(TextChunk(text=" ".join(chunk_words), ...))
    
    current_position += chunk_size - overlap_size  # Move forward by 500 words
    # (600 chunk - 100 overlap = 500 words forward)
    # So chunks overlap: words 0-599, 500-1099, 1000-1599, ...
```

**Visual example:**
```
Paper words: [0   1   2 ... 499 500 501 ... 599 600 601 ... 1099 1100...]
Chunk 1:     [0 ─────────────────────────── 599]
Chunk 2:                 [500 ──────────────────── 1099]
Chunk 3:                               [1000 ─────────── 1599]
                         ↑overlap↑     ↑overlap↑
```

Words 500-599 appear in BOTH chunk 1 AND chunk 2. This ensures a sentence that's near the boundary is captured completely in at least one chunk.

---

## 11. LLM INTEGRATION (OLLAMA)

### What Is Ollama?

Ollama is a tool that lets you run AI language models locally (on your own computer). It downloads models from the internet and serves them via a REST API, similar to OpenAI's API but running locally.

**Why local?**
- No API costs
- No data sent to cloud (privacy)
- No internet required after model download
- No rate limits

### OllamaClient (src/services/ollama/client.py)

```python
class OllamaClient:
    def __init__(self, settings: Settings):
        self.base_url = settings.ollama_host    # "http://localhost:11434"
        self.timeout = httpx.Timeout(float(settings.ollama_timeout))  # 300 seconds
        self.prompt_builder = RAGPromptBuilder()
```

**`httpx`:** Modern async HTTP client for Python. Alternative to `requests` but supports `async/await`.

### The generate() Method — Line by Line

```python
async def generate(self, model: str, prompt: str, stream: bool = False):
    async with httpx.AsyncClient(timeout=self.timeout) as client:
        data = {
            "model": model,      # "llama3.2:1b"
            "prompt": prompt,    # The full prompt with context + question
            "stream": stream,    # False = wait for complete response
        }
        
        response = await client.post(
            f"{self.base_url}/api/generate",  # Ollama's generate endpoint
            json=data
        )
        
        if response.status_code == 200:
            result = response.json()
            
            # Parse usage statistics
            usage_metadata = {
                "prompt_tokens": result.get("prompt_eval_count", 0),
                "completion_tokens": result.get("eval_count", 0),
                "latency_ms": round(result["total_duration"] / 1_000_000, 2)
                # Ollama reports duration in nanoseconds, convert to ms
            }
            
            result["usage_metadata"] = usage_metadata
            return result
```

**Why `async`?** While waiting for the LLM to generate (which can take 5-30 seconds), `async` allows the server to handle other requests. Without async, one slow LLM call would block the entire server.

### generate_rag_answer() — The RAG Prompt Flow

```python
async def generate_rag_answer(self, query, chunks, model):
    # Build prompt: "Here are papers [chunks]. Answer: [query]"
    prompt = self.prompt_builder.create_rag_prompt(query, chunks)
    
    response = await self.generate(
        model=model,
        prompt=prompt,
        temperature=0.7,    # Creativity level (0=deterministic, 1=creative)
        top_p=0.9,         # Nucleus sampling (consider top 90% probable tokens)
    )
    
    # Extract answer text
    answer_text = response["response"]
    
    # Build source list from chunk metadata
    sources = []
    for chunk in chunks:
        arxiv_id = chunk.get("arxiv_id")
        if arxiv_id:
            sources.append(f"https://arxiv.org/pdf/{arxiv_id}.pdf")
    
    return {"answer": answer_text, "sources": sources, ...}
```

**Temperature:** Controls randomness. 
- 0.0 = Always picks the most likely next word (deterministic, good for grading/classification)
- 0.7 = Some creativity (good for answering questions)
- 1.0 = Very creative/random (good for creative writing)

### Streaming (generate_rag_answer_stream)

Instead of waiting for the complete response (5-30 seconds of silence), streaming sends words as they're generated:

```python
async for chunk in self.generate_stream(model=model, prompt=prompt):
    if chunk.get("response"):
        text_chunk = chunk["response"]  # One or a few words
        yield chunk                      # Send immediately to client
    
    if chunk.get("done", False):
        break
```

The client (browser/Gradio) receives `{"chunk": "Transform"}`, `{"chunk": "ers"}`, `{"chunk": " use"}`, etc., and displays them in real-time.

---

## 12. RAG ENDPOINTS (src/routers/ask.py)

### POST /ask — Standard RAG Endpoint

```
User → POST /ask {query: "...", top_k: 5, use_hybrid: true}
         ↓
      Check Redis cache (exact match)
         ↓ (cache miss)
      Generate query embedding (Jina AI)
         ↓
      OpenSearch hybrid search → top 5 chunks
         ↓
      Build RAG prompt (chunks + query)
         ↓
      Ollama generates answer
         ↓
      Store in Redis cache
         ↓
      Return {answer: "...", sources: [...], chunks_used: 5}
```

### Key Code Section — Chunk Preparation

```python
async def _prepare_chunks_and_sources(request, opensearch_client, embeddings_service):
    
    # Step 1: Get embedding for the query (if hybrid search requested)
    query_embedding = None
    if request.use_hybrid:
        query_embedding = await embeddings_service.embed_query(request.query)
    
    # Step 2: Search OpenSearch
    search_results = opensearch_client.search_unified(
        query=request.query,
        query_embedding=query_embedding,    # None = BM25 only
        size=request.top_k,                 # How many chunks to get
        use_hybrid=request.use_hybrid,
    )
    
    # Step 3: Extract chunk text and build source URLs
    chunks = []
    sources_set = set()   # set() prevents duplicate URLs
    
    for hit in search_results.get("hits", []):
        chunks.append({
            "arxiv_id": hit.get("arxiv_id", ""),
            "chunk_text": hit.get("chunk_text", ""),  # The actual paper text
        })
        
        arxiv_id = hit.get("arxiv_id", "")
        if arxiv_id:
            # Build PDF URL: "2401.12345v1" → "2401.12345"
            arxiv_id_clean = arxiv_id.split("v")[0]
            sources_set.add(f"https://arxiv.org/pdf/{arxiv_id_clean}.pdf")
    
    return chunks, list(sources_set), arxiv_ids
```

### POST /stream — Server-Sent Events

```python
@stream_router.post("/stream")
async def ask_question_stream(request):
    async def generate_stream():
        # ... same as /ask but yields chunks as they come
        
        async for chunk in ollama_client.generate_rag_answer_stream(...):
            if chunk.get("response"):
                yield f"data: {json.dumps({'chunk': chunk['response']})}\n\n"
                # Format: "data: {"chunk": "Transform"}\n\n"
                # The \n\n is required by Server-Sent Events spec
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/plain",   # SSE uses text/event-stream but this works
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
    )
```

**Server-Sent Events (SSE):** A web standard for server-to-client streaming. Each event is prefixed with `data: ` and terminated with `\n\n`. The browser's `EventSource` API handles this automatically.

---

## 13. CACHING SYSTEM (REDIS)

### Why Cache?

**Without cache:**
- Every question → Jina AI API call (~100ms) + OpenSearch search (~50ms) + Ollama LLM (~5-30 seconds)
- 100 identical questions = 100 LLM calls = 5-30 minutes of compute

**With cache:**
- First question → normal flow (~30 seconds)
- Same question again → Redis lookup (~1ms)
- 100 identical questions = 1 LLM call + 99 cache hits = ~30 seconds total (99% faster)

### How Cache Keys Work

```python
def _generate_cache_key(self, request: AskRequest) -> str:
    key_data = {
        "query": request.query,        # The exact question
        "model": request.model,        # "llama3.2:1b"
        "top_k": request.top_k,        # 5
        "use_hybrid": request.use_hybrid,  # true/false
        "categories": sorted(request.categories or []),  # sorted for consistency
    }
    
    # Convert to JSON string, sorted keys for consistency
    key_string = json.dumps(key_data, sort_keys=True)
    
    # Take SHA-256 hash, use first 16 characters
    key_hash = hashlib.sha256(key_string.encode()).hexdigest()[:16]
    
    return f"exact_cache:{key_hash}"
    # Example: "exact_cache:a1b2c3d4e5f6a7b8"
```

**Why hash instead of storing the full query as key?**
1. Redis keys should be short and consistent in length
2. Long queries could exceed key size limits
3. Hashing is O(1) regardless of query length

**Why `sorted(categories)`?** So that `["cs.AI", "cs.LG"]` and `["cs.LG", "cs.AI"]` produce the same cache key (order shouldn't matter).

### Cache Flow in /ask

```python
# Check cache first
cached_response = await cache_client.find_cached_response(request)
if cached_response:
    return cached_response   # Instant return, no API calls

# ... do full RAG pipeline ...

# Store result
await cache_client.store_response(request, response)
# Stored with TTL of 6 hours (REDIS__TTL_HOURS=6)
```

**TTL (Time-To-Live):** After 6 hours, cached answers expire. This is because:
1. Papers are indexed daily — answers might become outdated
2. Don't want to store stale responses forever
3. Memory management (Redis has 256MB limit)

---

## 14. MONITORING (LANGFUSE)

### What Is Langfuse?

Langfuse is an open-source LLM observability platform. It records:
- Every prompt sent to the LLM
- Every response received
- Token counts (for cost estimation)
- Latency at each step
- Custom metadata (user ID, search mode, etc.)

### Tracing Hierarchy

```
Trace (one user request)
  ├── Span: embedding (Jina API call for query)
  ├── Span: search (OpenSearch query)
  ├── Span: prompt_construction (building the prompt string)
  └── Span: generation (Ollama LLM call)
        └── Observation: token counts, latency
```

**Trace:** The top-level container for one user request (one question)
**Span:** A sub-operation within a trace (each step has its own span)

### LangfuseTracer — How It Works

```python
class LangfuseTracer:
    def create_span(self, trace, name, input_data, metadata):
        span = trace.span(
            name=name,          # "document_retrieval"
            input=input_data,   # {"query": "...", "top_k": 5}
            metadata=metadata,  # {"node": "retrieve", "attempt": 1}
        )
        return span
    
    def end_span(self, span, output, metadata):
        span.end(
            output=output,      # {"documents_found": 3, "status": "success"}
            metadata=metadata,  # {"execution_time_ms": 150}
        )
```

### RAGTracer — High-Level Wrapper

`src/services/langfuse/tracer.py` provides convenience methods:

```python
class RAGTracer:
    def trace_request(self, user_id, query):
        return self.tracer.start_trace(name="rag_request", ...)
    
    def trace_embedding(self, trace, query):
        return self.tracer.create_span(trace, "embedding", ...)
    
    def trace_search(self, trace, query, top_k):
        return self.tracer.create_span(trace, "search", ...)
    
    def trace_generation(self, trace, model, prompt):
        return self.tracer.create_span(trace, "generation", ...)
```

Usage in `/ask` endpoint:
```python
rag_tracer = RAGTracer(langfuse_tracer)
with rag_tracer.trace_request("api_user", request.query) as trace:
    with rag_tracer.trace_embedding(trace, request.query) as span:
        embedding = await embeddings_service.embed_query(request.query)
    
    with rag_tracer.trace_search(trace, request.query, request.top_k) as span:
        results = opensearch_client.search_unified(...)
    
    # ... etc.
```

**Dashboard:** Visit `http://localhost:3001` (login: admin@example.com / admin123) to see all traces.

---

## 15. AGENTIC RAG — THE INTELLIGENCE LAYER (WEEK 7)

### What Is LangGraph?

LangGraph is a library for building multi-step AI workflows as graphs. Instead of a linear pipeline (step 1 → step 2 → step 3), you can have:
- Conditional edges (if condition: go to node A, else go to node B)
- Loops (go back to a previous node)
- Parallel execution

### The Agent State (src/services/agents/state.py)

State is the data that flows through the graph. Every node can read and write to it:

```python
class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    # The conversation history. "add_messages" reducer APPENDS new messages
    # instead of replacing the list (crucial for multi-step flow)
    
    original_query: Optional[str]   # The user's original question
    rewritten_query: Optional[str]  # If the agent rewrote the query
    retrieval_attempts: int         # How many times we've tried to retrieve
    
    guardrail_result: Optional[GuardrailScoring]  # Score (0-100) + reason
    routing_decision: Optional[str]  # "generate_answer" or "rewrite_query"
    
    sources: Optional[Dict]         # Raw tool output (documents retrieved)
    relevant_sources: List[SourceItem]  # Filtered, relevant sources
    grading_results: List[GradingResult]  # Per-document relevance grades
    
    metadata: Dict[str, Any]        # Extra info: timing, model name, etc.
```

**`Annotated[list[AnyMessage], add_messages]`:** The `add_messages` is a "reducer." When two nodes both add messages to state, `add_messages` appends them into a single list instead of overwriting. This is how conversation history accumulates.

### The Graph Structure (_build_graph in agentic_rag.py)

```python
workflow = StateGraph(AgentState, context_schema=Context)
# AgentState = what data flows between nodes
# Context = shared dependencies (services like ollama, opensearch, etc.)

# Add nodes (each is an async function)
workflow.add_node("guardrail", ainvoke_guardrail_step)
workflow.add_node("out_of_scope", ainvoke_out_of_scope_step)
workflow.add_node("retrieve", ainvoke_retrieve_step)
workflow.add_node("tool_retrieve", ToolNode(tools))   # Built-in LangGraph tool executor
workflow.add_node("grade_documents", ainvoke_grade_documents_step)
workflow.add_node("rewrite_query", ainvoke_rewrite_query_step)
workflow.add_node("generate_answer", ainvoke_generate_answer_step)

# Add edges (connections between nodes)
workflow.add_edge(START, "guardrail")          # Always start with guardrail

workflow.add_conditional_edges(                # After guardrail:
    "guardrail",
    continue_after_guardrail,                  # Run this function to decide
    {
        "continue": "retrieve",                # Score >= threshold → retrieve
        "out_of_scope": "out_of_scope",       # Score < threshold → reject
    }
)

workflow.add_edge("out_of_scope", END)         # Done after rejection

workflow.add_conditional_edges(
    "retrieve",
    tools_condition,                           # LangGraph built-in: is there a tool call?
    {
        "tools": "tool_retrieve",              # Yes → execute tool
        END: END,                              # No → end (max retries reached)
    }
)

workflow.add_edge("tool_retrieve", "grade_documents")  # After retrieval → grade

workflow.add_conditional_edges(
    "grade_documents",
    lambda state: state.get("routing_decision", "generate_answer"),
    {
        "generate_answer": "generate_answer",  # Relevant → answer
        "rewrite_query": "rewrite_query",      # Not relevant → rewrite
    }
)

workflow.add_edge("rewrite_query", "retrieve")  # After rewrite → try again
workflow.add_edge("generate_answer", END)        # After answer → done

compiled_graph = workflow.compile()
```

### Visual Flow of the Agent

```
START
  │
  ▼
[GUARDRAIL]  ──── LLM scores 0-100: "Is this about CS/AI/ML papers?"
  │
  ├── score >= 60 ──► [RETRIEVE] ──── Create tool call for OpenSearch search
  │                        │
  │                        ▼ (if max retries hit → END with apology)
  │                   [TOOL_RETRIEVE] ──── Execute search, get documents
  │                        │
  │                        ▼
  │                 [GRADE_DOCUMENTS] ──── LLM: "Are these docs relevant?"
  │                        │
  │                   ┌────┴────┐
  │              yes  ▼         ▼  no
  │         [GENERATE]    [REWRITE_QUERY] ──── LLM rewrites query
  │              │                │
  │              ▼                └──► back to [RETRIEVE] (loop)
  │             END
  │
  └── score < 60 ──► [OUT_OF_SCOPE] ──── Polite rejection message
                          │
                         END
```

### Node 1: guardrail_node.py — Domain Validation

```python
async def ainvoke_guardrail_step(state, runtime):
    query = get_latest_query(state["messages"])
    
    # Prompt the LLM to score the query
    guardrail_prompt = GUARDRAIL_PROMPT.format(question=query)
    # Prompt: "Score 0-100 whether this is about CS/AI/ML research..."
    
    llm = runtime.context.ollama_client.get_langchain_model(
        model=runtime.context.model_name,
        temperature=0.0,  # Deterministic — we want consistent scoring
    )
    
    # structured_output forces the LLM to return JSON: {"score": 85, "reason": "..."}
    structured_llm = llm.with_structured_output(GuardrailScoring)
    response = await structured_llm.ainvoke(guardrail_prompt)
    
    return {"guardrail_result": response}  # Updates the state
```

**`with_structured_output(GuardrailScoring)`:** Forces the LLM to return JSON matching the Pydantic model `GuardrailScoring`. LangChain handles the prompt formatting and JSON parsing automatically.

**`temperature=0.0`:** For the guardrail, we want the same score every time for the same query. Randomness would make the system unpredictable.

### Node 2: retrieve_node.py — Document Retrieval Initiation

```python
async def ainvoke_retrieve_step(state, runtime):
    messages = state["messages"]
    question = get_latest_query(messages)
    current_attempts = state.get("retrieval_attempts", 0)
    max_attempts = runtime.context.max_retrieval_attempts  # Default: 2
    
    # If too many retries, give up
    if current_attempts >= max_attempts:
        return {"messages": [AIMessage(content="I couldn't find relevant papers...")]}
    
    # Create a TOOL CALL — not the retrieval itself, just the intention
    # LangGraph's ToolNode will execute this
    return {
        "retrieval_attempts": current_attempts + 1,
        "messages": [
            AIMessage(
                content="",
                tool_calls=[{
                    "id": f"retrieve_{current_attempts + 1}",
                    "name": "retrieve_papers",    # Name of the registered tool
                    "args": {"query": question},  # Arguments to pass to the tool
                }]
            )
        ]
    }
```

**Why create a tool call instead of directly retrieving?**

This is the LangGraph pattern. The `retrieve` node creates an "intention" to call a tool. LangGraph's built-in `ToolNode` then executes the actual tool function. This separation allows LangGraph to:
1. Log the tool call in the message history
2. Handle tool execution errors gracefully
3. Support multiple tools (if you add more retrieval tools later)

### Node 3: grade_documents_node.py — Relevance Assessment

```python
async def ainvoke_grade_documents_step(state, runtime):
    question = get_latest_query(state["messages"])
    context = get_latest_context(state["messages"])  # Retrieved documents text
    
    if not context:
        return {"routing_decision": "rewrite_query", "grading_results": []}
    
    # Ask LLM: are these documents relevant?
    grading_prompt = GRADE_DOCUMENTS_PROMPT.format(
        context=context,      # The retrieved document texts
        question=question,    # The user's question
    )
    
    structured_llm = llm.with_structured_output(GradeDocuments)
    # GradeDocuments model: {"binary_score": "yes"/"no", "reasoning": "..."}
    
    grading_response = await structured_llm.ainvoke(grading_prompt)
    is_relevant = grading_response.binary_score == "yes"
    
    route = "generate_answer" if is_relevant else "rewrite_query"
    
    return {
        "routing_decision": route,
        "grading_results": [GradingResult(
            document_id="retrieved_docs",
            is_relevant=is_relevant,
            reasoning=grading_response.reasoning,
        )]
    }
```

**This prevents hallucination.** Without grading, even irrelevant documents would be passed to the answer generator, which might make up facts. By checking first, we ensure only relevant documents generate answers.

### Node 4: rewrite_query_node.py — Query Improvement

```python
async def ainvoke_rewrite_query_step(state, runtime):
    original_question = state.get("original_query")
    
    llm = runtime.context.ollama_client.get_langchain_model(
        temperature=0.3,  # Some creativity for rewriting
    )
    structured_llm = llm.with_structured_output(QueryRewriteOutput)
    # QueryRewriteOutput: {"rewritten_query": "...", "reasoning": "..."}
    
    prompt = REWRITE_PROMPT.format(question=original_question)
    result = await structured_llm.ainvoke(prompt)
    
    rewritten_query = result.rewritten_query.strip()
    
    return {
        "messages": [HumanMessage(content=rewritten_query)],  # New question
        "rewritten_query": rewritten_query,
    }
```

**Example:**
- Original: "How does attention work?" 
- Rewritten: "self-attention mechanism transformer architecture neural network query key value"

The rewritten query has more technical keywords that are more likely to match paper text in OpenSearch.

### Node 5: generate_answer_node.py — Final Answer

```python
async def ainvoke_generate_answer_step(state, runtime):
    question = get_latest_query(state["messages"])
    context = get_latest_context(state["messages"])
    
    if not context:
        context = "No relevant documents found."
    
    answer_prompt = GENERATE_ANSWER_PROMPT.format(
        context=context,      # The relevant paper chunks
        question=question,    # The user's question
    )
    
    llm = runtime.context.ollama_client.get_langchain_model(
        temperature=runtime.context.temperature,  # Default 0.7
    )
    
    response = await llm.ainvoke(answer_prompt)
    answer = response.content
    
    return {"messages": [AIMessage(content=answer)]}
```

### Node 6: out_of_scope_node.py — Polite Rejection

```python
async def ainvoke_out_of_scope_step(state, runtime):
    question = get_latest_query(state["messages"])
    
    response_text = (
        "I apologize, but I can only help with questions about academic research papers "
        "in Computer Science, AI, and Machine Learning from arXiv.\n\n"
        f"Your question: '{question}'\n\n"
        "This appears to be outside my domain. You might want to try:\n"
        "- General-purpose AI assistants for broad knowledge questions\n"
        "..."
    )
    
    return {"messages": [AIMessage(content=response_text)]}
```

**Why not just let the LLM answer?** Without guardrails, the LLM might make up paper references ("As shown in Johnson et al. 2023...") when no such paper exists. Better to reject honestly.

### The Context Pattern (context.py)

```python
class Context:
    """Dependency injection container for agent nodes."""
    ollama_client: OllamaClient
    opensearch_client: OpenSearchClient
    embeddings_client: JinaEmbeddingsClient
    langfuse_tracer: Optional[LangfuseTracer]
    trace: Any
    model_name: str         # "llama3.2:1b"
    temperature: float      # 0.7
    top_k: int              # 5
    max_retrieval_attempts: int  # 2
    guardrail_threshold: int     # 60
```

Instead of each node creating its own service connections, all services are passed through `Context`. This is **dependency injection** — nodes receive what they need, they don't go looking for it. Makes testing easy (inject mock services in tests).

---

## 16. TELEGRAM BOT

### How the Bot Works

```
User sends message on Telegram
         ↓
Telegram servers receive it
         ↓
Bot polls Telegram API: "Any new messages?"
         ↓
python-telegram-bot library receives the update
         ↓
Dispatches to the correct handler:
  /start → _start_command()
  /help  → _help_command()
  /search <keywords> → _search_command()
  Any other text → _handle_question()
```

### The Question Handler (_handle_question)

This essentially runs a mini RAG pipeline:

```python
async def _handle_question(self, update, context):
    query = update.message.text
    await update.message.chat.send_action("typing")  # Show "typing..." indicator
    
    # 1. Check Redis cache
    cached = await self.cache.find_cached_response(ask_request)
    if cached:
        await self._send_answer(update, cached)
        return
    
    # 2. Get query embedding
    query_embedding = await self.embeddings.embed_query(query)
    
    # 3. Hybrid search in OpenSearch
    results = self.opensearch.search_unified(
        query=query, query_embedding=query_embedding,
        size=3, use_hybrid=True  # Only 3 chunks for Telegram (shorter messages)
    )
    
    # 4. Generate answer with Ollama
    prompt = RAGPromptBuilder().create_rag_prompt(query, chunks)
    ollama_response = await self.ollama.generate(model="llama3.2:1b", prompt=prompt)
    answer = ollama_response.get("response", "")
    
    # 5. Store in cache
    await self.cache.store_response(ask_request, response)
    
    # 6. Send formatted response
    await self._send_answer(update, response)
```

### Message Formatting (_send_answer)

```python
async def _send_answer(self, update, response):
    message = f"*Answer:*\n{response.answer}\n"
    
    if response.sources:
        message += "\n*Sources:*\n"
        for idx, source_url in enumerate(response.sources[:5], 1):
            arxiv_id = source_url.split("/")[-1].replace(".pdf", "")
            message += f"{idx}. https://arxiv.org/abs/{arxiv_id}\n"
    
    # Try Markdown formatting (bold, etc.)
    try:
        await update.message.reply_text(message, parse_mode="Markdown")
    except Exception:
        # If Markdown parsing fails (e.g., unmatched asterisks in answer)
        await update.message.reply_text(message)  # Plain text fallback
```

---

## 17. HOW TO RUN THE SYSTEM — STEP BY STEP

### Prerequisites

```bash
# Install Docker Desktop: https://www.docker.com/products/docker-desktop/
# Install UV (Python package manager):
curl -LsSf https://astral.sh/uv/install.sh | sh

# Check installations
docker --version          # Should show Docker version
docker compose version    # Should show Docker Compose version
uv --version              # Should show UV version
python3 --version         # Should be 3.12+
```

### Step 1: Clone and Configure

```bash
cd /path/to/project
cp .env.example .env      # Copy example config

# Open .env and optionally fill in:
# JINA_API_KEY=your_key_here        (needed for Week 4+ embeddings)
# TELEGRAM__BOT_TOKEN=your_token    (needed for Week 7 Telegram bot)
# Leave Langfuse keys empty for now (it self-hosts)
```

### Step 2: Install Python Dependencies

```bash
uv sync
# Creates virtual environment and installs all packages from pyproject.toml
```

### Step 3: Start All Services

```bash
docker compose up --build -d
# --build: Rebuild Docker images (needed first time)
# -d: Run in background (detached mode)

# Watch startup progress:
docker compose logs -f    # -f: follow/stream logs
# Wait for "API ready" message (takes 2-5 minutes)
```

### Step 4: Verify Everything Is Running

```bash
# Check all containers are healthy
docker compose ps
# Should show all containers as "healthy"

# Check the API
curl http://localhost:8000/api/v1/health
# Expected: {"status": "healthy", "services": {...}}

# Visit the API docs
open http://localhost:8000/docs         # Mac
# or: xdg-open http://localhost:8000/docs  # Linux

# Visit other services
open http://localhost:8080    # Airflow (admin/admin123)
open http://localhost:5601    # OpenSearch Dashboards
open http://localhost:3001    # Langfuse (admin@example.com/admin123)
```

### Step 5: Download an AI Model

```bash
# Ollama needs to download the AI model first
docker exec -it rag-ollama ollama pull llama3.2:1b
# This downloads a 1 billion parameter model (~600MB)
# Wait for: "success"
```

### Step 6: Trigger Paper Ingestion

**Option A: Via Airflow UI**
1. Open `http://localhost:8080`
2. Find the `arxiv_paper_ingestion` DAG
3. Click the play button to trigger a manual run
4. Watch the tasks turn green one by one

**Option B: Via Python Script**
```bash
# In Jupyter notebook (Week 2):
uv run jupyter notebook notebooks/week2/week2_arxiv_integration.ipynb
```

### Step 7: Ask a Question

**Via API:**
```bash
curl -X POST http://localhost:8000/api/v1/ask \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How does the attention mechanism work in transformers?",
    "top_k": 5,
    "use_hybrid": true
  }'
```

**Via Gradio UI:**
```bash
uv run python gradio_launcher.py
open http://localhost:7861
# Type your question in the chat interface
```

**Via Agentic RAG:**
```bash
curl -X POST http://localhost:8000/agentic-ask \
  -H "Content-Type: application/json" \
  -d '{"query": "What are the main differences between GPT and BERT?"}'
```

### Step 8: Run Tests

```bash
make test           # Run all tests
make test-cov       # Run tests with coverage report
uv run pytest tests/unit/    # Only unit tests (fast)
uv run pytest tests/api/     # Only API tests
```

---

## 18. WHAT RESULTS YOU GET — EXPECTED OUTPUTS

### /api/v1/health

```json
{
  "status": "healthy",
  "version": "0.1.0",
  "services": {
    "database": "connected",
    "opensearch": "healthy",
    "ollama": "running"
  }
}
```

### /api/v1/ask

```json
{
  "query": "How does BERT work?",
  "answer": "BERT (Bidirectional Encoder Representations from Transformers) works by pre-training a deep bidirectional transformer on large unlabeled text corpora. Unlike previous models that read text left-to-right, BERT reads the entire sequence at once, allowing it to capture context from both directions. It uses two pre-training tasks: Masked Language Modeling (MLM), where random tokens are masked and the model learns to predict them, and Next Sentence Prediction (NSP), where the model learns to predict if one sentence follows another. These pre-trained representations are then fine-tuned for downstream tasks...",
  "sources": [
    "https://arxiv.org/pdf/1810.04805.pdf",
    "https://arxiv.org/pdf/2005.14165.pdf"
  ],
  "chunks_used": 5,
  "search_mode": "hybrid"
}
```

### /agentic-ask

```json
{
  "query": "What is the best way to fine-tune LLMs?",
  "answer": "Based on the retrieved research papers, the best approaches for fine-tuning LLMs include...",
  "sources": [{"arxiv_id": "2305.14314", "title": "LoRA: Low-Rank Adaptation..."}],
  "reasoning_steps": [
    "Validated query scope (score: 87/100)",
    "Retrieved documents (1 attempt(s))",
    "Graded documents (3 relevant)",
    "Generated answer from context"
  ],
  "retrieval_attempts": 1,
  "rewritten_query": null,
  "execution_time": 8.45,
  "guardrail_score": 87
}
```

### What Happens with Out-of-Scope Questions

```bash
curl -X POST http://localhost:8000/agentic-ask \
  -d '{"query": "What is the best pizza recipe?"}'
```

```json
{
  "answer": "I apologize, but I can only help with questions about academic research papers in Computer Science, AI, and Machine Learning from arXiv. Your question: 'What is the best pizza recipe?' appears to be outside my domain...",
  "guardrail_score": 2,
  "reasoning_steps": ["Validated query scope (score: 2/100)"]
}
```

### Airflow Run Results

After a successful DAG run, the logs show:
```
[2024-01-15 06:00:01] setup_environment: Environment validated ✓
[2024-01-15 06:00:05] fetch_daily_papers: Fetching cs.AI papers...
[2024-01-15 06:02:30] fetch_daily_papers: Fetched 15 papers, saved to PostgreSQL
[2024-01-15 06:02:31] index_papers_hybrid: Starting hybrid indexing...
[2024-01-15 06:05:45] index_papers_hybrid: Indexed 147 chunks for 15 papers
[2024-01-15 06:05:46] generate_daily_report:
  Papers processed today: 15
  Total papers in database: 234
  Total chunks in OpenSearch: 2847
  New chunks indexed: 147
[2024-01-15 06:05:47] cleanup_temp_files: Cleanup completed
```

---

## 19. DIFFERENT WAYS TO DO EACH PART (ALTERNATIVES)

### Alternative 1: Different Search Approach

| Approach | This System | Alternative | When to Choose |
|----------|-------------|-------------|----------------|
| Keyword Search | BM25 (OpenSearch) | PostgreSQL full-text search | Very small scale (<10K docs) |
| Vector Search | kNN in OpenSearch | Pinecone, Weaviate, Qdrant | Cloud-native, managed service |
| Hybrid Fusion | RRF (OpenSearch native) | Manual score merging | More control over weights |
| Embedding Provider | Jina AI (1024-dim) | OpenAI ada-002 (1536-dim) | Higher accuracy, needs API key |

### Alternative 2: Different LLM Approaches

| Approach | This System | Alternative |
|----------|-------------|-------------|
| LLM Provider | Ollama (local, llama3.2:1b) | OpenAI GPT-4, Anthropic Claude |
| Model Size | 1B params (fast, less accurate) | 7B, 13B, 70B params |
| Serving | Ollama | vLLM, TGI (Text Generation Inference) |
| Integration | httpx direct calls | LangChain, LlamaIndex |

### Alternative 3: Different Chunking Strategies

| Strategy | This System | Alternative |
|----------|-------------|-------------|
| Section-based | Yes (preferred) | Sentence-based chunking |
| Size | 600 words + 100 overlap | Fixed tokens (512, 1024) |
| Library | Custom implementation | LangChain TextSplitter, LlamaIndex |
| Granularity | Paragraph-level | Sentence-level, page-level |

### Alternative 4: Different Workflow Orchestration

| Tool | This System | Alternative |
|------|-------------|-------------|
| Scheduler | Apache Airflow 3.0 | Prefect, Dagster, Luigi |
| DAG definition | Python code | YAML (in some tools) |
| Monitoring | Airflow UI | Grafana + Prometheus |
| Scaling | Single machine | Kubernetes + Celery |

### Alternative 5: Different Agentic Frameworks

| Framework | This System | Alternative |
|-----------|-------------|-------------|
| Agent Library | LangGraph | AutoGen, CrewAI, Haystack |
| State management | TypedDict | Pydantic BaseModel |
| Routing | Conditional edges | Router chains |
| Tools | Custom + ToolNode | LangChain tools, custom |

### Alternative 6: Different Monitoring Solutions

| Aspect | This System | Alternative |
|--------|-------------|-------------|
| LLM Observability | Langfuse | Weights & Biases, MLflow, Helicone |
| Analytics DB | ClickHouse | PostgreSQL (simpler), BigQuery |
| Caching | Redis exact-match | Semantic caching (find similar queries) |
| Metrics | Langfuse dashboard | Grafana + Prometheus + custom metrics |

---

## 20. COMPARISON TABLES — ALL KEY DIFFERENCES

### Week-by-Week Capabilities

| Feature | W1 | W2 | W3 | W4 | W5 | W6 | W7 |
|---------|----|----|----|----|----|----|-----|
| Infrastructure (Docker) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Database (PostgreSQL) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| arXiv API Ingestion | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| PDF Parsing (Docling) | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| BM25 Keyword Search | ❌ | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Text Chunking | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ | ✅ |
| Vector Embeddings (Jina) | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ | ✅ |
| Hybrid Search (RRF) | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ | ✅ |
| LLM Integration (Ollama) | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ |
| RAG Pipeline (/ask) | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ |
| Streaming (/stream) | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ |
| Gradio Web UI | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ |
| Redis Caching | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ |
| Langfuse Monitoring | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ |
| LangGraph Agent | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| Guardrail Node | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| Document Grading | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| Query Rewriting | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| Telegram Bot | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |

### Search Mode Comparison

| Search Mode | How It Works | Best For | Weakness |
|-------------|-------------|----------|----------|
| BM25 Only | Keyword frequency + inverse doc frequency | Exact terms, specific names | Misses synonyms, semantic meaning |
| Vector Only | Cosine similarity of embeddings | Semantic matching, related concepts | Misses exact term matches |
| Hybrid (RRF) | Both BM25 + kNN, merged with RRF | Best of both worlds | Slower, needs Jina API key |

### Chunking Strategy Comparison

| Strategy | Chunk Size | Overlap | Context | Speed |
|----------|-----------|---------|---------|-------|
| Section-based | Variable (100-800 words) | 0 | Has title+abstract header | Fast |
| Word-based | 600 words fixed | 100 words | Raw text | Fast |
| Sentence-based | Variable | None | Preserves sentences | Medium |
| Token-based | 512/1024 tokens | Configurable | Precise for LLM | Slow |

### Performance Comparison

| Scenario | Time | Why |
|----------|------|-----|
| First question (no cache) | 5-30 seconds | Embedding + Search + LLM generation |
| Same question (cache hit) | < 10ms | Redis O(1) lookup |
| Search only (no LLM) | 100-500ms | Embedding + OpenSearch |
| Agentic RAG (relevant) | 15-60 seconds | Multiple LLM calls for guardrail + grade + generate |
| Agentic RAG (needs rewrite) | 30-90 seconds | Extra retrieve + grade + generate cycle |
| Agentic RAG (out of scope) | 5-15 seconds | Only guardrail + rejection message |

### Services Port Reference

| Service | Port | Purpose | Access |
|---------|------|---------|--------|
| FastAPI | 8000 | Main API + docs | `http://localhost:8000/docs` |
| Airflow | 8080 | Workflow UI | `http://localhost:8080` |
| OpenSearch | 9200 | Search REST API | `http://localhost:9200` |
| OpenSearch Dashboards | 5601 | Search UI | `http://localhost:5601` |
| Ollama | 11434 | LLM REST API | `http://localhost:11434` |
| PostgreSQL | 5432 | Main database | psql connection |
| Redis | 6379 | Cache | redis-cli |
| Langfuse | 3001 | Monitoring UI | `http://localhost:3001` |
| Langfuse Postgres | 5433 | Langfuse's DB | (internal) |
| Langfuse Redis | 6380 | Langfuse's cache | (internal) |
| MinIO | 9090 | Object storage API | `http://localhost:9090` |
| MinIO Console | 9091 | Storage UI | `http://localhost:9091` |
| Gradio | 7861 | Chat UI | `http://localhost:7861` |

---

## 21. CHEAT SHEET — QUICK REFERENCE

### Most Important Commands

```bash
# Start everything
docker compose up --build -d

# Check status
docker compose ps
docker compose logs -f api     # Watch API logs

# Stop everything
docker compose down            # Keep data
docker compose down -v         # Delete all data too

# Full reset
docker compose down --volumes && docker compose up --build -d

# Run tests
make test
uv run pytest tests/ -v

# Format and lint
make format
make lint

# Start Jupyter (for notebooks)
uv run jupyter notebook notebooks/week1/week1_setup.ipynb

# Start Gradio chat UI
uv run python gradio_launcher.py

# Pull Ollama model
docker exec -it rag-ollama ollama pull llama3.2:1b

# Check health
curl http://localhost:8000/api/v1/health

# Ask a question
curl -X POST http://localhost:8000/api/v1/ask \
  -H "Content-Type: application/json" \
  -d '{"query": "What is attention mechanism?", "top_k": 5}'

# Agentic RAG
curl -X POST http://localhost:8000/agentic-ask \
  -H "Content-Type: application/json" \
  -d '{"query": "How does GPT-4 work?"}'

# Hybrid search (no LLM)
curl -X POST http://localhost:8000/api/v1/hybrid-search/ \
  -H "Content-Type: application/json" \
  -d '{"query": "neural networks", "top_k": 10, "use_hybrid": true}'
```

### Key Configuration Variables (.env)

```bash
# Essential
JINA_API_KEY=jina_xxxxx                    # Get free key at jina.ai
OLLAMA_MODEL=llama3.2:1b                   # Or: llama3.2:3b for better quality

# Optional (Telegram bot)
TELEGRAM__BOT_TOKEN=1234567890:ABC...      # From @BotFather on Telegram
TELEGRAM__ENABLED=true

# Optional (Langfuse monitoring)
LANGFUSE__PUBLIC_KEY=pk-lf-xxxx
LANGFUSE__SECRET_KEY=sk-lf-xxxx
LANGFUSE__ENABLED=true

# Tuning
CHUNKING__CHUNK_SIZE=600                   # Words per chunk
CHUNKING__OVERLAP_SIZE=100                 # Overlap between chunks
OPENSEARCH__VECTOR_DIMENSION=1024          # Jina embedding size
REDIS__TTL_HOURS=6                         # Cache duration
```

### API Quick Reference

```bash
# Health check
GET  /api/v1/health

# RAG Q&A (waits for complete answer)
POST /api/v1/ask
Body: {"query": "...", "top_k": 5, "use_hybrid": true, "model": "llama3.2:1b"}

# RAG Q&A (streams words as generated)
POST /api/v1/stream
Body: same as /ask

# Agentic RAG (intelligent multi-step)
POST /agentic-ask
Body: {"query": "...", "user_id": "my_user", "model": "llama3.2:1b"}

# Hybrid search (no AI generation)
POST /api/v1/hybrid-search/
Body: {"query": "...", "top_k": 10, "use_hybrid": true, "categories": ["cs.AI"]}
```

### Key Python Concepts Used

| Concept | Where Used | What It Does |
|---------|-----------|-------------|
| `async/await` | All API handlers | Non-blocking I/O (multiple requests simultaneously) |
| `asynccontextmanager` | `main.py:lifespan` | Startup/shutdown lifecycle management |
| `TypedDict` | `state.py` | Typed dictionary (no runtime overhead) |
| `Pydantic BaseModel` | All schemas | Data validation + serialization |
| `Annotated` | `state.py:messages` | Attach metadata to type hints |
| `Optional[X]` | Config, state fields | Either X or None |
| `@asynccontextmanager` | Cache, tracing | Context manager for resource management |
| `yield` | lifespan, generators | Pause and resume execution |
| `hashlib.sha256` | Cache | Deterministic hash for cache keys |
| Generator pattern | Streaming | Yield chunks without buffering all in memory |

### Debugging Tips

```bash
# View logs for specific service
docker compose logs api          # FastAPI logs
docker compose logs airflow      # Airflow logs
docker compose logs opensearch   # OpenSearch logs
docker compose logs rag-ollama   # Ollama logs

# Enter a container
docker exec -it rag-api bash    # Get shell in API container
docker exec -it rag-ollama bash # Get shell in Ollama container

# Check OpenSearch index
curl http://localhost:9200/arxiv-papers-chunks/_count
curl http://localhost:9200/arxiv-papers-chunks/_search?size=1

# Check Redis
docker exec -it rag-redis redis-cli
> KEYS *          # List all cache keys
> TTL exact_cache:xxxxx  # Check TTL remaining

# Check PostgreSQL
docker exec -it rag-postgres psql -U rag_user -d rag_db
> SELECT COUNT(*) FROM papers;
> SELECT arxiv_id, title FROM papers LIMIT 5;
```

---

## 22. SUMMARY

This project is a **7-week progressive course** that builds a production-grade AI system from scratch. Each week adds a new layer:

**Foundation Layer (Week 1-2):** Sets up the infrastructure (Docker containers for all services) and builds an automated pipeline that fetches academic papers from arXiv daily, parses their PDFs, and stores them in PostgreSQL.

**Search Layer (Week 3-4):** Adds OpenSearch for efficient keyword search (BM25), then enhances it with semantic vector search. Papers are split into 600-word chunks, each chunk gets a 1024-dimension embedding from Jina AI, and hybrid search combines keyword matching with semantic similarity using Reciprocal Rank Fusion.

**RAG Layer (Week 5):** Integrates Ollama (local AI model) to turn search into question-answering. The system finds relevant paper chunks via hybrid search, constructs a prompt with the context, and generates comprehensive answers. A Gradio web interface provides a chat experience.

**Production Layer (Week 6):** Adds Redis caching (identical queries return instantly), Langfuse monitoring (tracks every LLM call with latency, tokens, costs), and full observability.

**Agentic Layer (Week 7):** The most sophisticated addition. LangGraph orchestrates an intelligent 6-node workflow that: validates questions are in-domain (guardrail), retrieves documents, grades their relevance (grade), rewrites queries if needed (rewrite), generates answers (generate), and handles out-of-scope questions gracefully. A Telegram bot enables mobile access.

**The key architectural principle:** Each week's code builds on the previous without breaking it. The `/ask` endpoint (Week 5) still exists alongside `/agentic-ask` (Week 7). You can use any level of sophistication based on your needs.

---

## 23. CONCLUSION

### What You've Learned

1. **RAG Systems:** How to combine traditional search (BM25) with modern AI (vector embeddings + LLM) to build systems that answer questions from your own document corpus.

2. **Production Patterns:** Caching (Redis), monitoring (Langfuse), automated pipelines (Airflow), containerization (Docker), health checks, graceful startup/shutdown — the practices that separate production systems from demos.

3. **Agentic AI:** How to use LangGraph to build multi-step AI workflows that can reason, adapt, and handle edge cases (out-of-domain queries, poor retrieval results).

4. **Modern Python:** Async/await, Pydantic validation, dependency injection, context managers, streaming responses — current best practices for building fast, maintainable Python services.

### The Key Trade-offs

| Decision | Why This Choice | Alternative |
|----------|----------------|-------------|
| Local LLM (Ollama) | Privacy, no cost, no rate limits | Better quality with cloud APIs |
| BM25 + Vector (hybrid) | Best recall + precision | BM25 only (simpler, no Jina key) |
| Redis exact-match cache | Simple, predictable, O(1) | Semantic cache (smarter but complex) |
| Section-based chunking | Preserves document structure | Fixed-size (simpler implementation) |
| LangGraph for agents | Explicit control, debuggable | More flexible but harder to debug |

### When to Use Each Endpoint

```
Simple question with known topic → POST /ask
   (uses cache, fast, reliable)

Real-time response needed → POST /stream
   (same as /ask but streams words as generated)

Important/complex question → POST /agentic-ask
   (slower but smarter: validates, grades, rewrites if needed)

Just searching, no AI answer → POST /hybrid-search/
   (fastest, no LLM, just returns relevant chunks)
```

### The Big Picture

This system demonstrates that modern AI applications are NOT just about the AI model itself. The AI (Ollama + llama3.2) is actually one of the simpler components. The hard parts are:
- Getting good data (arXiv + Docling)
- Chunking it intelligently (TextChunker)
- Indexing it searchably (OpenSearch hybrid)
- Making it fast enough to use (Redis cache)
- Making it observable enough to improve (Langfuse)
- Making it smart enough to handle edge cases (LangGraph agents)

Every piece works together. Remove any one piece and the quality drops significantly. This is what "production" means — all the pieces, working together, reliably.

---

*Explanation compiled from 100+ source files across the production-agentic-rag-course-main project. All code examples are taken directly from the actual source code.*
