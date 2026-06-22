# Production RAG System — Complete End-to-End Explanation

> **Who this is for:** Beginners who want to understand how a real, production-grade RAG system is built from scratch — every component, every design decision, with code from the actual project.

---

## Table of Contents

1. [What is RAG and Why It Exists](#1-what-is-rag)
2. [The Full System Architecture](#2-full-architecture)
3. [Week 1 — Infrastructure Foundation](#3-week-1-infrastructure)
4. [Week 2 — Data Ingestion Pipeline](#4-week-2-data-ingestion)
5. [Week 3 — BM25 Keyword Search](#5-week-3-bm25-search)
6. [Week 4 — Chunking and Hybrid Search](#6-week-4-hybrid-search)
7. [Week 5 — Complete RAG Pipeline with LLM](#7-week-5-complete-rag)
8. [Week 6 — Production Monitoring and Caching](#8-week-6-monitoring)
9. [Week 7 — Agentic RAG with LangGraph](#9-week-7-agentic-rag)
10. [RAG Evaluation — End to End](#10-evaluation)
11. [Project Structure Deep Dive](#11-project-structure)
12. [Request Lifecycle A to Z](#12-request-lifecycle)
13. [Common RAG Failure Modes](#13-failure-modes)
14. [Cheatsheet](#14-cheatsheet)
15. [Summary and Conclusion](#15-summary)

---

## 1. What is RAG?

### The Core Problem RAG Solves

LLMs like Claude or GPT-4 are trained on data up to a cutoff date. They don't know:
- What happened last week
- What's in your company's private documents
- The contents of academic papers published after training
- Your internal policies, customer data, or proprietary knowledge

**RAG (Retrieval-Augmented Generation)** solves this by combining two things:

```
WITHOUT RAG:
  User:  "What does the paper 'Attention is All You Need' say about multi-head attention?"
  LLM:   "From my training, I know..." ← may be outdated, may hallucinate details

WITH RAG:
  User:  "What does the paper say about multi-head attention?"
  System: 1. RETRIEVE: search papers database → fetch relevant chunks
          2. AUGMENT:  put chunks into the LLM prompt as context
          3. GENERATE: LLM reads the actual chunks → gives accurate answer
  LLM:   "According to the paper (section 3.2): 'Multi-head attention allows...'"
         ← grounded in the actual document, cannot hallucinate text that's right there
```

### The RAG Formula

```
RAG = RETRIEVAL + AUGMENTATION + GENERATION

RETRIEVAL:   Find the most relevant documents/chunks from a knowledge base
AUGMENTATION: Add those documents to the LLM's prompt as context
GENERATION:  LLM uses context to generate a grounded, accurate answer
```

### Why "Production" RAG is Different from Tutorial RAG

```
TUTORIAL RAG (toy):
  ├── Load a PDF
  ├── Split by fixed chunk size (512 tokens)
  ├── Store in Chroma (in-memory vector db)
  ├── Ask a question → similarity search → stuff into prompt
  └── Get answer

PRODUCTION RAG (this project):
  ├── Automated data pipeline (Airflow DAG fetches papers daily from arXiv API)
  ├── Scientific PDF parsing (Docling handles complex LaTeX, tables, equations)
  ├── Section-aware chunking (respects document structure, not just token counts)
  ├── Hybrid search (BM25 keyword search + semantic vector search fused with RRF)
  ├── Streaming responses (SSE, not wait-5-seconds-then-dump)
  ├── Full observability (Langfuse traces every LLM call, every search, every token)
  ├── Redis caching (150-400x speedup for repeated questions)
  ├── Agentic RAG (LangGraph orchestrates: guardrail → retrieve → grade → rewrite → generate)
  ├── Query rewriting (auto-improve bad queries before retrieval)
  ├── Document grading (LLM judges whether retrieved docs are actually relevant)
  ├── Evaluation framework (RAGAS metrics: faithfulness, relevancy, recall)
  └── Telegram bot (mobile access to the full system)
```

---

## 2. Full System Architecture

### The Complete Stack

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                    PRODUCTION RAG SYSTEM                                      │
│                  (arXiv Paper Curator)                                        │
└──────────────────────────────────────────────────────────────────────────────┘

LAYER 1: INTERFACES (how users interact)
┌─────────────────────────────────────────────────────────────────────────────┐
│  Gradio Web UI     FastAPI REST API     Telegram Bot                        │
│  (Port 7861)       (Port 8000/docs)     (Mobile Access)                     │
└────────────────────────────┬────────────────────────────────────────────────┘
                             │
LAYER 2: API ROUTING
┌────────────────────────────▼────────────────────────────────────────────────┐
│  /api/v1/ask         Standard RAG (retrieve → generate)                     │
│  /api/v1/stream      Streaming RAG (SSE token-by-token)                     │
│  /api/v1/agentic-ask Agentic RAG (LangGraph orchestrated)                   │
│  /api/v1/search      BM25 keyword search only                               │
│  /api/v1/hybrid-search  Hybrid search (BM25 + vector)                       │
│  /api/v1/papers      Paper CRUD (list, get by ID)                           │
└──────┬──────────────────────┬──────────────────────┬──────────────────────┘
       │                      │                      │
LAYER 3: SERVICES
┌──────▼───────┐  ┌───────────▼──────┐  ┌───────────▼──────────────────────┐
│   RAG Service │  │ Agentic RAG      │  │ Cache Service                    │
│               │  │ (LangGraph)      │  │ (Redis)                          │
│  1. Embed     │  │  ┌─ Guardrail    │  │ Check cache first                │
│  2. Search    │  │  ├─ Retrieve     │  │ Return cached if hit             │
│  3. Prompt    │  │  ├─ Grade Docs   │  │ Store new results                │
│  4. Generate  │  │  ├─ Rewrite Q   │  └──────────────────────────────────┘
│  5. Stream    │  │  └─ Generate    │
└──────┬───────┘  └────────┬─────────┘
       │                   │
LAYER 4: SEARCH ENGINE
┌──────▼───────────────────▼──────────────────────────────────────────────────┐
│  OpenSearch 2.19                                                             │
│  ├── BM25 Index (keyword/lexical search)                                    │
│  ├── Vector Index (semantic similarity search, 1024-dim Jina embeddings)    │
│  └── RRF Fusion (combine BM25 + vector scores into one ranked list)         │
└──────────────────────────────────────────────────────────────────────────────┘

LAYER 5: LLM LAYER
┌──────────────────────────────────────────────────────────────────────────────┐
│  Ollama (Local LLM Server, Port 11434)                                       │
│  ├── Generation: llama3.1, mistral, or any local model                      │
│  ├── Guardrail scoring (structured JSON output)                              │
│  ├── Document grading (binary relevance judgment)                            │
│  └── Query rewriting (intelligent query improvement)                         │
└──────────────────────────────────────────────────────────────────────────────┘

LAYER 6: DATA STORAGE
┌────────────────────────┐  ┌─────────────────────────────────────────────────┐
│  PostgreSQL 16          │  │  Redis Cache                                    │
│  ├── Paper metadata     │  │  ├── Query → Response cache                    │
│  ├── Full text content  │  │  ├── TTL-based expiry                           │
│  └── Ingestion state    │  │  └── 150-400x speedup for repeat questions      │
└────────────────────────┘  └─────────────────────────────────────────────────┘

LAYER 7: DATA PIPELINE (automated)
┌──────────────────────────────────────────────────────────────────────────────┐
│  Apache Airflow 3.0 (Port 8080)                                              │
│  └── Daily DAG: arXiv API → PDF Parser → PostgreSQL → OpenSearch Index      │
└──────────────────────────────────────────────────────────────────────────────┘

LAYER 8: OBSERVABILITY
┌──────────────────────────────────────────────────────────────────────────────┐
│  Langfuse (Port 3000)                                                        │
│  ├── Every LLM call traced (model, tokens, latency, cost)                   │
│  ├── Every search traced (query, results, timing)                            │
│  ├── Every RAG pipeline traced end-to-end                                    │
│  └── Dashboards for quality and performance monitoring                       │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Evolution Week by Week

```
Week 1: [FastAPI] + [PostgreSQL] + [OpenSearch] + [Airflow] + [Ollama]
Week 2: + [arXiv API client] + [PDF Parser (Docling)] + [Airflow DAG]
Week 3: + [BM25 Search Service] + [/api/v1/search endpoint]
Week 4: + [Text Chunker] + [Jina Embeddings] + [Hybrid Search] + [RRF Fusion]
Week 5: + [RAG Service] + [/api/v1/ask] + [/api/v1/stream] + [Gradio UI]
Week 6: + [Langfuse Tracing] + [Redis Cache] + [/api/v1/stream updated]
Week 7: + [LangGraph Agent] + [5 Agent Nodes] + [Telegram Bot] + [/api/v1/agentic-ask]
```

---

## 3. Week 1 — Infrastructure Foundation

### What Gets Built

The entire infrastructure runs in Docker containers, orchestrated by `compose.yml`. Every service connects via a Docker network.

### Services and Their Roles

```
SERVICE           PORT   PURPOSE
─────────────────────────────────────────────────────────────────
FastAPI           8000   Your REST API server (the brain)
PostgreSQL 16     5432   Relational database (paper metadata)
OpenSearch 2.19   9200   Search engine (finds relevant papers)
OpenSearch Dash   5601   UI to explore search indexes
Apache Airflow    8080   Workflow scheduler (runs daily pipelines)
Ollama            11434  Local LLM server (runs models locally)
Redis             6379   In-memory cache (Week 6)
Langfuse          3000   Observability dashboard (Week 6)
Gradio            7861   Chat UI for RAG (Week 5)
```

### The FastAPI Application Structure

```python
# src/main.py — application entry point

from fastapi import FastAPI
from src.routers import ping, papers, search, hybrid_search, ask, agentic_ask
from src.middlewares import setup_middlewares

app = FastAPI(
    title="arXiv Paper Curator",
    description="Production RAG system for academic paper Q&A",
    version="1.0.0",
)

# Middleware: CORS, logging, request timing
setup_middlewares(app)

# Routers: each file handles a group of endpoints
app.include_router(ping.router)           # GET /health
app.include_router(papers.router)         # GET /api/v1/papers
app.include_router(search.router)         # POST /api/v1/search
app.include_router(hybrid_search.router)  # POST /api/v1/hybrid-search
app.include_router(ask.router)            # POST /api/v1/ask, /stream
app.include_router(agentic_ask.router)    # POST /api/v1/agentic-ask
```

### The Database Model

```python
# src/models/paper.py — SQLAlchemy ORM model

from sqlalchemy import Column, String, Text, DateTime, Integer
from sqlalchemy.dialects.postgresql import ARRAY
from src.database import Base

class Paper(Base):
    __tablename__ = "papers"
    
    id = Column(String, primary_key=True)           # UUID generated internally
    arxiv_id = Column(String, unique=True, index=True)  # e.g. "2310.12123"
    title = Column(String, nullable=False)
    abstract = Column(Text)
    authors = Column(ARRAY(String))                  # ["Author A", "Author B"]
    categories = Column(ARRAY(String))               # ["cs.LG", "cs.AI"]
    published_date = Column(DateTime)
    full_text = Column(Text)                         # Extracted PDF content
    pdf_url = Column(String)
    sections = Column(Text)                          # JSON: {"Introduction": "...", ...}
    ingestion_status = Column(String, default="pending")  # pending/completed/failed
    created_at = Column(DateTime, server_default="now()")
    updated_at = Column(DateTime, onupdate="now()")
```

### Configuration Management

```python
# src/config.py — all config in one place via Pydantic Settings

from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database
    database__host: str = "localhost"
    database__port: int = 5432
    database__name: str = "arxiv_papers"
    database__user: str = "postgres"
    database__password: str = "postgres"
    
    # OpenSearch
    opensearch__host: str = "localhost"
    opensearch__port: int = 9200
    opensearch__index: str = "arxiv_papers"
    
    # Ollama (local LLM)
    ollama__base_url: str = "http://localhost:11434"
    ollama__model: str = "llama3.1"
    
    # Jina AI (embeddings)
    jina_api_key: str = ""
    
    # Redis (caching)
    redis__host: str = "localhost"
    redis__port: int = 6379
    
    # Langfuse (observability)
    langfuse__public_key: str = ""
    langfuse__secret_key: str = ""
    langfuse__host: str = "http://localhost:3000"
    
    class Config:
        env_file = ".env"
        env_nested_delimiter = "__"   # database__host → database.host

settings = Settings()
```

**Why `__` delimiter?** It lets you set nested config via env vars: `DATABASE__HOST=mydb.aws.com` without Python code changes. Production-friendly.

### Health Check Endpoint

```python
# src/routers/ping.py

from fastapi import APIRouter
from src.schemas.api.health import HealthResponse

router = APIRouter()

@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Check that all services are alive."""
    return HealthResponse(
        status="healthy",
        services={
            "api": "up",
            "database": check_postgres(),
            "opensearch": check_opensearch(),
            "ollama": check_ollama(),
        }
    )
```

---

## 4. Week 2 — Data Ingestion Pipeline

### The Data Flow

```
arXiv API
    │ (fetch paper metadata: title, abstract, authors, PDF URL)
    ▼
ArxivClient (rate-limited, retry logic)
    │
    ▼
PDFParserService (Docling: extract text, sections, tables)
    │
    ▼
PostgreSQL (store metadata + full_text + sections)
    │
    ▼
OpenSearch (index for search — done in Week 3/4)
```

### The arXiv Client

```python
# src/services/arxiv/client.py (conceptual)

import time
import httpx
from typing import List

class ArxivClient:
    """Fetches papers from arXiv API with rate limiting."""
    
    BASE_URL = "http://export.arxiv.org/api/query"
    RATE_LIMIT_DELAY = 3.0   # 3 seconds between requests (arXiv requires this)
    
    def __init__(self):
        self.last_request_time = 0
    
    def search_papers(
        self,
        query: str,                    # e.g. "machine learning transformers"
        categories: List[str],         # e.g. ["cs.LG", "cs.AI", "cs.CL"]
        max_results: int = 50,
        start: int = 0,
    ) -> List[dict]:
        """Fetch papers matching query from arXiv."""
        
        # Rate limiting: always wait 3s between requests
        elapsed = time.time() - self.last_request_time
        if elapsed < self.RATE_LIMIT_DELAY:
            time.sleep(self.RATE_LIMIT_DELAY - elapsed)
        
        # Build category filter: "cat:cs.LG OR cat:cs.AI"
        cat_filter = " OR ".join([f"cat:{c}" for c in categories])
        full_query = f"({query}) AND ({cat_filter})"
        
        # Call arXiv API (returns Atom XML)
        response = httpx.get(self.BASE_URL, params={
            "search_query": full_query,
            "start": start,
            "max_results": max_results,
            "sortBy": "submittedDate",
            "sortOrder": "descending",
        })
        
        self.last_request_time = time.time()
        
        # Parse XML response → list of paper dicts
        return self._parse_atom_feed(response.text)
```

### Scientific PDF Parsing with Docling

```python
# Why Docling instead of PyPDF2 or pdfplumber?
#
# Regular PDFs:
#   PyPDF2 works fine — extract text, done
#
# Scientific PDFs:
#   - LaTeX-rendered equations → need special handling
#   - Multi-column layouts → reading order matters
#   - Tables with merged cells → structure must be preserved
#   - References section → should be separated
#   - Figures with captions → captions are useful, figures are not
#
# Docling handles ALL of this automatically

from docling.document_converter import DocumentConverter

class PDFParserService:
    def __init__(self):
        self.converter = DocumentConverter()
    
    def parse_pdf(self, pdf_url: str) -> dict:
        """Parse a scientific PDF into structured text."""
        result = self.converter.convert(pdf_url)
        doc = result.document
        
        # Extract structured sections
        sections = {}
        current_section = "Introduction"
        current_text = []
        
        for item in doc.iterate_items():
            if hasattr(item, 'text'):
                # Detect section headers (bold, larger font)
                if item.is_heading():
                    if current_text:
                        sections[current_section] = " ".join(current_text)
                    current_section = item.text
                    current_text = []
                else:
                    current_text.append(item.text)
        
        # Save last section
        if current_text:
            sections[current_section] = " ".join(current_text)
        
        return {
            "full_text": doc.export_to_text(),
            "sections": sections,           # {"Introduction": "...", "Methods": "..."}
            "markdown": doc.export_to_markdown(),
        }
```

### Airflow DAG — Automated Daily Ingestion

```python
# airflow/dags/arxiv_ingestion_dag.py

from airflow.decorators import dag, task
from datetime import datetime, timedelta

@dag(
    dag_id="arxiv_daily_ingestion",
    description="Fetch new arXiv papers daily and store in PostgreSQL",
    schedule="0 6 * * *",         # Run daily at 6 AM UTC
    start_date=datetime(2024, 1, 1),
    catchup=False,
    default_args={
        "retries": 3,
        "retry_delay": timedelta(minutes=5),
    },
    tags=["rag", "data-ingestion"],
)
def arxiv_ingestion():
    
    @task
    def fetch_papers():
        """Fetch paper metadata from arXiv API."""
        from src.services.arxiv.client import ArxivClient
        
        client = ArxivClient()
        papers = client.search_papers(
            query="large language models RAG retrieval augmented generation",
            categories=["cs.LG", "cs.AI", "cs.CL", "cs.IR"],
            max_results=100,
        )
        return papers   # Passed to next task
    
    @task
    def parse_pdfs(papers: list):
        """Download and parse PDFs for each paper."""
        from src.services.pdf_parser.service import PDFParserService
        
        parser = PDFParserService()
        enriched = []
        
        for paper in papers:
            try:
                parsed = parser.parse_pdf(paper["pdf_url"])
                paper["full_text"] = parsed["full_text"]
                paper["sections"] = parsed["sections"]
                paper["status"] = "parsed"
            except Exception as e:
                paper["status"] = "parse_failed"
                paper["error"] = str(e)
            
            enriched.append(paper)
        
        return enriched
    
    @task
    def store_to_database(papers: list):
        """Store parsed papers in PostgreSQL."""
        from src.repositories.paper import PaperRepository
        
        repo = PaperRepository()
        stored_count = 0
        
        for paper in papers:
            if paper.get("status") == "parsed":
                repo.upsert(paper)   # Insert or update by arxiv_id
                stored_count += 1
        
        return {"stored": stored_count, "total": len(papers)}
    
    @task
    def index_to_opensearch(store_result: dict):
        """Index stored papers in OpenSearch for search."""
        from src.services.indexing.hybrid_indexer import HybridIndexer
        
        indexer = HybridIndexer()
        new_papers = indexer.index_new_papers()
        return {"indexed": new_papers}
    
    # DAG wiring: task A feeds into task B
    papers = fetch_papers()
    parsed = parse_pdfs(papers)
    stored = store_to_database(parsed)
    index_to_opensearch(stored)

# Instantiate the DAG
arxiv_ingestion()
```

**What makes this production-grade:**
- Retries (3 attempts) for transient failures (API timeouts, PDF parse errors)
- `upsert` instead of insert (idempotent — safe to rerun)
- Tasks are separate and testable
- Schedule-driven (no cron scripts, Airflow manages execution history and monitoring)

---

## 5. Week 3 — BM25 Keyword Search

### Why BM25 Before Vectors?

Most RAG tutorials jump straight to vector search. This project takes the professional path:

```
PROFESSIONAL APPROACH:
  Week 3: BM25 (keyword search) ← FIRST
  Week 4: Add vectors (hybrid search) ← SECOND

WHY THIS ORDER?
  1. BM25 is highly predictable — if a query contains exact keywords, BM25 WILL find it
  2. Vector search has failure modes that are hard to debug (embedding drift, poor quality)
  3. Companies like Elasticsearch, Algolia, Solr have used BM25 for 20 years with great results
  4. Hybrid (BM25 + vectors) beats pure vector search in almost every benchmark
  5. You can't debug hybrid search without understanding BM25 first
```

### What is BM25?

BM25 (Best Match 25) is a statistical ranking algorithm. Given a query, it scores every document:

```
BM25 Score(document, query) = Σ (for each term in query):
  IDF(term) × TF(term, document) × (k1 + 1) / (TF(term, document) + k1 × (1 - b + b × |doc| / avgdl))

Where:
  IDF(term)  = how RARE the term is across all documents
               → rare terms score higher ("quantum" > "the")
  TF(term)   = how often the term appears in this document
               → but with diminishing returns (not linear)
  |doc|      = length of this document
  avgdl      = average document length in the collection
  k1, b      = tunable parameters (k1=1.5, b=0.75 are defaults)

Intuition:
  - Exact keyword match → high score
  - Common words (the, is, of) → near-zero score  
  - Rare domain terms (backpropagation, transformer) → high IDF → high score
  - Score plateaus after term appears 3-4 times (diminishing returns via k1)
  - Shorter documents score slightly higher (length normalization via b)
```

### OpenSearch Index Configuration

```python
# src/services/opensearch/index_config_hybrid.py

PAPERS_INDEX_MAPPING = {
    "mappings": {
        "properties": {
            # BM25 searchable text fields
            "title": {
                "type": "text",
                "analyzer": "english",       # Removes stopwords, applies stemming
                "boost": 2.0,                # Title matches count 2x more than body
            },
            "abstract": {
                "type": "text",
                "analyzer": "english",
                "boost": 1.5,
            },
            "chunk_text": {
                "type": "text",
                "analyzer": "english",
            },
            "section_name": {
                "type": "keyword",           # Exact match only (no analysis)
            },
            
            # Vector field (added in Week 4)
            "embedding": {
                "type": "knn_vector",
                "dimension": 1024,           # Jina embeddings dimension
                "method": {
                    "engine": "nmslib",
                    "space_type": "cosinesimil",
                    "name": "hnsw",
                    "parameters": {
                        "ef_construction": 128,
                        "m": 24,
                    }
                }
            },
            
            # Filter fields
            "arxiv_id": {"type": "keyword"},
            "paper_id": {"type": "keyword"},
            "authors": {"type": "keyword"},
            "categories": {"type": "keyword"},
            "published_date": {"type": "date"},
        }
    },
    "settings": {
        "number_of_shards": 1,
        "number_of_replicas": 0,             # Development: 0 replicas
        "index.knn": True,                   # Enable KNN for vector search
    }
}
```

### BM25 Query Builder

```python
# src/services/opensearch/query_builder.py

class QueryBuilder:
    
    def build_bm25_query(
        self,
        query: str,
        top_k: int = 10,
        filters: dict = None,
    ) -> dict:
        """Build an OpenSearch BM25 query."""
        
        query_body = {
            "size": top_k,
            "query": {
                "bool": {
                    "must": [
                        {
                            "multi_match": {
                                "query": query,
                                "fields": [
                                    "title^2",        # Title matches weighted 2x
                                    "abstract^1.5",   # Abstract weighted 1.5x
                                    "chunk_text",     # Full text weighted 1x
                                ],
                                "type": "best_fields",
                                "operator": "or",     # Any word match counts
                                "fuzziness": "AUTO",  # Handles typos: "tranformer" → "transformer"
                            }
                        }
                    ],
                    "filter": self._build_filters(filters),
                }
            },
            "_source": ["arxiv_id", "title", "chunk_text", "section_name", "authors", "published_date"],
            "highlight": {
                "fields": {
                    "chunk_text": {"number_of_fragments": 2},
                    "title": {},
                }
            }
        }
        return query_body
    
    def _build_filters(self, filters: dict) -> list:
        """Build filter clauses (don't affect scoring, just narrow results)."""
        clauses = []
        
        if not filters:
            return clauses
        
        if "categories" in filters:
            clauses.append({"terms": {"categories": filters["categories"]}})
        
        if "date_from" in filters:
            clauses.append({"range": {"published_date": {"gte": filters["date_from"]}}})
        
        if "authors" in filters:
            clauses.append({"terms": {"authors": filters["authors"]}})
        
        return clauses
```

---

## 6. Week 4 — Chunking and Hybrid Search

### Why Chunk Documents?

```
PROBLEM: A research paper is 8,000-40,000 words
         LLM context window: 2,000-8,000 tokens for RAG context
         
         If you index the WHOLE paper as one document:
           - Search returns the whole 40,000-word paper
           - You can't fit it in the prompt
           - Relevance is diluted (specific answer buried in noise)
         
         If you chunk into 600-word pieces:
           - Search returns the SPECIFIC section that answers the question
           - Fits in the prompt easily
           - High-precision retrieval (the right part, not the whole thing)
```

### The Section-Aware Chunking Strategy

```python
# src/services/indexing/text_chunker.py

class TextChunker:
    """Chunks papers with respect to their section structure."""
    
    def __init__(
        self,
        chunk_size: int = 600,      # Target words per chunk
        overlap_size: int = 100,    # Words shared between adjacent chunks
        min_chunk_size: int = 100,  # Discard chunks smaller than this
    ):
        self.chunk_size = chunk_size
        self.overlap_size = overlap_size
        self.min_chunk_size = min_chunk_size
    
    def chunk_paper(
        self,
        title: str,
        abstract: str,
        full_text: str,
        arxiv_id: str,
        paper_id: str,
        sections: dict = None,     # {"Introduction": "...", "Methods": "..."}
    ) -> List[TextChunk]:
        """Chunk a paper using section-aware strategy."""
        
        chunks = []
        
        # CHUNK 1: Always create an abstract chunk (high relevance for overview questions)
        if abstract:
            chunks.append(TextChunk(
                text=f"Title: {title}\n\nAbstract: {abstract}",
                metadata=ChunkMetadata(
                    arxiv_id=arxiv_id,
                    paper_id=paper_id,
                    section_name="abstract",
                    chunk_index=0,
                )
            ))
        
        # CHUNK 2+: Section-based chunking (if sections extracted)
        if sections and isinstance(sections, dict):
            for section_name, section_text in sections.items():
                section_chunks = self._chunk_text(
                    text=section_text,
                    metadata=ChunkMetadata(
                        arxiv_id=arxiv_id,
                        paper_id=paper_id,
                        section_name=section_name,
                    )
                )
                chunks.extend(section_chunks)
        
        # FALLBACK: Simple word-based chunking if no sections
        else:
            text_chunks = self._chunk_text(
                text=full_text,
                metadata=ChunkMetadata(arxiv_id=arxiv_id, paper_id=paper_id),
            )
            chunks.extend(text_chunks)
        
        return chunks
    
    def _chunk_text(self, text: str, metadata: ChunkMetadata) -> List[TextChunk]:
        """Chunk a text string with sliding window and overlap."""
        words = text.split()
        chunks = []
        chunk_index = 0
        position = 0
        
        while position < len(words):
            # Take chunk_size words starting from position
            chunk_words = words[position : position + self.chunk_size]
            
            # Reconstruct text from words
            chunk_text = " ".join(chunk_words)
            
            # Only keep chunks above minimum size
            if len(chunk_words) >= self.min_chunk_size:
                m = ChunkMetadata(
                    arxiv_id=metadata.arxiv_id,
                    paper_id=metadata.paper_id,
                    section_name=metadata.section_name,
                    chunk_index=chunk_index,
                    word_count=len(chunk_words),
                )
                chunks.append(TextChunk(text=chunk_text, metadata=m))
                chunk_index += 1
            
            # Slide forward by (chunk_size - overlap_size)
            # This creates OVERLAP between consecutive chunks
            step = self.chunk_size - self.overlap_size
            position += step
        
        return chunks
```

**Why 100-word overlap?** Consider this scenario:

```
Text: "...The key innovation is the attention mechanism. [CHUNK 1 ENDS]
       [CHUNK 2 STARTS] This mechanism allows tokens to attend to..."

WITHOUT OVERLAP:
  Query: "how does the attention mechanism work?"
  Chunk 1: "...The key innovation is the attention mechanism."  ← incomplete sentence
  Chunk 2: "This mechanism allows tokens to attend to..."       ← no context about what "this" refers to

WITH 100-WORD OVERLAP:
  Chunk 1: "...The key innovation is the attention mechanism."
  Chunk 2: "...The key innovation is the attention mechanism. This mechanism allows tokens to attend to..."
           ← context preserved! Both chunks can answer the question
```

### Jina AI Embeddings

```python
# src/services/embeddings/jina_client.py

import httpx
from typing import List

class JinaEmbeddingsClient:
    """Client for Jina AI embedding API."""
    
    API_URL = "https://api.jina.ai/v1/embeddings"
    MODEL = "jina-embeddings-v3"  # 1024 dimensions, state-of-the-art
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
    
    def embed_query(self, query: str) -> List[float]:
        """Embed a search query (task: retrieval.query)."""
        return self._embed([query], task="retrieval.query")[0]
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed document chunks for indexing (task: retrieval.passage)."""
        # Note: different task type for query vs document!
        # Using wrong task type degrades retrieval quality significantly
        return self._embed(texts, task="retrieval.passage")
    
    def _embed(self, texts: List[str], task: str) -> List[List[float]]:
        """Call Jina API with batching."""
        BATCH_SIZE = 100   # Jina API limit per request
        all_embeddings = []
        
        for i in range(0, len(texts), BATCH_SIZE):
            batch = texts[i : i + BATCH_SIZE]
            
            response = httpx.post(
                self.API_URL,
                headers=self.headers,
                json={
                    "model": self.MODEL,
                    "task": task,
                    "dimensions": 1024,
                    "input": batch,
                },
                timeout=60.0,
            )
            response.raise_for_status()
            
            data = response.json()
            embeddings = [item["embedding"] for item in data["data"]]
            all_embeddings.extend(embeddings)
        
        return all_embeddings
```

### Hybrid Search with RRF Fusion

```
HYBRID SEARCH INTUITION:

Query: "attention mechanism in transformers"

BM25 results (keyword match):
  Rank 1: "Attention Is All You Need" paper         (score: 18.4)  ← exact keyword match
  Rank 2: "BERT: Pre-training of Transformers"      (score: 14.2)
  Rank 3: "RoBERTa: A Robustly Optimized Baseline"  (score: 9.1)
  Rank 4: "GPT-2: Language Models are Multitask"    (score: 7.8)

Vector results (semantic similarity):
  Rank 1: "Self-Attention in Computer Vision"       (score: 0.94)  ← semantically related
  Rank 2: "Attention Is All You Need"               (score: 0.92)
  Rank 3: "Sparse Transformers"                     (score: 0.89)
  Rank 4: "BERT: Pre-training of Transformers"      (score: 0.87)

RRF FUSION (combines both using rank positions, not raw scores):
  RRF(doc) = Σ 1 / (k + rank_in_each_list)    where k=60 (constant)

  "Attention Is All You Need":           1/(60+1) + 1/(60+2) = 0.0164 + 0.0161 = 0.0325
  "BERT: Pre-training of Transformers":  1/(60+2) + 1/(60+4) = 0.0161 + 0.0156 = 0.0317
  "Self-Attention in Computer Vision":   0 + 1/(60+1)        = 0 + 0.0164 = 0.0164
  "Sparse Transformers":                 0 + 1/(60+3)        = 0 + 0.0159 = 0.0159

Final ranking after RRF:
  Rank 1: "Attention Is All You Need"           ← appeared HIGH in BOTH lists
  Rank 2: "BERT: Pre-training of Transformers"  ← appeared HIGH in BOTH lists
  Rank 3: "Self-Attention in Computer Vision"   ← semantic only, but high semantic rank
  Rank 4: "Sparse Transformers"

WHY RRF IS BETTER THAN SCORE COMBINATION:
  - BM25 scores are in range [0, 30+]
  - Vector scores are in range [-1, 1] or [0, 1]
  - You CANNOT add 18.4 + 0.94 (different scales!)
  - RRF uses only RANKS (1st, 2nd, 3rd...) — scale-independent
```

```python
# src/services/opensearch/query_builder.py — hybrid query

def build_hybrid_query(self, query: str, query_embedding: List[float], top_k: int = 10) -> dict:
    """Build a hybrid BM25 + KNN query with RRF fusion."""
    
    return {
        "size": top_k,
        "query": {
            "hybrid": {
                "queries": [
                    # Query 1: BM25 lexical search
                    {
                        "multi_match": {
                            "query": query,
                            "fields": ["title^2", "abstract^1.5", "chunk_text"],
                        }
                    },
                    # Query 2: KNN vector search
                    {
                        "knn": {
                            "embedding": {
                                "vector": query_embedding,
                                "k": top_k,
                            }
                        }
                    }
                ]
            }
        },
        "search_pipeline": {
            "phase_results_processors": [
                {
                    "normalization-processor": {
                        "normalization": {"technique": "min_max"},
                        "combination": {
                            "technique": "rrf",        # Reciprocal Rank Fusion
                            "parameters": {"rank_constant": 60}
                        }
                    }
                }
            ]
        }
    }
```

---

## 7. Week 5 — Complete RAG Pipeline with LLM

### The Full RAG Request Flow

```python
# src/routers/ask.py

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from src.schemas.api.ask import AskRequest, AskResponse

router = APIRouter(prefix="/api/v1")

@router.post("/ask", response_model=AskResponse)
async def ask(request: AskRequest, rag_service = Depends(get_rag_service)):
    """Standard RAG endpoint — waits for full response."""
    result = await rag_service.answer(
        query=request.query,
        top_k=request.top_k or 5,
        use_hybrid=request.use_hybrid or True,
    )
    return AskResponse(
        answer=result.answer,
        sources=result.sources,
        retrieval_time_ms=result.retrieval_time_ms,
        generation_time_ms=result.generation_time_ms,
    )

@router.post("/stream")
async def stream_ask(request: AskRequest, rag_service = Depends(get_rag_service)):
    """Streaming RAG endpoint — returns tokens as Server-Sent Events."""
    async def generate():
        async for chunk in rag_service.stream_answer(request.query):
            # SSE format: "data: <content>\n\n"
            yield f"data: {chunk}\n\n"
        yield "data: [DONE]\n\n"    # Signal completion to client
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",     # Disable nginx buffering
        }
    )
```

### The RAG Service — Core Logic

```python
# src/services/rag_service.py (conceptual)

class RAGService:
    """Orchestrates: embed → search → build prompt → generate."""
    
    def __init__(
        self,
        opensearch: OpenSearchClient,
        embeddings: JinaEmbeddingsClient,
        ollama: OllamaClient,
        langfuse_tracer: Optional[RAGTracer] = None,
        cache: Optional[CacheService] = None,
    ):
        self.opensearch = opensearch
        self.embeddings = embeddings
        self.ollama = ollama
        self.tracer = langfuse_tracer
        self.cache = cache
    
    async def answer(self, query: str, top_k: int = 5, use_hybrid: bool = True) -> RAGResult:
        """Execute full RAG pipeline."""
        
        # STEP 0: Check cache (skip entire pipeline if cached)
        if self.cache:
            cached = await self.cache.get(query)
            if cached:
                return cached   # 150-400x faster than running the pipeline
        
        # STEP 1: Embed the query
        query_embedding = self.embeddings.embed_query(query)
        
        # STEP 2: Retrieve relevant chunks from OpenSearch
        if use_hybrid:
            chunks = self.opensearch.hybrid_search(query, query_embedding, top_k)
        else:
            chunks = self.opensearch.bm25_search(query, top_k)
        
        # STEP 3: Build the prompt with retrieved context
        prompt = self._build_prompt(query, chunks)
        
        # STEP 4: Generate answer with local LLM
        answer = await self.ollama.generate(prompt)
        
        # STEP 5: Extract source citations
        sources = self._extract_sources(chunks)
        
        result = RAGResult(answer=answer, sources=sources, ...)
        
        # STEP 6: Cache result for future identical queries
        if self.cache:
            await self.cache.set(query, result)
        
        return result
    
    def _build_prompt(self, query: str, chunks: List[dict]) -> str:
        """Build the RAG prompt — context + question."""
        
        # Format retrieved chunks as numbered documents
        context_parts = []
        for i, chunk in enumerate(chunks, 1):
            context_parts.append(
                f"[Document {i}]\n"
                f"Paper: {chunk['title']}\n"
                f"Section: {chunk.get('section_name', 'unknown')}\n"
                f"Content: {chunk['chunk_text']}\n"
            )
        
        context = "\n---\n".join(context_parts)
        
        # System prompt is loaded from file (easily editable without code changes)
        system_prompt = self._load_system_prompt()
        
        return f"""{system_prompt}

RETRIEVED CONTEXT:
{context}

USER QUESTION: {query}

ANSWER:"""
    
    def _load_system_prompt(self) -> str:
        """Load from file for easy editing."""
        # src/services/ollama/prompts/rag_system.txt
        with open("src/services/ollama/prompts/rag_system.txt") as f:
            return f.read()
```

### The Optimized System Prompt

```
# src/services/ollama/prompts/rag_system.txt
# Key insight: shorter prompt = faster inference + cheaper

You are a research assistant specializing in CS/AI/ML papers.

Rules:
- Answer ONLY based on the provided context documents
- If context doesn't contain the answer, say "I don't have information about this"
- Cite paper titles when referencing specific claims
- Be concise but complete
- Never hallucinate information not in the context
```

**Why a separate file?** The prompt evolves frequently. Keeping it in a `.txt` file means:
- Marketing/content teams can edit prompts without touching Python code
- You can run A/B tests by swapping prompt files
- Git history shows prompt changes separately from code changes

### Streaming with Ollama

```python
# src/services/ollama/client.py

import httpx
import json
from typing import AsyncIterator

class OllamaClient:
    """Client for local Ollama LLM server."""
    
    async def stream_generate(self, prompt: str, model: str = "llama3.1") -> AsyncIterator[str]:
        """Stream tokens from Ollama as they're generated."""
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": True,             # Critical: enable streaming
                    "options": {
                        "temperature": 0.1,     # Low temperature = more consistent
                        "num_predict": 512,     # Max tokens to generate
                        "stop": ["USER QUESTION:", "RETRIEVED CONTEXT:"],  # Stop tokens
                    },
                },
            ) as response:
                async for line in response.aiter_lines():
                    if line:
                        data = json.loads(line)
                        token = data.get("response", "")
                        if token:
                            yield token         # One token at a time → SSE to user
                        
                        if data.get("done"):
                            break
```

---

## 8. Week 6 — Production Monitoring and Caching

### Langfuse — What Gets Traced

Every RAG request creates a tree of spans in Langfuse:

```
TRACE: rag_request
  └── session_id: sess-abc123, user_id: user-123

  ├── SPAN: query_embedding
  │   ├── input: {query: "what is attention mechanism?", length: 35}
  │   ├── output: {embedding_duration_ms: 145.2, success: true}
  │   └── duration: 145ms

  ├── SPAN: search_retrieval
  │   ├── input: {query: "...", top_k: 5, mode: "hybrid"}
  │   ├── output: {chunks_returned: 5, unique_papers: 3, total_hits: 47}
  │   └── duration: 89ms

  ├── SPAN: prompt_construction
  │   ├── input: {chunk_count: 5}
  │   ├── output: {prompt_length: 2847, prompt_preview: "You are a research..."}
  │   └── duration: 2ms

  └── SPAN: llm_generation
      ├── input: {model: "llama3.1", prompt_length: 2847}
      ├── output: {response: "The attention mechanism works by...", response_length: 412}
      └── duration: 4.2s
```

### The Langfuse Tracer

```python
# src/services/langfuse/tracer.py

from contextlib import contextmanager

class RAGTracer:
    """Wraps Langfuse SDK for RAG-specific tracing."""
    
    def __init__(self, tracer: LangfuseTracer):
        self.tracer = tracer
    
    @contextmanager
    def trace_request(self, user_id: str, query: str):
        """Context manager that wraps a full RAG request in a trace."""
        trace = None
        try:
            with self.tracer.trace_rag_request(
                query=query,
                user_id=user_id,
                session_id=f"session_{user_id}",
            ) as trace:
                yield trace          # Caller gets the trace object to attach spans
        finally:
            if trace:
                self.tracer.flush()  # Ensure all events are sent before response
    
    @contextmanager
    def trace_embedding(self, trace, query: str):
        """Trace the embedding step."""
        span = self.tracer.create_span(
            trace=trace,
            name="query_embedding",
            input_data={"query": query, "query_length": len(query)},
        )
        try:
            yield span
        finally:
            if span:
                span.end()           # Always close spans, even on exceptions

# Usage in RAG service:
async def answer(self, query: str) -> RAGResult:
    with self.tracer.trace_request(user_id="user-123", query=query) as trace:
        
        with self.tracer.trace_embedding(trace, query) as emb_span:
            embedding = self.embeddings.embed_query(query)
            self.tracer.update_span(emb_span, output={"embedding_dim": len(embedding)})
        
        with self.tracer.trace_search(trace, query, top_k=5) as search_span:
            chunks = self.opensearch.hybrid_search(query, embedding, 5)
            self.tracer.end_search(search_span, chunks, ...)
        
        # etc...
```

### Redis Caching — Exact Match Strategy

```python
# src/services/cache/service.py

import redis
import hashlib
import json
from typing import Optional

class CacheService:
    """Redis-based exact match cache for RAG responses."""
    
    DEFAULT_TTL = 3600   # Cache entries expire after 1 hour
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
    
    def _cache_key(self, query: str) -> str:
        """Deterministic cache key from query text."""
        # Normalize: lowercase, strip whitespace
        normalized = query.lower().strip()
        # Hash to fixed-length key (SHA256 → 64 hex chars)
        return f"rag:v1:{hashlib.sha256(normalized.encode()).hexdigest()}"
    
    async def get(self, query: str) -> Optional[dict]:
        """Return cached response or None."""
        key = self._cache_key(query)
        
        try:
            cached = self.redis.get(key)
            if cached:
                return json.loads(cached)
        except redis.RedisError:
            pass    # Cache failure → degrade gracefully (run the pipeline)
        
        return None
    
    async def set(self, query: str, result: dict, ttl: int = None) -> bool:
        """Cache a response with TTL."""
        key = self._cache_key(query)
        
        try:
            self.redis.setex(
                name=key,
                time=ttl or self.DEFAULT_TTL,
                value=json.dumps(result),
            )
            return True
        except redis.RedisError:
            return False  # Cache failure → don't fail the user request
```

**The 150-400x speedup claim explained:**
```
First request: "What is attention mechanism?"
  → embed (145ms) + search (89ms) + LLM generate (4200ms) = 4.4 seconds

Subsequent identical request (from cache):
  → Redis GET (1-5ms) = 0.005 seconds

Speedup: 4400ms / 10ms = 440x faster
```

**Cache TTL strategy:**
```
1 hour TTL for most queries
  → Papers don't change content, so responses stay valid
  → But new papers are added daily, so we don't cache forever

Could also use: content-based invalidation
  → When new papers indexed → clear relevant cache keys
  → More complex but more accurate
```

---

## 9. Week 7 — Agentic RAG with LangGraph

### Why Agentic RAG?

```
STANDARD RAG (deterministic):
  Query → Retrieve → Generate → Done
  
  Problem 1: Bad query → bad retrieval → bad answer (no recovery)
  Problem 2: Retrieved docs may be irrelevant → LLM hallucinates anyway
  Problem 3: Out-of-domain queries answered confidently (no guardrail)

AGENTIC RAG (adaptive):
  Query → GUARDRAIL (is this in scope?)
        → RETRIEVE (get docs)
        → GRADE (are docs relevant?)
        → if not relevant: REWRITE QUERY → RETRIEVE again
        → GENERATE (grounded answer)
  
  Solves all 3 problems above with intelligent decision nodes
```

### The LangGraph Workflow

```
                    ┌──────────────────────────────────────┐
                    │         START                         │
                    └──────────────────┬───────────────────┘
                                       │
                    ┌──────────────────▼───────────────────┐
                    │      GUARDRAIL NODE                   │
                    │  "Is this query about CS/AI papers?"  │
                    │  LLM scores query: 0-100              │
                    └──────────┬────────────────┬──────────┘
                  score ≥ 50   │                │  score < 50
                               │                │
              ┌────────────────▼──┐         ┌───▼──────────────────┐
              │  RETRIEVE NODE    │         │  OUT OF SCOPE NODE    │
              │  Hybrid search    │         │  "Please ask about    │
              │  top_k chunks     │         │   CS/AI papers only"  │
              └────────┬──────────┘         └──────────────────────┘
                       │
              ┌────────▼──────────┐
              │  GRADE DOCS NODE  │
              │  LLM evaluates:   │
              │  "Are retrieved   │
              │   docs relevant?" │
              └──────┬────────────┘
           relevant  │             │  not relevant
                     │             │
         ┌───────────▼──┐   ┌──────▼───────────────────┐
         │  GENERATE    │   │  REWRITE QUERY NODE       │
         │  ANSWER NODE │   │  LLM rewrites query for   │
         │              │   │  better retrieval         │
         │  Final ans   │   └──────┬────────────────────┘
         └──────────────┘         │
                                  │ (attempt < max_attempts)
                                  └──► back to RETRIEVE NODE
                                  │
                                  │ (attempt >= max_attempts)
                                  └──► GENERATE ANSWER NODE anyway
```

### Agent State

```python
# src/services/agents/state.py

from typing import Annotated, List, Optional
from langchain_core.messages import BaseMessage
from langgraph.graph import MessagesState
from .models import GuardrailScoring, GradingResult

class AgentState(MessagesState):
    """State that flows through every node in the graph."""
    
    # Query tracking
    original_query: str          # The original user question (never modified)
    rewritten_query: Optional[str] = None  # LLM-improved version
    
    # Retrieval tracking
    retrieved_docs: List[dict] = []      # Chunks from OpenSearch
    retrieval_attempts: int = 0          # How many times we've tried retrieval
    
    # Evaluation results
    guardrail_result: Optional[GuardrailScoring] = None   # In-scope score
    grading_results: List[GradingResult] = []             # Per-doc relevance scores
    routing_decision: Optional[str] = None                # "generate_answer" or "rewrite_query"
    
    # Output
    final_answer: Optional[str] = None
    reasoning_steps: List[str] = []     # Human-readable trace of decisions
```

### Node 1 — Guardrail

```python
# src/services/agents/nodes/guardrail_node.py

async def ainvoke_guardrail_step(state: AgentState, runtime: Runtime[Context]) -> dict:
    """Check if query is within scope using LLM scoring."""
    
    query = get_latest_query(state["messages"])
    
    guardrail_prompt = GUARDRAIL_PROMPT.format(question=query)
    
    # Use structured output — LLM MUST return {score: int, reason: str}
    llm = runtime.context.ollama_client.get_langchain_model(temperature=0.0)
    structured_llm = llm.with_structured_output(GuardrailScoring)
    
    response = await structured_llm.ainvoke(guardrail_prompt)
    # response.score: 0-100 (100 = definitely in scope)
    # response.reason: "Query is about transformer architecture in NLP"
    
    return {"guardrail_result": response}

def continue_after_guardrail(state: AgentState, runtime: Runtime[Context]):
    """Routing function: continue or reject based on score threshold."""
    score = state["guardrail_result"].score
    threshold = runtime.context.guardrail_threshold  # default: 50
    
    return "continue" if score >= threshold else "out_of_scope"
```

```
GUARDRAIL PROMPT:
  "Rate this question's relevance to CS/AI/ML research papers on a scale 0-100.
   Score 100 if directly about research papers, algorithms, or methods.
   Score 0 if about cooking, sports, or unrelated topics.
   
   Question: {question}
   
   Return JSON: {score: int, reason: str}"

Example:
  Query: "What is backpropagation?"
  Score: 85  → CONTINUE (CS topic)
  
  Query: "What's the best pizza recipe?"
  Score: 0   → OUT OF SCOPE
  
  Query: "Who won the World Cup?"
  Score: 2   → OUT OF SCOPE
```

### Node 2 — Document Grading

```python
# src/services/agents/nodes/grade_documents_node.py

async def ainvoke_grade_documents_step(state: AgentState, runtime: Runtime[Context]) -> dict:
    """LLM evaluates whether retrieved docs actually answer the question."""
    
    question = get_latest_query(state["messages"])
    context = get_latest_context(state["messages"])   # Retrieved chunks as text
    
    if not context:
        # No docs retrieved → must rewrite query
        return {"routing_decision": "rewrite_query", "grading_results": []}
    
    grading_prompt = GRADE_DOCUMENTS_PROMPT.format(
        context=context,
        question=question,
    )
    
    llm = runtime.context.ollama_client.get_langchain_model(temperature=0.0)
    structured_llm = llm.with_structured_output(GradeDocuments)
    
    grading_response = await structured_llm.ainvoke(grading_prompt)
    # grading_response.binary_score: "yes" or "no"
    # grading_response.reasoning: "The context mentions attention but doesn't explain the mechanism"
    
    is_relevant = grading_response.binary_score == "yes"
    route = "generate_answer" if is_relevant else "rewrite_query"
    
    return {
        "routing_decision": route,
        "grading_results": [GradingResult(
            is_relevant=is_relevant,
            score=1.0 if is_relevant else 0.0,
            reasoning=grading_response.reasoning,
        )],
    }
```

```
GRADE DOCUMENTS PROMPT:
  "You are a grader assessing whether retrieved documents are relevant to the question.
   
   Retrieved documents:
   {context}
   
   Question: {question}
   
   Are the documents relevant? Answer yes or no with reasoning.
   Return JSON: {binary_score: 'yes'|'no', reasoning: str}"
```

### Node 3 — Query Rewriting

```python
# src/services/agents/nodes/rewrite_query_node.py

async def ainvoke_rewrite_query_step(state: AgentState, runtime: Runtime[Context]) -> dict:
    """LLM rewrites the query to improve retrieval."""
    
    original_question = state.get("original_query") or state["messages"][0].content
    current_attempt = state.get("retrieval_attempts", 0)
    
    rewrite_prompt = REWRITE_PROMPT.format(question=original_question)
    
    llm = runtime.context.ollama_client.get_langchain_model(temperature=0.3)
    structured_llm = llm.with_structured_output(QueryRewriteOutput)
    
    result = await structured_llm.ainvoke(rewrite_prompt)
    # result.rewritten_query: improved query
    # result.reasoning: "Added synonyms and domain-specific terms"
    
    return {
        "messages": [HumanMessage(content=result.rewritten_query)],
        "rewritten_query": result.rewritten_query,
    }
```

```
REWRITE PROMPT:
  "You are rewriting a search query to find better research paper results.
   
   Original query: {question}
   
   Improve it by:
   - Adding domain-specific terminology
   - Including synonyms
   - Making it more specific
   - Removing ambiguity
   
   Return JSON: {rewritten_query: str, reasoning: str}"

Example:
  Original: "how does gpt work?"
  Rewritten: "GPT autoregressive language model transformer decoder architecture next token prediction"
```

### Building the LangGraph

```python
# src/services/agents/agentic_rag.py

class AgenticRAGService:
    
    def _build_graph(self):
        """Compile the full LangGraph workflow."""
        
        graph = StateGraph(AgentState)
        
        # ADD NODES (each is an async function)
        graph.add_node("guardrail",        ainvoke_guardrail_step)
        graph.add_node("retrieve",         ainvoke_retrieve_step)
        graph.add_node("grade_documents",  ainvoke_grade_documents_step)
        graph.add_node("rewrite_query",    ainvoke_rewrite_query_step)
        graph.add_node("generate_answer",  ainvoke_generate_answer_step)
        graph.add_node("out_of_scope",     ainvoke_out_of_scope_step)
        
        # ADD EDGES (wiring: what comes after what)
        graph.add_edge(START, "guardrail")
        
        # Conditional edge: guardrail result decides next node
        graph.add_conditional_edges(
            "guardrail",
            continue_after_guardrail,           # routing function
            {
                "continue": "retrieve",          # score ≥ threshold → retrieve
                "out_of_scope": "out_of_scope",  # score < threshold → reject
            }
        )
        
        graph.add_edge("retrieve", "grade_documents")
        
        # Conditional edge: grading decides next node
        graph.add_conditional_edges(
            "grade_documents",
            lambda state, _: state["routing_decision"],
            {
                "generate_answer": "generate_answer",
                "rewrite_query": "rewrite_query",
            }
        )
        
        # After rewrite: try retrieval again
        graph.add_edge("rewrite_query", "retrieve")
        
        # Terminal nodes
        graph.add_edge("generate_answer", END)
        graph.add_edge("out_of_scope", END)
        
        return graph.compile()
    
    async def answer(self, query: str, user_id: str = "anonymous") -> AgenticRAGResult:
        """Run the full agentic RAG pipeline."""
        
        initial_state = {
            "messages": [HumanMessage(content=query)],
            "original_query": query,
            "retrieval_attempts": 0,
            "reasoning_steps": [],
        }
        
        # Run graph — LangGraph handles the state transitions automatically
        result = await self.graph.ainvoke(
            initial_state,
            config={
                "configurable": {
                    "context": Context(
                        opensearch=self.opensearch,
                        ollama=self.ollama,
                        embeddings=self.embeddings,
                        langfuse_tracer=self.langfuse_tracer,
                        model_name=self.graph_config.model,
                        top_k=self.graph_config.top_k,
                        guardrail_threshold=self.graph_config.guardrail_threshold,
                        max_retrieval_attempts=self.graph_config.max_retrieval_attempts,
                    )
                }
            }
        )
        
        return AgenticRAGResult(
            answer=result.get("final_answer", ""),
            rewritten_query=result.get("rewritten_query"),
            retrieval_attempts=result.get("retrieval_attempts", 1),
            grading_results=result.get("grading_results", []),
            guardrail_score=result["guardrail_result"].score if result.get("guardrail_result") else None,
            reasoning_steps=result.get("reasoning_steps", []),
        )
```

---

## 10. RAG Evaluation — End to End

### Why Evaluation is Critical

```
WITHOUT EVALUATION:
  You deploy a RAG system
  Users ask 1,000 questions
  You have no idea if answers are:
    ✗ Accurate (does the LLM answer correctly?)
    ✗ Grounded (is the answer based on the docs, not hallucinated?)
    ✗ Complete (did we retrieve the right docs?)
    ✗ Relevant (does the answer address the question?)

WITH EVALUATION:
  You run RAGAS metrics on your test set
  You get scores for:
    ✓ Faithfulness: 0.87 (87% of claims traceable to retrieved docs)
    ✓ Answer Relevancy: 0.92 (92% of the answer addresses the question)
    ✓ Context Recall: 0.78 (78% of answer-needed info was retrieved)
    ✓ Context Precision: 0.83 (83% of retrieved docs were actually needed)
  
  You know EXACTLY where your RAG system is weak and how to fix it
```

### The 4 RAGAS Metrics Explained

```
METRIC 1: FAITHFULNESS (0.0 - 1.0)
  Question: "Is every claim in the answer supported by the retrieved context?"
  
  Answer: "The attention mechanism has complexity O(n²) and was first proposed in 2017."
  
  Retrieved context: "...self-attention has quadratic complexity in sequence length..."
  
  Claims in answer:
    ✓ "complexity O(n²)" → found in context
    ✗ "first proposed in 2017" → NOT in context (hallucinated!)
  
  Faithfulness = 1/2 = 0.50  ← Low! The date was hallucinated.
  
  WHAT TO FIX: Tighten system prompt → "never state facts not in the context"

─────────────────────────────────────────────────────────────────

METRIC 2: ANSWER RELEVANCY (0.0 - 1.0)
  Question: "Is the answer actually about the question asked?"
  
  Query: "What is BERT?"
  Answer: "BERT was developed by Google in 2018. It uses a transformer encoder architecture
           with bidirectional training via masked language modeling and next sentence prediction."
  
  Bad answer: "Transformers were first introduced in the 'Attention is All You Need' paper
               by Vaswani et al. They use multi-head attention..."
               ← talks about transformers in general, not BERT specifically
  
  Measured by: Generate 5 questions that the answer WOULD answer
  → Good answer: generated questions look like "What is BERT?", "Who made BERT?"
  → Bad answer: generated questions look like "What is a transformer?"
  
  Cosine similarity between original query and generated questions = score
  
  WHAT TO FIX: Ensure prompt instructs model to stay focused on the specific question

─────────────────────────────────────────────────────────────────

METRIC 3: CONTEXT RECALL (0.0 - 1.0)
  Question: "Did we retrieve ALL the information needed to answer correctly?"
  
  Ground truth answer (the perfect answer):
    "BERT uses MLM (Masked Language Modeling) where 15% of tokens are masked,
     and NSP (Next Sentence Prediction) for bidirectional pre-training."
  
  Retrieved context:
    Chunk 1: "...BERT uses Masked Language Modeling..."  ✓
    Chunk 2: "...the model predicts masked tokens..."    ✓
    [NSP information NOT retrieved]                     ✗
  
  Context Recall = 2/3 important facts retrieved = 0.67
  
  WHAT TO FIX: Increase top_k (retrieve more chunks), or improve chunking strategy

─────────────────────────────────────────────────────────────────

METRIC 4: CONTEXT PRECISION (0.0 - 1.0)
  Question: "Were the retrieved documents actually relevant?"
  
  Query: "What is BERT?"
  Retrieved 5 chunks:
    Chunk 1: About BERT architecture            ← relevant ✓
    Chunk 2: About BERT training                ← relevant ✓
    Chunk 3: About GPT (different model)        ← irrelevant ✗
    Chunk 4: About tokenization in general      ← borderline ✗
    Chunk 5: About BERT fine-tuning             ← relevant ✓
  
  Context Precision = 3/5 = 0.60
  
  WHAT TO FIX: Better embeddings, tighter BM25 query, reranking step
```

### Implementation with RAGAS

```python
# evaluation/ragas_evaluation.py

from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_recall,
    context_precision,
)
from datasets import Dataset
import asyncio
from typing import List, Dict

class RAGEvaluator:
    """Runs RAGAS evaluation on your RAG system."""
    
    def __init__(self, rag_service, langfuse_client=None):
        self.rag = rag_service
        self.langfuse = langfuse_client   # Optional: log eval results
    
    async def evaluate_dataset(
        self, 
        test_cases: List[Dict],
        metrics=None,
    ) -> dict:
        """Run RAGAS on a list of test cases.
        
        Each test case:
          {
            "question": "What is the attention mechanism?",
            "ground_truth": "The attention mechanism allows..."  # Human-written ideal answer
          }
        """
        if metrics is None:
            metrics = [faithfulness, answer_relevancy, context_recall, context_precision]
        
        # Run RAG system on each question, collect results
        questions, answers, contexts, ground_truths = [], [], [], []
        
        for tc in test_cases:
            result = await self.rag.answer(tc["question"])
            
            questions.append(tc["question"])
            answers.append(result.answer)
            contexts.append([chunk["chunk_text"] for chunk in result.sources])
            ground_truths.append(tc["ground_truth"])
        
        # Build RAGAS dataset
        dataset = Dataset.from_dict({
            "question": questions,
            "answer": answers,
            "contexts": contexts,
            "ground_truth": ground_truths,
        })
        
        # Run evaluation
        result = evaluate(
            dataset=dataset,
            metrics=metrics,
            llm=self._get_judge_llm(),   # LLM that acts as evaluator
        )
        
        scores = {
            "faithfulness":      result["faithfulness"],
            "answer_relevancy":  result["answer_relevancy"],
            "context_recall":    result["context_recall"],
            "context_precision": result["context_precision"],
        }
        
        # Log to Langfuse if configured
        if self.langfuse:
            self._log_evaluation_to_langfuse(scores, test_cases, answers)
        
        return scores
    
    def _get_judge_llm(self):
        """LLM used by RAGAS to evaluate answers."""
        from langchain_ollama import OllamaLLM
        return OllamaLLM(model="llama3.1", base_url="http://localhost:11434")
```

### Building Your Test Dataset

```python
# evaluation/test_dataset.py
# A test dataset for the arXiv Paper Curator RAG system

TEST_CASES = [
    {
        "question": "What is the attention mechanism in transformers?",
        "ground_truth": (
            "The attention mechanism in transformers computes a weighted sum of values "
            "where the weights are determined by the compatibility between a query and keys. "
            "It allows the model to focus on relevant parts of the input sequence. "
            "Multi-head attention runs h parallel attention functions on d_k/h dimensions each."
        ),
    },
    {
        "question": "What is BERT's pre-training approach?",
        "ground_truth": (
            "BERT uses two pre-training objectives: Masked Language Modeling (MLM) where "
            "15% of tokens are masked and the model predicts them, and Next Sentence Prediction "
            "(NSP) where the model predicts if two sentences are consecutive. This enables "
            "bidirectional training unlike unidirectional models like GPT."
        ),
    },
    {
        "question": "How does RAG reduce hallucination?",
        "ground_truth": (
            "RAG reduces hallucination by providing retrieved documents as context to the LLM. "
            "The model is instructed to answer only from the context, not from parametric memory. "
            "Claims can be traced back to source documents and verified."
        ),
    },
    {
        "question": "What is LoRA fine-tuning?",
        "ground_truth": (
            "LoRA (Low-Rank Adaptation) freezes pre-trained model weights and injects trainable "
            "low-rank matrices into each transformer layer. It drastically reduces trainable "
            "parameters (by 10,000x for GPT-3) while maintaining model quality."
        ),
    },
    # Add 20-50 more test cases for statistical significance
]
```

### Evaluating the Agentic RAG System

The Agentic RAG adds additional evaluation dimensions:

```python
# evaluation/agentic_evaluation.py

class AgenticRAGEvaluator:
    """Evaluates all dimensions of the agentic RAG system."""
    
    async def evaluate_guardrail(self, test_cases: List[Dict]) -> dict:
        """Evaluate guardrail: does it correctly classify in/out of scope?"""
        
        # Test cases with known labels
        guardrail_tests = [
            {"query": "What is backpropagation?",       "expected": "in_scope"},
            {"query": "Best pizza recipe",               "expected": "out_of_scope"},
            {"query": "Explain transformers",            "expected": "in_scope"},
            {"query": "Who won the Super Bowl?",         "expected": "out_of_scope"},
            {"query": "What is gradient descent?",       "expected": "in_scope"},
            {"query": "Stock market predictions",        "expected": "out_of_scope"},
        ]
        
        correct = 0
        for tc in guardrail_tests:
            result = await self.agentic_rag.answer(tc["query"])
            predicted = "in_scope" if result.guardrail_score >= 50 else "out_of_scope"
            if predicted == tc["expected"]:
                correct += 1
        
        return {
            "guardrail_accuracy": correct / len(guardrail_tests),
            "total_tests": len(guardrail_tests),
        }
    
    async def evaluate_query_rewriting(self, test_cases: List[Dict]) -> dict:
        """Evaluate query rewriting: do rewritten queries retrieve better docs?"""
        
        improvements = []
        
        for tc in test_cases:
            # Get results with original query
            original_result = await self.run_retrieval(tc["original_query"])
            original_ndcg = self._calculate_ndcg(original_result, tc["relevant_arxiv_ids"])
            
            # Get rewritten query from the agent
            agent_result = await self.agentic_rag.answer(tc["original_query"])
            
            if agent_result.rewritten_query:
                rewritten_result = await self.run_retrieval(agent_result.rewritten_query)
                rewritten_ndcg = self._calculate_ndcg(rewritten_result, tc["relevant_arxiv_ids"])
                
                improvements.append(rewritten_ndcg - original_ndcg)
        
        return {
            "avg_ndcg_improvement": sum(improvements) / len(improvements) if improvements else 0,
            "queries_rewritten": len(improvements),
        }
    
    def _calculate_ndcg(self, retrieved_docs: List[dict], relevant_ids: List[str]) -> float:
        """Calculate Normalized Discounted Cumulative Gain."""
        # DCG = Σ (relevance_i / log2(rank + 1))
        dcg = 0.0
        for rank, doc in enumerate(retrieved_docs, 1):
            relevance = 1 if doc["arxiv_id"] in relevant_ids else 0
            dcg += relevance / (rank + 1).bit_length()  # log2 approximation
        
        # Ideal DCG (if all relevant docs were ranked first)
        ideal_dcg = sum(1 / (rank + 1).bit_length() for rank in range(1, len(relevant_ids) + 1))
        
        return dcg / ideal_dcg if ideal_dcg > 0 else 0.0
```

### Running a Full Evaluation Pipeline

```bash
# Run all evaluations

# 1. Standard RAGAS metrics
uv run python -m evaluation.run_ragas \
  --test-cases evaluation/test_cases.json \
  --output evaluation/results/ragas_$(date +%Y%m%d).json

# 2. Agentic-specific metrics  
uv run python -m evaluation.run_agentic_eval \
  --test-cases evaluation/test_cases.json \
  --output evaluation/results/agentic_$(date +%Y%m%d).json

# 3. Compare standard RAG vs agentic RAG
uv run python -m evaluation.compare \
  --standard evaluation/results/ragas_*.json \
  --agentic evaluation/results/agentic_*.json
```

### Interpreting Scores and Taking Action

```
FAITHFULNESS < 0.80 → LLM is hallucinating
  Action: Strengthen system prompt: "ONLY use information from the context documents"
          Add a post-processing check that validates claims against retrieved chunks

ANSWER RELEVANCY < 0.80 → Answers drift off-topic
  Action: Add "Focus ONLY on the question asked" to system prompt
          Reduce max_tokens to prevent rambling

CONTEXT RECALL < 0.70 → Missing key information in retrieval
  Action: Increase top_k from 5 to 10
          Try smaller chunk_size (300 words) to be more specific
          Improve embeddings model

CONTEXT PRECISION < 0.70 → Retrieving irrelevant chunks
  Action: Add reranking step (cross-encoder) after initial retrieval
          Tune BM25 field boosts
          Switch from top_k fixed to threshold-based retrieval

GUARDRAIL ACCURACY < 0.85 → Guardrail misclassifying
  Action: Adjust threshold (default 50, try 60 or 40)
          Add domain-specific examples to the guardrail prompt
          Use a stronger model for scoring

QUERY REWRITING NDCG IMPROVEMENT < 0 → Rewriting is making things WORSE
  Action: Lower temperature on rewrite node (0.1 instead of 0.3)
          Add more specific examples to rewrite prompt
          Limit rewriting to queries that are vague (< 5 words)
```

---

## 11. Project Structure Deep Dive

```
production-agentic-rag-course-main/
│
├── src/                                    ← All application code
│   ├── main.py                             ← FastAPI app entry point, router registration
│   ├── config.py                           ← All config via Pydantic Settings
│   ├── database.py                         ← SQLAlchemy engine + session factory
│   ├── dependencies.py                     ← FastAPI dependency injection (DI)
│   ├── middlewares.py                      ← CORS, logging, timing middleware
│   ├── exceptions.py                       ← Custom exception classes + handlers
│   │
│   ├── models/                             ← Database models (SQLAlchemy ORM)
│   │   └── paper.py                        ← Paper table definition
│   │
│   ├── schemas/                            ← Data validation (Pydantic)
│   │   ├── api/
│   │   │   ├── ask.py                      ← AskRequest, AskResponse schemas
│   │   │   ├── search.py                   ← SearchRequest, SearchResponse
│   │   │   └── health.py                   ← HealthResponse
│   │   ├── arxiv/paper.py                  ← arXiv paper data structure
│   │   ├── embeddings/jina.py              ← Jina API request/response
│   │   ├── indexing/models.py              ← TextChunk, ChunkMetadata
│   │   └── pdf_parser/models.py            ← ParsedDocument, Section
│   │
│   ├── repositories/                       ← Database access layer (CRUD)
│   │   └── paper.py                        ← PaperRepository (get, upsert, list)
│   │
│   ├── routers/                            ← API endpoint handlers
│   │   ├── ping.py                         ← GET /health
│   │   ├── ask.py                          ← POST /api/v1/ask + /stream
│   │   ├── agentic_ask.py                  ← POST /api/v1/agentic-ask
│   │   ├── search.py                       ← POST /api/v1/search (BM25)
│   │   └── hybrid_search.py               ← POST /api/v1/hybrid-search
│   │
│   ├── services/                           ← Business logic
│   │   ├── metadata_fetcher.py             ← Main pipeline orchestrator
│   │   ├── opensearch/
│   │   │   ├── client.py                   ← OpenSearch queries (search, index)
│   │   │   ├── query_builder.py            ← BM25 + hybrid query construction
│   │   │   ├── index_config_hybrid.py      ← Index mapping with vector field
│   │   │   └── factory.py                  ← Singleton client creation
│   │   ├── embeddings/
│   │   │   ├── jina_client.py              ← Jina AI API client
│   │   │   └── factory.py                  ← Client initialization
│   │   ├── indexing/
│   │   │   ├── text_chunker.py             ← Section-aware word-based chunking
│   │   │   ├── hybrid_indexer.py           ← Orchestrates chunk + embed + index
│   │   │   └── factory.py
│   │   ├── ollama/
│   │   │   ├── client.py                   ← Ollama API (generate, stream)
│   │   │   └── prompts/rag_system.txt       ← System prompt (editable without code)
│   │   ├── langfuse/
│   │   │   ├── client.py                   ← Raw Langfuse SDK wrapper
│   │   │   ├── tracer.py                   ← RAGTracer (context managers per step)
│   │   │   └── factory.py
│   │   ├── cache/
│   │   │   └── service.py                  ← Redis exact-match cache
│   │   ├── agents/                         ← Agentic RAG (Week 7)
│   │   │   ├── agentic_rag.py              ← AgenticRAGService (builds graph)
│   │   │   ├── state.py                    ← AgentState TypedDict
│   │   │   ├── context.py                  ← Context (dependency injection)
│   │   │   ├── config.py                   ← GraphConfig (thresholds, top_k, etc)
│   │   │   ├── models.py                   ← GuardrailScoring, GradeDocuments
│   │   │   ├── prompts.py                  ← All agent prompts in one place
│   │   │   ├── tools.py                    ← create_retriever_tool
│   │   │   └── nodes/
│   │   │       ├── guardrail_node.py       ← Domain validation
│   │   │       ├── retrieve_node.py        ← OpenSearch hybrid search
│   │   │       ├── grade_documents_node.py ← LLM relevance judgment
│   │   │       ├── rewrite_query_node.py   ← LLM query improvement
│   │   │       ├── generate_answer_node.py ← Final answer generation
│   │   │       ├── out_of_scope_node.py    ← Rejection message
│   │   │       └── utils.py                ← get_latest_query, get_latest_context
│   │   └── telegram/
│   │       ├── bot.py                      ← Telegram Bot handler
│   │       └── factory.py
│   │
│   ├── db/                                 ← Database abstraction
│   │   ├── interfaces/
│   │   │   ├── base.py                     ← Abstract repository interface
│   │   │   └── postgresql.py               ← PostgreSQL implementation
│   │   └── factory.py
│   │
│   └── gradio_app.py                       ← Gradio chat interface
│
├── notebooks/                              ← Weekly Jupyter notebooks
│   ├── week1/week1_setup.ipynb
│   ├── week2/week2_arxiv_integration.ipynb
│   ├── week3/week3_opensearch.ipynb
│   ├── week4/week4_hybrid_search.ipynb
│   ├── week5/week5_complete_rag_system.ipynb
│   ├── week6/week6_cache_testing.ipynb
│   └── week7/week7_agentic_rag.ipynb
│
├── airflow/                                ← Workflow orchestration
│   └── dags/
│       └── arxiv_ingestion_dag.py          ← Daily paper fetch + index DAG
│
├── tests/                                  ← Test suite
│   ├── unit/                               ← Unit tests (no services needed)
│   └── integration/                        ← Integration tests (services running)
│
├── compose.yml                             ← Docker Compose (all 9 services)
├── Dockerfile                              ← FastAPI app container
├── Makefile                                ← Developer commands (make start, test, etc)
└── pyproject.toml                          ← Python dependencies (uv managed)
```

---

## 12. Request Lifecycle A to Z

Tracing one user question through the FULL agentic RAG system:

```
USER TYPES: "What is RLHF and how is it used in LLM training?"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 1: HTTP Request arrives (t=0ms)
  POST /api/v1/agentic-ask
  Body: {"query": "What is RLHF and how is it used in LLM training?"}
  
  FastAPI router: validates body via Pydantic schema AskRequest
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 2: Cache check (t=2ms)
  Redis: GET rag:v1:a7f3b...
  Result: CACHE MISS (first time asking this question)
  → proceed with full pipeline
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 3: LangGraph starts (t=5ms)
  Initial state = {messages: [HumanMessage("What is RLHF?")], ...}
  Graph begins at START node
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 4: GUARDRAIL NODE (t=5ms → t=890ms)
  Prompt: "Rate relevance to CS/AI/ML research: 'What is RLHF?'"
  Ollama (llama3.1) thinks...
  Response: {score: 95, reason: "RLHF is a key ML training technique"}
  Decision: 95 ≥ 50 threshold → CONTINUE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 5: RETRIEVE NODE (t=890ms → t=1.1s)
  
  5a. Embed query via Jina AI API:
      Input: "What is RLHF and how is it used in LLM training?"
      Output: [0.023, -0.451, 0.821, ...] (1024-dim vector)
      Duration: 145ms
  
  5b. Hybrid search in OpenSearch:
      BM25 query: matches "RLHF", "reinforcement learning", "human feedback"
      KNN query: finds semantically similar chunks about reward models, PPO
      RRF fusion combines both lists
      Returns: 5 best chunks from 3 papers
      Duration: 65ms
  
  State updated: retrieved_docs = [chunk1, chunk2, chunk3, chunk4, chunk5]
  Context string: "Chunk 1: RLHF trains reward models... Chunk 2: PPO algorithm..."
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 6: GRADE DOCUMENTS NODE (t=1.1s → t=2.0s)
  Prompt: "Are these documents relevant to: 'What is RLHF?'"
  Context shown to LLM grader: [5 retrieved chunks]
  
  Ollama (llama3.1) evaluates...
  Response: {binary_score: "yes", reasoning: "Context explicitly covers RLHF, reward modeling, PPO..."}
  Decision: relevant → route to "generate_answer"
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 7: GENERATE ANSWER NODE (t=2.0s → t=6.5s)
  Prompt structure:
    [system prompt from rag_system.txt]
    
    RETRIEVED CONTEXT:
    [Document 1] Paper: "Training language models to follow instructions..."
    Content: "RLHF consists of three phases: SFT, reward model training, and PPO..."
    
    [Document 2] Paper: "Learning to summarize with human feedback"
    Content: "The reward model is trained on human preference comparisons..."
    
    [... 3 more documents ...]
    
    USER QUESTION: What is RLHF and how is it used in LLM training?
  
  Ollama streams response token by token:
  "RLHF (Reinforcement Learning from Human Feedback) is a training technique..."
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 8: Response returned (t=6.5s)
  {
    "answer": "RLHF (Reinforcement Learning from Human Feedback) consists of...",
    "guardrail_score": 95,
    "retrieval_attempts": 1,
    "rewritten_query": null,  ← query was good on first try
    "sources": [
      {"arxiv_id": "2203.02155", "title": "Training language models to follow instructions..."},
      {"arxiv_id": "2009.01325", "title": "Learning to summarize with human feedback"}
    ],
    "reasoning_steps": [
      "Guardrail: in-scope (score=95)",
      "Retrieved 5 chunks from 3 papers",
      "Grading: relevant (documents contain RLHF information)",
      "Generated answer from context"
    ]
  }
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 9: Cache store (async, t=6.5s)
  Redis SET rag:v1:a7f3b... (JSON result, TTL=3600s)
  
  Next time same question asked → STEP 2 hits cache, returns in 5ms
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 10: Langfuse trace complete (async, t=6.5s)
  Full trace tree stored in Langfuse:
    rag_request (6.5s total)
    ├── guardrail_validation (885ms, score=95)
    ├── query_embedding (145ms)
    ├── search_retrieval (65ms, 5 chunks, 3 papers)
    ├── document_grading (895ms, relevant=true)
    └── llm_generation (4.5s, model=llama3.1)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

WHAT HAPPENS WITH A BAD QUERY? (demonstrates query rewriting)
  User: "tell me about the thing with attention"
  
  Step 4 (Guardrail): score=72 → continue (vague but CS topic)
  Step 5 (Retrieve): BM25 for "thing" matches nothing useful, 
                     vector search returns generic results
  Step 6 (Grade): "Documents are not relevant to the vague query" → rewrite
  Step 7 (Rewrite): LLM rewrites → "attention mechanism self-attention transformer architecture"
  Step 5 again (Retrieve): Now finds "Attention is All You Need" chunks ✓
  Step 6 again (Grade): "Documents relevant" → generate
  Step 7 (Generate): Clear answer about attention mechanism
```

---

## 13. Common RAG Failure Modes

```
FAILURE 1: Retrieval Failure (most common)
  Symptom: Answer says "I don't have information" but the paper exists
  Causes:
    - Query uses different vocabulary than indexed text
      ("neural net" vs "artificial neural network")
    - Chunk size too large → relevant sentence diluted in 600-word chunk
    - BM25 only → can't find semantic synonyms
  Fix: Use hybrid search, smaller chunks, query rewriting

FAILURE 2: Hallucination
  Symptom: LLM answers confidently with wrong facts not in context
  Causes:
    - Weak system prompt doesn't enforce context-only answers
    - Retrieved docs are marginally relevant → LLM fills gaps with training knowledge
    - High temperature setting (0.7+) → more creative but less faithful
  Fix: Stronger system prompt, lower temperature (0.1), faithfulness eval

FAILURE 3: Context Overflow
  Symptom: LLM ignores information from early in the prompt ("lost in the middle")
  Causes:
    - Too many chunks (top_k=20, prompt becomes 10,000 tokens)
    - Most LLMs attention weakens in the middle of very long contexts
  Fix: Reduce top_k to 5-7, use reranking to put best chunks first

FAILURE 4: Stale Data
  Symptom: System answers about old papers, doesn't know about recent work
  Causes:
    - Airflow DAG not running (check Airflow UI for failed runs)
    - arXiv API rate limit hit → papers not fetched
    - PDF parse failure → papers stored without text → not indexed
  Fix: Monitor DAG runs, add alerts for failed ingestion

FAILURE 5: Out-of-Domain Confidence
  Symptom: RAG answers questions about cooking, sports, etc.
  Causes:
    - No guardrail → any query goes through the pipeline
    - Guardrail threshold too low
  Fix: Add guardrail node (Week 7), tune threshold

FAILURE 6: Slow Response
  Symptom: Users wait 10-15 seconds per query
  Causes:
    - No caching → every identical query reruns the full pipeline
    - Large model (Llama3.1:70b) on CPU-only machine
    - Large chunks → long prompts → slow generation
  Fix: Redis cache, use smaller model (llama3.1:8b), reduce chunk size
```

---

## 14. Cheatsheet

### Quick Commands

```bash
# Setup
cp .env.example .env
uv sync
docker compose up --build -d

# Access
curl http://localhost:8000/health            # Check API
open http://localhost:8000/docs             # Interactive API docs
open http://localhost:7861                  # Gradio chat UI
open http://localhost:3000                  # Langfuse tracing
open http://localhost:8080                  # Airflow DAGs
open http://localhost:5601                  # OpenSearch Dashboards

# Test RAG
curl -X POST http://localhost:8000/api/v1/ask \
  -H "Content-Type: application/json" \
  -d '{"query": "What is attention mechanism?"}'

# Test Agentic RAG
curl -X POST http://localhost:8000/api/v1/agentic-ask \
  -H "Content-Type: application/json" \
  -d '{"query": "How does RLHF work?"}'

# Development
make start        # Start all services
make health       # Check all services
make test         # Run tests
make test-cov     # Tests with coverage
make lint         # Lint + type check
make stop         # Stop services

# Notebooks (one per week)
uv run jupyter notebook notebooks/week5/week5_complete_rag_system.ipynb
```

### Key Files to Know

| File | What It Does |
|------|-------------|
| `src/config.py` | All configuration — change behavior without touching other files |
| `src/main.py` | App entry point — see all registered routes |
| `src/services/agents/agentic_rag.py` | Full LangGraph workflow |
| `src/services/agents/nodes/` | One file per agent node |
| `src/services/agents/prompts.py` | All LLM prompts in one place |
| `src/services/indexing/text_chunker.py` | Chunking strategy |
| `src/services/opensearch/query_builder.py` | BM25 + hybrid queries |
| `src/services/ollama/prompts/rag_system.txt` | System prompt (edit freely) |
| `airflow/dags/arxiv_ingestion_dag.py` | Daily data pipeline |
| `compose.yml` | All Docker services |

### Technology Stack

| Layer | Technology | Why Chosen |
|-------|-----------|------------|
| API | FastAPI | Async, auto-docs, type-safe |
| Database | PostgreSQL 16 | Reliable, JSONB for flexible schemas |
| Search | OpenSearch 2.19 | BM25 + KNN in one engine, free/OSS |
| Embeddings | Jina v3 (1024-dim) | SOTA quality, free tier available |
| LLM | Ollama (local) | Zero cost, privacy, no rate limits |
| Caching | Redis | Sub-millisecond, battle-tested |
| Tracing | Langfuse | RAG-native metrics, self-hostable |
| Orchestration | LangGraph | State-based, visual graph, reliable |
| Pipeline | Apache Airflow 3.0 | Scheduling, retries, monitoring |
| PDF Parsing | Docling | Scientific documents, handles LaTeX |

### RAGAS Score Reference

| Score | Meaning | Action |
|-------|---------|--------|
| 0.90-1.0 | Excellent | Monitor, no changes needed |
| 0.80-0.90 | Good | Minor prompt tuning |
| 0.70-0.80 | Acceptable | Investigate and improve |
| 0.60-0.70 | Needs work | Major changes required |
| < 0.60 | Poor | Rethink approach |

---

## 15. Summary and Conclusion

### What This Project Teaches

This is not a toy RAG system. It is a **complete production implementation** that teaches:

**Infrastructure:** How real AI systems are deployed — Docker Compose, service orchestration, health checks, environment configuration, async APIs.

**Data Engineering:** How automated pipelines work — Airflow DAGs, rate-limited API clients, scientific PDF parsing, idempotent upserts, failure handling.

**Search Fundamentals:** Why BM25 matters — IDF/TF math, index mappings, field boosting, filters. Understanding this makes you a better engineer than those who only use vector search.

**Hybrid Retrieval:** How state-of-the-art retrieval works — RRF fusion combines the best of keyword and semantic search without score normalization headaches.

**Production LLM Integration:** Streaming SSE, optimized prompts, local models for privacy, structured outputs for agent decision nodes.

**Observability:** How to actually understand your system — Langfuse traces make every LLM call inspectable, not a black box.

**Caching:** Simple but powerful — exact-match Redis caching with graceful fallback delivers massive speedups with minimal complexity.

**Agentic Systems:** Real LangGraph usage — state management, conditional edges, node composition, dependency injection via Context.

**Evaluation:** The professional difference — RAGAS metrics give you objective scores so you can make data-driven improvements instead of guessing.

### The 7-Week Learning Path

```
Week 1: Build the foundation (Docker, FastAPI, PostgreSQL, OpenSearch, Ollama)
Week 2: Fill it with data (arXiv API, Docling PDF parser, Airflow automation)
Week 3: Make it searchable (BM25 keyword search — learn WHY before you skip to AI)
Week 4: Make it smart (Jina embeddings, hybrid RRF search)
Week 5: Make it answer (RAG pipeline, LLM integration, streaming)
Week 6: Make it production (Langfuse tracing, Redis caching)
Week 7: Make it agentic (LangGraph, guardrail, grading, rewriting, Telegram)

AFTER WEEK 7: Add evaluation (RAGAS) to measure and improve quality continuously
```

### What to Build Next

```
EXTENDING THIS PROJECT:
  1. Add RAGAS evaluation notebook with 50+ test cases
  2. Implement reranking (cross-encoder after initial retrieval)
  3. Add multi-modal support (retrieve from paper figures/tables)
  4. Build a UI that shows reasoning_steps from agentic RAG
  5. Add A/B testing: standard RAG vs agentic RAG on same queries

APPLYING THESE SKILLS:
  Legal: Index company contracts, answer "what does clause 5.3 say about termination?"
  Medical: Index clinical studies, answer drug interaction questions
  Enterprise: Index documentation, answer "how do I configure X?"
  Finance: Index earnings reports, answer "what was Q3 revenue growth?"
```

### The Core Insight

The difference between a tutorial RAG and production RAG is not the RAG algorithm itself — that part is simple. The difference is everything around it: **how data gets in, how answers get traced, how failures get recovered from, how quality gets measured**.

This project builds all of that. By the end, you understand not just "how to do RAG" but **how AI systems are actually built and operated in production**.

---

*This explanation covers every component of the `production-agentic-rag-course-main` project. All code examples are drawn from the actual source files in the project. Start with Week 1 and build incrementally — each week's code builds on the previous week.*
