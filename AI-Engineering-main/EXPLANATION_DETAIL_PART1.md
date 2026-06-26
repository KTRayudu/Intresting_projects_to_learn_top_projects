# AI Engineering Bootcamp — Complete Beginner's Guide
# PART 1: FOUNDATIONS (Modules 01–10)

**For:** Complete beginners with zero AI/ML background  
**Goal:** Understand every concept, tool, and line of code  
**Style:** Plain English first → technical explanation → actual code  

---

## TABLE OF CONTENTS — PART 1

- [What Is AI Engineering?](#what-is-ai-engineering)
- [Module 01 — Prompt Engineering and Vibe Checking](#module-01)
- [Module 02 — Embeddings and RAG Basics](#module-02)
- [Module 03 — End-to-End RAG Deployment](#module-03)
- [Module 04 — Production RAG with LangChain and LangGraph](#module-04)
- [Module 05 — Our First Agent with LangGraph](#module-05)
- [Module 06 — Multi-Agent with LangGraph](#module-06)
- [Module 07 — Synthetic Data Generation and LangSmith](#module-07)
- [Module 08 — Evaluating RAG with RAGAS](#module-08)
- [Module 09 — Fine-tuning Embeddings](#module-09)
- [Module 10 — Fine-tuning a Reasoning Model](#module-10)

---

## WHAT IS AI ENGINEERING?

Before diving into modules, understand what this entire bootcamp is about.

### The Big Picture

Think of a regular software engineer — they build apps using databases, APIs, servers.  
**AI Engineering** is the same idea but with **Large Language Models (LLMs)** like ChatGPT, Claude, or Llama as the core component.

**The challenge:** LLMs alone are not enough for real products.

```
PROBLEM 1: LLMs hallucinate (make things up confidently)
PROBLEM 2: LLMs don't know your private company data
PROBLEM 3: LLMs cost money — need to use them efficiently
PROBLEM 4: LLMs need monitoring, evaluation, improvement over time
PROBLEM 5: LLMs need to take actions (call APIs, search, etc.)
```

**AI Engineering** is the discipline of solving all five problems above.

### The Two Phases

```
┌─────────────────────────────────────────────────────────────────┐
│                    AI ENGINEERING LIFECYCLE                     │
│                                                                 │
│  PHASE 1: PROTOTYPING              PHASE 2: PRODUCTIONIZING     │
│  ─────────────────────             ────────────────────────     │
│  Prompt Engineering                Evaluating RAG and Agents    │
│  RAG Applications                  Improving Search Pipelines   │
│  Agents and Multi-Agents           Monitoring Production KPIs   │
│  Fine-Tuning LLMs                  Setting up Inference Servers │
│  Deploying Prototypes              Scalable Production Infra    │
│                                                                 │
│  Modules 01-10                     Modules 13-32               │
└─────────────────────────────────────────────────────────────────┘
```

**Prototyping** = "Can we make it work?"  
**Productionizing** = "Can we make it work reliably at scale for thousands of users?"

### The Full Learning Path

```
Module 01: Prompt Engineering     ← Talk to the LLM effectively
Module 02: Embeddings + RAG       ← Teach LLM about YOUR data
Module 03: Deploy RAG             ← Ship it to users
Module 04: Production RAG         ← Use proper frameworks (LangChain)
Module 05: First Agent            ← LLM that takes actions
Module 06: Multi-Agent            ← Multiple LLMs working together
Module 07: Synthetic Data         ← Auto-generate test cases
Module 08: RAGAS Evaluation       ← Measure quality rigorously
Module 09: Fine-tune Embeddings   ← Specialize search for your domain
Module 10: Fine-tune Reasoning    ← Make LLM smarter at your tasks
         ↓
Module 13: Advanced Retrieval     ← Better search strategies
Module 16: LLMOps                 ← Monitor and operate in production
Module 17: On-Prem Agents         ← Run everything locally (no cloud)
Module 18: Quantization           ← Run models cheaply on small GPUs
         ↓
Modules 21-27: Swirl AI tracks    ← Full production pipelines
Module 28: LLM Engineering        ← Deep model understanding
Module 32: arXiv Curator          ← Complete production system (7 phases)
```

---

<a name="module-01"></a>
## MODULE 01 — Prompt Engineering and Vibe Checking

**Session name:** "Introduction and Vibe Check"  
**Key skill:** Talk to an LLM effectively; quickly check if your app works

### What Is an LLM?

An LLM (Large Language Model) is a program trained on billions of text documents. It learned patterns in language so well that it can complete sentences, answer questions, write code, and more.

```
You type:  "The capital of France is"
LLM says:  "Paris."

You type:  "Write Python to reverse a string"
LLM says:  "def reverse(s): return s[::-1]"
```

The LLM doesn't "know" things like humans. It **predicts the most likely next word** based on its training.

### What Is Prompt Engineering?

A **prompt** is the text you send to the LLM. **Prompt Engineering** = writing prompts that reliably get the results you want.

**Bad prompt:**
```
Tell me about AI.
```

**Good prompt:**
```
You are an expert AI tutor explaining concepts to a complete beginner 
with no technical background. Explain Artificial Intelligence in 3 
bullet points using simple everyday analogies. Avoid all jargon.
```

The good prompt provides:
- A **role** ("expert AI tutor")
- **Context** about the audience ("complete beginner")
- **Specific format** (3 bullet points, analogies)
- **Constraint** (avoid jargon)

### The Anatomy of a Prompt

```
┌─────────────────────────────────────────────────────────┐
│                    PROMPT STRUCTURE                      │
│                                                         │
│  SYSTEM PROMPT  (sets behavior)                         │
│  ─────────────────────────────                          │
│  "You are a customer service agent for AcmeCorp.        │
│   Only answer questions about our products.             │
│   Be friendly and concise."                             │
│                                                         │
│  USER MESSAGE   (the question)                          │
│  ──────────────────────────                             │
│  "What is your return policy?"                          │
│                                                         │
│  ASSISTANT RESPONSE  (LLM generates this)              │
│  ────────────────────────────────────────               │
│  "Our return policy allows returns within 30 days..."   │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### Prompt Engineering Techniques

#### 1. Zero-Shot — Ask Without Examples
```
Classify this review as POSITIVE or NEGATIVE:
"The acting was terrible and the plot made no sense."
```

#### 2. Few-Shot — Give Examples First
```
Classify reviews as POSITIVE or NEGATIVE:

Review: "Amazing performances!" → POSITIVE
Review: "Boring and slow."     → NEGATIVE
Review: "Best film ever!"      → POSITIVE

Review: "I walked out after 20 minutes." → ???
```
The LLM learns the pattern from examples and applies it.

#### 3. Chain-of-Thought — Ask to Reason Step by Step
```
Question: If a store has 3 apples and buys 5 more, then gives 2 away, 
how many remain?

Think step by step before giving your final answer.
```

Without "think step by step": LLM might say "6" (guessing 3+5-2 blindly).  
With it: LLM works through → 3+5=8, then 8-2=6. Correct!

#### 4. Role Prompting
```
You are a Socratic philosopher. When asked any question, respond only 
with a deeper question that leads the asker to discover the answer themselves.
```

### What Is "Vibe Checking"?

"Vibe checking" = quick, informal evaluation of your LLM app. Not rigorous — just: "Does it completely fail at basic things?"

**The 5 standard vibe check questions used in this module:**

| Question | What It Tests |
|----------|---------------|
| "Explain OOP to a complete beginner" | Basic explanation capability |
| "Summarize this paragraph..." | Summarization |
| "Write a 100-word story about a robot finding friendship" | Creative writing |
| "If packs have 4 apples/3 oranges, how many packs to get 12/9?" | Math reasoning |
| "Rewrite this in a professional, formal tone" | Style transformation |

**Limitations of vibe checking (discussed in class):**
- Not comprehensive — misses edge cases
- Subjective — "good" varies by person
- Not reproducible — same question, different outputs
- Not measurable — no number to track improvement

That's why Modules 07 and 08 introduce rigorous evaluation.

### The Assignment: Build a Chatbot with Chainlit

**Chainlit** = Python library for building chat interfaces (like ChatGPT's UI) in minutes.

```python
import chainlit as cl
from openai import OpenAI

client = OpenAI()  # reads OPENAI_API_KEY from environment

@cl.on_message
async def main(message: cl.Message):
    # This function runs every time user sends a message
    # message.content = the text the user typed
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",       # cheap, fast model for development
        messages=[
            {
                "role": "system",
                "content": "You are a helpful assistant."
            },
            {
                "role": "user",
                "content": message.content  # user's actual message
            }
        ]
    )
    
    # Extract text from API response and send it back to UI
    answer = response.choices[0].message.content
    await cl.Message(content=answer).send()
```

**Every line explained:**

| Line | What It Does |
|------|-------------|
| `@cl.on_message` | Decorator: run this function when user sends a message |
| `async def main` | Async = can wait for API without freezing the whole program |
| `message: cl.Message` | Type hint: message is a Chainlit Message object |
| `client.chat.completions.create(...)` | Call OpenAI API to generate a response |
| `model="gpt-4o-mini"` | Use GPT-4o mini (cheap: ~$0.15/million tokens) |
| `messages=[...]` | Conversation history in OpenAI's required format |
| `response.choices[0].message.content` | Extract the text from the API response |
| `await cl.Message(...).send()` | Send the response back to the chat UI |

### How to Run Locally

```bash
# 1. Install dependencies
pip install chainlit openai

# 2. Set API key (on Mac/Linux)
export OPENAI_API_KEY="sk-your-key-here"

# 3. Run the app
chainlit run app.py

# 4. Open browser at http://localhost:8000
```

### Key Takeaways — Module 01

```
┌─────────────────────────────────────────────────────┐
│              MODULE 01 SUMMARY                      │
│                                                     │
│  LLM = predicts next word (trained on internet)    │
│  Prompt = instruction you send to LLM              │
│  Good prompt = role + context + format + constraint│
│  Few-shot > zero-shot for pattern tasks            │
│  Chain-of-thought improves math/reasoning          │
│  Vibe check = quick sanity test (not rigorous)     │
│  Chainlit = fast Python chat UI library            │
└─────────────────────────────────────────────────────┘
```

---

<a name="module-02"></a>
## MODULE 02 — Embeddings and RAG Basics

**Session name:** "Embeddings and RAG"  
**Key skill:** Teach the LLM about your own private documents

### The Core Problem

LLMs were trained up to a certain date and on public data only. They know nothing about:
- Your company's internal documents
- Events after their training cutoff
- Your specialized domain knowledge

**Solution: RAG (Retrieval Augmented Generation)**

### What Are Embeddings?

An **embedding** is a list of numbers (called a vector) that represents the *meaning* of a piece of text.

```
"I love cats"      → [0.12, -0.45,  0.78,  0.23, -0.91, ...]  (1536 numbers)
"I adore kittens"  → [0.11, -0.44,  0.77,  0.24, -0.90, ...]  (very similar!)
"I hate rainy days"→ [0.12, -0.45,  0.79, -0.80,  0.15, ...]  (different)
"Quantum physics"  → [-0.90, 0.33, -0.12,  0.67,  0.44, ...]  (very different)
```

**Key insight:** Sentences with **similar meaning** produce **similar numbers**.

Think of it like GPS coordinates:
- New York [40.7, -74.0] and Boston [42.3, -71.0] → close
- New York [40.7, -74.0] and Tokyo [35.6, 139.6] → far
- Embeddings work the same way, but for meaning instead of geography

### Measuring Similarity: Cosine Similarity

The most common way to measure how similar two vectors are:

```
"cat" vector:      →→→  (pointing right)
"kitten" vector:   →→↗  (almost same direction)
"car" vector:      ↑↑↑  (very different direction)

cosine_sim("cat", "kitten") = 0.95  (nearly identical direction)
cosine_sim("cat", "car")    = 0.20  (very different direction)

Formula: similarity = (A · B) / (|A| × |B|)
where A·B = dot product, |A| = length of vector A
```

Math simplified:
- **1.0** = pointing in exact same direction = identical meaning
- **0.0** = pointing at 90° = unrelated
- **-1.0** = pointing opposite = opposite meaning

### What Is a Vector Database?

A vector database stores embeddings and lets you **find the most similar ones quickly**.

```
VECTOR DATABASE CONTENTS:
────────────────────────────────────────────────────────────
ID  │ Original Text                    │ Embedding (vector)
────────────────────────────────────────────────────────────
 1  │ "Refunds processed in 5-7 days"  │ [0.12, -0.45, ...]
 2  │ "Returns accepted within 30 days"│ [0.13, -0.46, ...]
 3  │ "Contact support at support@..."  │ [-0.88, 0.33, ...]
 4  │ "Our CEO founded company in 2005" │ [-0.71, 0.12, ...]
────────────────────────────────────────────────────────────

USER ASKS: "How do I get a refund?"
QUERY VECTOR: [0.11, -0.44, ...]

RESULT: IDs 1 and 2 are most similar (cosine similarity ~0.95)!
        IDs 3 and 4 are not similar at all.
```

### What Is RAG? The Three Steps

```
┌──────────────────────────────────────────────────────────────────┐
│                          RAG PIPELINE                            │
│                                                                  │
│  STEP 1: RETRIEVAL                                               │
│  User asks: "What is the refund policy?"                         │
│  → Embed the question into a vector                              │
│  → Search vector DB for similar document chunks                  │
│  → Get top 3-5 most relevant chunks back                        │
│                                                                  │
│  STEP 2: AUGMENTATION                                            │
│  → Take retrieved chunks + original question                     │
│  → Build a new prompt: "Use this context: [chunk1][chunk2]...    │
│     Answer this question: What is the refund policy?"            │
│                                                                  │
│  STEP 3: GENERATION                                              │
│  → Send augmented prompt to LLM                                  │
│  → LLM reads the context (info it didn't have before!)          │
│  → LLM answers based on YOUR documents                           │
│  → "Based on our policy, refunds are accepted within 30 days"   │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### The `aimakerspace` Custom Library

This module ships a hand-built library (in `02_Embeddings_and_RAG/aimakerspace/`) to teach the concepts without hiding them behind abstractions.

#### `vectordatabase.py` — A Vector Database From Scratch

```python
import numpy as np
from collections import defaultdict

class VectorDatabase:
    def __init__(self):
        self.vectors = defaultdict(np.array)  # stores vectors by ID
        self.texts = {}                        # stores original text by ID
    
    def insert(self, key, vector, text):
        """Store a text + its vector embedding"""
        # key: unique ID like "chunk_0", "chunk_1"
        # vector: list of floats from OpenAI embedding API
        # text: the original text chunk
        self.vectors[key] = np.array(vector)  # convert to numpy for fast math
        self.texts[key] = text
    
    @staticmethod
    def cosine_similarity(vector_a, vector_b):
        """Calculate how similar two vectors are (-1 to 1)"""
        dot_product = np.dot(vector_a, vector_b)  # A·B = sum of element products
        norm_a = np.linalg.norm(vector_a)          # |A| = sqrt(sum of squares)
        norm_b = np.linalg.norm(vector_b)          # |B| = sqrt(sum of squares)
        return dot_product / (norm_a * norm_b)     # the cosine similarity formula
    
    def search_by_text(self, query_vector, k=5):
        """Find k most similar stored chunks to the query"""
        scores = {}
        for key, stored_vector in self.vectors.items():
            # Compare query vector against EVERY stored vector
            scores[key] = self.cosine_similarity(query_vector, stored_vector)
        
        # Sort by score highest first, take top k
        top_keys = sorted(scores, key=scores.get, reverse=True)[:k]
        
        # Return (text, score) pairs
        return [(self.texts[key], scores[key]) for key in top_keys]
```

**Key numpy operations explained:**
- `np.dot(a, b)` — multiply each pair of numbers and sum: `a[0]*b[0] + a[1]*b[1] + ...`
- `np.linalg.norm(v)` — the "length" of a vector: `sqrt(v[0]² + v[1]² + ...)`
- `np.array(list)` — converts Python list to numpy array (faster for math)

#### `text_utils.py` — Loading and Chunking Documents

Why chunk? Because:
1. LLMs have a maximum input length (context window)
2. Smaller chunks are more precise for retrieval
3. You want the one paragraph that answers the question, not the whole book

```python
class CharacterTextSplitter:
    def __init__(self, chunk_size=1000, chunk_overlap=200):
        # chunk_size = max characters per chunk (~200 words at 1000 chars)
        # chunk_overlap = characters shared between adjacent chunks
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def split(self, text):
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + self.chunk_size      # where this chunk ends
            chunk = text[start:end]             # slice the chunk
            chunks.append(chunk)
            start = end - self.chunk_overlap    # next chunk overlaps with this one
        
        return chunks
```

**Why overlap matters:**
```
WITHOUT overlap:
  Chunk 1: "...The CEO of the company is John"
  Chunk 2: "Smith who founded it in 2005..."
  → Neither chunk alone says "John Smith" is the CEO!

WITH overlap (200 chars):
  Chunk 1: "...The CEO of the company is John"
  Chunk 2: "is John Smith who founded..."   ← repeats "is John"
  → Both chunks contain "John Smith"
```

### Full RAG Flow in Code

```python
from aimakerspace.text_utils import TextFileLoader, CharacterTextSplitter
from aimakerspace.vectordatabase import VectorDatabase
from openai import OpenAI

client = OpenAI()

# ═══════════════════════════════
# PHASE 1: INDEX (run once)
# ═══════════════════════════════

# Load all text files from a folder
loader = TextFileLoader("my_documents/")
loader.load()
documents = loader.documents  # list of strings

# Split into chunks
splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
all_chunks = []
for doc in documents:
    all_chunks.extend(splitter.split(doc))

# Embed each chunk and store in vector DB
db = VectorDatabase()
for i, chunk in enumerate(all_chunks):
    # Ask OpenAI to convert text to a vector
    response = client.embeddings.create(
        model="text-embedding-3-small",  # embedding model (different from chat!)
        input=chunk
    )
    vector = response.data[0].embedding  # list of 1536 floats
    db.insert(key=f"chunk_{i}", vector=vector, text=chunk)

print(f"Indexed {len(all_chunks)} chunks")

# ═══════════════════════════════
# PHASE 2: QUERY (run per user question)
# ═══════════════════════════════

def answer_question(question: str) -> str:
    # 1. Embed the question
    q_response = client.embeddings.create(
        model="text-embedding-3-small",
        input=question
    )
    q_vector = q_response.data[0].embedding
    
    # 2. Find top 3 most similar chunks
    results = db.search_by_text(query_vector=q_vector, k=3)
    # results = [(text, score), (text, score), (text, score)]
    
    # 3. Build context from retrieved chunks
    context = "\n\n---\n\n".join([text for text, score in results])
    
    # 4. Build augmented prompt
    prompt = f"""Use ONLY the context below to answer the question.
If the answer is not in the context, say "I don't know."

CONTEXT:
{context}

QUESTION: {question}

ANSWER:"""
    
    # 5. Generate answer
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

print(answer_question("What is the return policy?"))
```

### ASCII Diagram: Complete RAG Flow

```
INDEXING (one-time setup):
──────────────────────────────
PDFs / TXT files
      │
      ▼  TextFileLoader
[full document text]
      │
      ▼  CharacterTextSplitter
[chunk 0][chunk 1][chunk 2]...[chunk N]
      │
      ▼  OpenAI text-embedding-3-small
[vector 0][vector 1][vector 2]...[vector N]
      │
      ▼  VectorDatabase.insert()
[STORED IN MEMORY/DISK]


QUERYING (every user question):
────────────────────────────────
User: "What is the refund policy?"
      │
      ▼  OpenAI text-embedding-3-small
[query vector]
      │
      ▼  VectorDatabase.search_by_text(k=3)
[chunk 2, chunk 0, chunk 7]  (top 3 most similar)
      │
      ▼  Build augmented prompt
"Context: [chunk2][chunk0][chunk7]
 Question: What is the refund policy?"
      │
      ▼  OpenAI gpt-4o-mini
"Based on the policy, refunds are accepted within 30 days..."
```

### Module 02 Assignment Options

Choose ONE to add to the RAG pipeline:
1. **PDF support** — load `.pdf` files using `PyPDF2` or `pdfplumber`
2. **New distance metric** — add dot product (faster) or Euclidean distance
3. **Metadata support** — store source file name and page number with each chunk

```python
# Example: Metadata support
db.insert(
    key=f"chunk_{i}",
    vector=vector,
    text=chunk,
    metadata={"source": "policy.pdf", "page": 3, "section": "Returns"}
)
```

### Key Takeaways — Module 02

```
┌─────────────────────────────────────────────────────┐
│              MODULE 02 SUMMARY                      │
│                                                     │
│  Embedding = text → list of numbers (vector)       │
│  Similar text → similar numbers                    │
│  Cosine similarity = angle between vectors (0-1)   │
│  Vector DB = stores and searches embeddings fast   │
│  RAG = Retrieve context → Augment prompt → Generate│
│  Chunk overlap prevents losing info at boundaries  │
│  text-embedding-3-small ≠ gpt-4o-mini (diff APIs) │
└─────────────────────────────────────────────────────┘
```

---

<a name="module-03"></a>
## MODULE 03 — End-to-End RAG Deployment

**Session name:** "End-to-End RAG"  
**Key skill:** Turn your Jupyter notebook RAG into a deployed web app

### From Notebook to Real App

A Jupyter notebook runs **only on your machine**. Nobody else can use it.

**Deployment** = put your app on a server with a public URL:
```
https://your-name-rag-app.hf.space  ← anyone can visit this
```

### Target Platform: Hugging Face Spaces

HF Spaces is a free hosting platform for AI apps. You push your code via Git and it deploys automatically.

```
LOCAL (your laptop)          → HF SPACES (their servers)
─────────────────────           ─────────────────────────
chainlit run app.py             Auto-builds from git push
localhost:8000                  https://your-app.hf.space
Only you can use it             Anyone on internet can use it
Your CPU/GPU                    Their cloud hardware
```

### The External Repository: AIE5-DeployPythonicRAG

This module uses a **separate Git repo** (not the main AIE5 repo) to deploy:

```
AIE5-DeployPythonicRAG/
├── app.py              ← Chainlit chat app
├── requirements.txt    ← Python dependencies list
├── Dockerfile          ← Container build instructions
├── .env                ← API keys (NEVER commit to git!)
└── data/               ← documents to index at startup
```

**CRITICAL WARNING from the module:**
```
DO NOT clone the new repo inside your existing AIE5 repo!
This causes Git nesting problems.

WRONG:  cd AIE5/ && git clone AIE5-DeployPythonicRAG  ← BAD!
RIGHT:  cd ~ && git clone AIE5-DeployPythonicRAG       ← GOOD!
```

### Key Deployment Concepts

#### 1. Environment Variables — Keep API Keys Safe

**Never put API keys directly in code:**
```python
# BAD — anyone who sees your code on GitHub can steal your key!
client = OpenAI(api_key="sk-proj-abc123...")

# GOOD — read from environment variable
import os
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
```

Local `.env` file (add to `.gitignore` so it never gets committed):
```
OPENAI_API_KEY=sk-proj-abc123...
LANGCHAIN_API_KEY=ls__xyz789...
```

On HF Spaces: set these as "Secrets" in the Space settings panel.

#### 2. `requirements.txt` — List All Dependencies

```
openai==1.30.0
chainlit==1.1.0
langchain==0.2.0
faiss-cpu==1.7.4
python-dotenv==1.0.0
```

HF Spaces runs `pip install -r requirements.txt` automatically when building.

#### 3. Dockerfile — Package Everything Consistently

Docker creates a "container" — a consistent environment that runs identically anywhere:

```dockerfile
FROM python:3.11-slim            # start with Python 3.11 base image

WORKDIR /app                     # all commands run from /app directory

COPY requirements.txt .          # copy requirements first (layer caching)
RUN pip install -r requirements.txt  # install dependencies

COPY . .                         # copy ALL your code into container

EXPOSE 8000                      # tell Docker which port the app uses

CMD ["chainlit", "run", "app.py", "--host", "0.0.0.0", "--port", "8000"]
# CMD = the command to start the app
# --host 0.0.0.0 = accept connections from outside (not just localhost)
```

#### 4. The Deployment Flow

```
You write code locally
        │
        ▼
git add . && git commit -m "deploy"
        │
        ▼
git push origin main
        │
        ▼
HF Spaces detects the push automatically
        │
        ▼
HF Spaces reads Dockerfile and builds the container
        │
        ▼
Container runs on HF's servers
        │
        ▼
Your app is live at https://your-app.hf.space !
```

### Module 03 Key Takeaways

```
┌─────────────────────────────────────────────────────┐
│              MODULE 03 SUMMARY                      │
│                                                     │
│  Deployment = app accessible to anyone via URL     │
│  HF Spaces = free hosting for AI apps              │
│  NEVER put API keys in code (use .env + secrets)  │
│  requirements.txt = list packages to install       │
│  Dockerfile = reproducible environment recipe      │
│  git push → automatic rebuild on HF Spaces         │
└─────────────────────────────────────────────────────┘
```

---

<a name="module-04"></a>
## MODULE 04 — Production RAG with LangChain and LangGraph

**Session name:** "Production RAG with LangGraph and LangChain"  
**Key skill:** Use proper production frameworks instead of custom code

### Why Move From Custom Code to LangChain?

Module 02's custom `aimakerspace` library was for learning. In production:

| Custom Library | LangChain |
|----------------|-----------|
| We wrote it ourselves | Battle-tested by thousands of companies |
| Basic features only | 100+ integrations |
| No active maintenance | Actively developed, bugs fixed quickly |
| Good for learning | Good for production |

### What Is LangChain?

LangChain is a Python framework for building LLM applications. Think of it as a "toolkit" with:
- Pre-built document loaders (PDF, CSV, web pages, Notion, etc.)
- Pre-built text splitters (character, recursive, semantic)
- Pre-built vector stores (FAISS, Pinecone, ChromaDB, etc.)
- Pre-built LLM wrappers (OpenAI, Anthropic, HuggingFace, etc.)
- **LCEL** — a way to chain components together

### LCEL — LangChain Expression Language

LCEL is LangChain's pipe operator (`|`) for chaining components.

Just like Unix shell pipes:
```bash
# Shell: output of each command flows into the next
cat file.txt | grep "error" | sort | uniq -c

# LCEL: output of each component flows into the next
retriever | prompt_template | llm | output_parser
```

#### Complete LCEL RAG Chain

```python
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import DirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

# ─── Setup ───────────────────────────────────────────────────

# Load documents (supports PDF, txt, Word, etc.)
loader = DirectoryLoader("data/", glob="**/*.txt")
docs = loader.load()
# DirectoryLoader finds all .txt files recursively

# Split with RecursiveCharacterTextSplitter
# It tries to split on: paragraphs → sentences → words → characters
splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,          # target 1000 characters per chunk
    chunk_overlap=200,        # 200 chars of overlap
    separators=["\n\n", "\n", " ", ""]  # try these separators in order
)
chunks = splitter.split_documents(docs)
# Each chunk is a Document object with .page_content and .metadata

# Create embeddings and vector store in ONE step
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
vectorstore = FAISS.from_documents(chunks, embeddings)
# FAISS: Facebook's fast vector search library (works locally, free)
# This embeds all chunks and stores them in FAISS automatically

# Create retriever from vector store
retriever = vectorstore.as_retriever(
    search_type="similarity",   # use cosine similarity
    search_kwargs={"k": 3}      # return top 3 results
)

# ─── Build LCEL Chain ────────────────────────────────────────

# Prompt template with placeholders
prompt = ChatPromptTemplate.from_template("""
Answer the question based ONLY on the following context.
If the answer is not in the context, say "I don't know."

Context:
{context}

Question: {question}

Answer:""")
# {context} and {question} will be filled in at runtime

# LLM
llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0   # 0 = deterministic (same question → same answer)
)

# Output parser: converts AIMessage object → plain string
output_parser = StrOutputParser()

# Helper to format retrieved documents
def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)
    # Join all retrieved chunks with double newlines

# Build the chain using LCEL pipe operator
chain = (
    {
        # Dict with two keys fed to the prompt template
        "context": retriever | format_docs,  # retriever returns docs, format_docs converts to string
        "question": RunnablePassthrough()    # passes the input unchanged (the question itself)
    }
    | prompt         # fills {context} and {question} into template
    | llm            # sends filled prompt to GPT-4o-mini
    | output_parser  # converts response to plain string
)
# The | operator chains: output of left becomes input of right

# ─── Use It ───────────────────────────────────────────────────

answer = chain.invoke("What is the company's vacation policy?")
# invoke() runs the whole chain end-to-end
print(answer)

# Streaming (word by word):
for chunk in chain.stream("What is the sick leave policy?"):
    print(chunk, end="", flush=True)
```

### What Is LangGraph? (The Key Upgrade)

LangChain chains are **linear**: A → B → C → done.

**LangGraph** adds the ability to **loop, branch, and maintain state**:
```
A → B → C (if condition) → D
          ↓ (else)
          E → back to B  (loop!)
```

This is essential for agents — they need to decide what to do next based on what happened before.

#### Three Core Concepts

```
STATE   = A dictionary that flows through the entire graph
          All nodes read from it and write to it
          Example: {question: "...", docs: [...], answer: "..."}

NODE    = A Python function that:
          - receives the current state as input
          - returns a partial state update as output
          Example: retrieve_node(state) → {"docs": [...]}

EDGE    = A connection between nodes
          Regular edge: always goes from A to B
          Conditional edge: goes to B or C depending on state
```

#### LangGraph RAG Implementation

```python
from langgraph.graph import StateGraph, END
from typing import TypedDict, List

# Define the state (what information flows through the graph)
class RAGState(TypedDict):
    question: str           # user's question
    documents: List[str]    # retrieved text chunks
    answer: str             # final generated answer

# Node 1: Retrieve relevant documents
def retrieve(state: RAGState) -> dict:
    """Find relevant document chunks for the question"""
    question = state["question"]
    docs = retriever.invoke(question)           # use LangChain retriever
    return {"documents": [d.page_content for d in docs]}
    # Return ONLY the keys you're changing — LangGraph merges the rest

# Node 2: Generate answer using retrieved docs
def generate(state: RAGState) -> dict:
    """Generate an answer using the retrieved context"""
    question = state["question"]
    context = "\n\n".join(state["documents"])  # join all chunks
    
    prompt_text = f"""Answer based ONLY on this context:
{context}

Question: {question}
Answer:"""
    
    response = llm.invoke([HumanMessage(content=prompt_text)])
    return {"answer": response.content}

# Build the graph
builder = StateGraph(RAGState)       # pass the state type

# Add nodes (name → function)
builder.add_node("retrieve", retrieve)
builder.add_node("generate", generate)

# Set the starting node
builder.set_entry_point("retrieve")

# Add edges (connections)
builder.add_edge("retrieve", "generate")   # retrieve → generate
builder.add_edge("generate", END)          # generate → done

# Compile (validates the graph, creates executable)
rag_graph = builder.compile()

# Run it!
result = rag_graph.invoke({"question": "What is the vacation policy?"})
print(result["answer"])
```

#### Conditional Edges (Branching)

What if documents retrieved are not relevant? Branch to a different path:

```python
def grade_documents(state: RAGState) -> str:
    """Decide if retrieved docs are good enough"""
    documents = state["documents"]
    
    if not documents:
        return "no_documents"   # → go to fallback node
    
    # Use LLM to judge relevance
    prompt = f"Are these docs relevant to '{state['question']}'? Yes or No."
    response = llm.invoke([HumanMessage(content=prompt)])
    
    if "no" in response.content.lower():
        return "not_relevant"   # → rewrite the query
    
    return "relevant"           # → proceed to generate

# Add conditional edge
builder.add_conditional_edges(
    "retrieve",           # FROM this node
    grade_documents,      # CALL this function (returns a string key)
    {
        "relevant": "generate",       # if relevant → generate answer
        "not_relevant": "rewrite",    # if not relevant → rewrite query
        "no_documents": "fallback"    # if no docs → use fallback
    }
)
```

### LangSmith — Tracing and Observability

**Problem:** When the chain runs, it's a black box. You don't know:
- What prompt was actually sent to the LLM?
- How long did the retrieval take?
- How many tokens did it use?

**LangSmith** makes the entire chain transparent:

```python
import os

# Set these environment variables before running your chain
os.environ["LANGCHAIN_TRACING_V2"] = "true"     # enable tracing
os.environ["LANGCHAIN_API_KEY"] = "ls__your_key" # from smith.langchain.com
os.environ["LANGCHAIN_PROJECT"] = "my-rag-app"   # project name in dashboard

# That's it! Now EVERY chain.invoke() is automatically traced.
# No code changes needed.
```

LangSmith UI shows you for each run:
- Input and output at each step
- Latency (time per step)
- Token usage and cost
- Any errors

### Module 04 Key Takeaways

```
┌─────────────────────────────────────────────────────┐
│              MODULE 04 SUMMARY                      │
│                                                     │
│  LangChain = framework for LLM apps                │
│  LCEL pipe | chains components linearly            │
│  FAISS = fast local vector store                   │
│  RecursiveCharacterTextSplitter = smarter splitter │
│  LangGraph adds state, loops, branching            │
│  State = shared dict flowing through graph         │
│  Nodes = functions, Edges = connections            │
│  LangSmith = observability (set 3 env vars)        │
└─────────────────────────────────────────────────────┘
```

---

<a name="module-05"></a>
## MODULE 05 — Our First Agent with LangGraph

**Session name:** "Our First Agent with LangGraph"  
**Key skill:** Build an LLM that decides what to do, not just what to say

### Agent vs Chain: The Core Difference

```
CHAIN (Module 04):
  User question → [always same path] → Answer
  Fixed sequence. Predictable. No choices.

AGENT (Module 05):
  User question → LLM decides → Use tool A? → LLM decides → Use tool B?
                      ↑___________________________________|
  Dynamic. LLM chooses tools. Can loop. Autonomous.
```

**Real example:**
```
User: "What's the refund policy and how much is 15% of $200?"

Chain would:  retrieve docs about refund → generate answer (may miss the math!)

Agent does:
  1. "I need to find refund policy" → calls search_tool
  2. "I need to calculate 15% of $200" → calls calculator_tool
  3. "I have everything" → gives final answer combining both
```

### The ReAct Pattern

The dominant agent design: **Re**asoning + **Act**ing

```
REASON: "I need information about topic X"
ACT:    call search_tool("topic X")
OBSERVE: "Search returned: [results...]"
REASON: "I need to verify claim Y from the results"
ACT:    call search_tool("verify Y")
OBSERVE: "Verified: [more results...]"
REASON: "I have enough to answer now"
RETURN: final_answer("Based on my research, ...")
```

### Building the Agent Step by Step

#### Step 1: Define Tools

```python
from langchain_core.tools import tool

# The @tool decorator converts a regular Python function into an LLM tool
# The docstring IS the tool description — the LLM reads it to decide when to use the tool!

@tool
def search_documents(query: str) -> str:
    """Search the company knowledge base for information.
    Use this when you need to find policies, procedures, or facts.
    
    Args:
        query: What to search for
    
    Returns:
        Relevant document excerpts
    """
    docs = retriever.invoke(query)          # use your vector store retriever
    if not docs:
        return "No relevant documents found."
    return "\n---\n".join(d.page_content for d in docs[:3])

@tool
def calculate(expression: str) -> str:
    """Calculate a simple mathematical expression.
    Use this for any arithmetic: addition, subtraction, percentages, etc.
    
    Args:
        expression: Math expression like '200 * 0.15' or '100 + 50 - 20'
    
    Returns:
        The calculated result
    """
    try:
        result = eval(expression)   # evaluate math expression
        return f"Result: {result}"
    except Exception as e:
        return f"Calculation error: {e}"

tools = [search_documents, calculate]
```

#### Step 2: Bind Tools to the LLM

```python
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(model="gpt-4o-mini")

# bind_tools tells the LLM what tools exist and their descriptions
llm_with_tools = llm.bind_tools(tools)
# When invoked, this LLM can now return EITHER:
#   A. A regular text answer (no tools needed)
#   B. A tool_call request: {name: "search_documents", args: {query: "..."}}
```

#### Step 3: Define Agent State

```python
from typing import TypedDict, Annotated, List
import operator
from langchain_core.messages import BaseMessage

class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add]
    # Annotated[List, operator.add] means:
    #   - This is a list
    #   - When updating, ADD to the list (append), not replace it
    # So message history keeps accumulating
```

#### Step 4: Define Agent Node (The Brain)

```python
from langchain_core.messages import SystemMessage

def agent_node(state: AgentState) -> dict:
    """The agent's reasoning node — decides what to do next"""
    
    system = SystemMessage(content="""You are a helpful assistant with access to tools.
    Use the search_documents tool to find information.
    Use the calculate tool for any math.
    When you have enough information, give a final answer.""")
    
    # Combine system message with conversation history
    messages = [system] + state["messages"]
    
    # Invoke LLM — it will either answer or request a tool call
    response = llm_with_tools.invoke(messages)
    
    return {"messages": [response]}  # append response to history
```

#### Step 5: Routing Logic

```python
def should_continue(state: AgentState) -> str:
    """After agent responds, decide what to do next"""
    last_message = state["messages"][-1]  # most recent message
    
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        # LLM requested a tool → execute the tool
        return "tools"
    else:
        # LLM gave a final answer → stop
        return "end"
```

#### Step 6: Build and Compile the Graph

```python
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

# ToolNode automatically executes whatever tool the LLM requested
tool_node = ToolNode(tools)
# It reads the tool_calls from the last message, runs the tool function,
# and returns a ToolMessage with the result

# Build graph
graph = StateGraph(AgentState)

graph.add_node("agent", agent_node)
graph.add_node("tools", tool_node)

graph.set_entry_point("agent")

# After agent: go to "tools" or "end" based on should_continue()
graph.add_conditional_edges(
    "agent",
    should_continue,
    {
        "tools": "tools",   # if tool needed
        "end": END          # if done
    }
)

# After tools always: back to agent (to process the tool result)
graph.add_edge("tools", "agent")

agent = graph.compile()
```

#### Step 7: Run the Agent

```python
from langchain_core.messages import HumanMessage

result = agent.invoke({
    "messages": [HumanMessage(content="What is the refund policy and what is 15% of $200?")]
})

# Print the final message (the agent's answer)
print(result["messages"][-1].content)
```

### The Agent Loop Visualized

```
User: "What is refund policy and 15% of $200?"
                │
                ▼
         ┌─────────┐
         │  AGENT  │  LLM thinks: "I need to search for refund policy"
         └─────────┘
              │ tool_call: search_documents("refund policy")
              ▼
         ┌─────────┐
         │  TOOLS  │  Executes search_documents → returns policy text
         └─────────┘
              │ ToolMessage: "Refunds within 30 days..."
              ▼
         ┌─────────┐
         │  AGENT  │  LLM thinks: "Now I need to calculate 15% of 200"
         └─────────┘
              │ tool_call: calculate("200 * 0.15")
              ▼
         ┌─────────┐
         │  TOOLS  │  Executes calculate → returns "Result: 30.0"
         └─────────┘
              │ ToolMessage: "Result: 30.0"
              ▼
         ┌─────────┐
         │  AGENT  │  LLM thinks: "I have both answers, I'm done"
         └─────────┘
              │ AIMessage (no tool_calls) → final answer
              ▼
         "Our return policy allows returns within 30 days.
          15% of $200 = $30.00"
```

### Always Add a Loop Limit

Prevent infinite loops with a max iterations counter:

```python
class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add]
    iteration_count: int

def agent_node(state: AgentState) -> dict:
    count = state.get("iteration_count", 0)
    
    # Safety limit: stop after 10 iterations
    if count >= 10:
        return {
            "messages": [AIMessage(content="I've reached the maximum number of steps.")],
            "iteration_count": count + 1
        }
    
    response = llm_with_tools.invoke([system] + state["messages"])
    return {"messages": [response], "iteration_count": count + 1}
```

### LangSmith Evaluation for Agents

```python
from langsmith import Client
from langsmith.evaluation import evaluate

client = Client()

# Create evaluation dataset
dataset = client.create_dataset("agent_tests")
client.create_examples(
    inputs=[
        {"question": "What is the vacation policy?"},
        {"question": "What is 25% of $500?"},
    ],
    outputs=[
        {"answer": "Employees get 15 days of vacation per year"},
        {"answer": "$125"},
    ],
    dataset_id=dataset.id
)

# Run agent on each test case
def run_on_example(inputs):
    result = agent.invoke({"messages": [HumanMessage(content=inputs["question"])]})
    return {"answer": result["messages"][-1].content}

# Evaluate
results = evaluate(
    run_on_example,
    data="agent_tests",
    experiment_prefix="agent_v1"
)
```

### Module 05 Key Takeaways

```
┌─────────────────────────────────────────────────────┐
│              MODULE 05 SUMMARY                      │
│                                                     │
│  Agent = LLM that decides which tools to use       │
│  ReAct = Reason → Act → Observe → Repeat           │
│  @tool decorator = makes Python function a tool    │
│  Docstring = tool description (LLM reads this!)    │
│  bind_tools() = tells LLM what tools exist         │
│  ToolNode = auto-executes the requested tool       │
│  Loop: agent → tools → agent → ... → END          │
│  ALWAYS add max iteration limit                     │
└─────────────────────────────────────────────────────┘
```

---

<a name="module-06"></a>
## MODULE 06 — Multi-Agent with LangGraph

**Session name:** "Multi-Agent with LangGraph"  
**Key skill:** Build a team of specialized AI agents that collaborate

### Why Multi-Agent?

A single agent can do anything — but "a jack of all trades is master of none."

Multi-agent systems:
- Each agent is a **specialist** with a focused role
- A **supervisor** coordinates who does what next
- Better quality because each agent can have its own specialized prompt and tools

### The Module 06 System: Research + Write a LinkedIn Post

```
Goal: Research an ML paper and write a LinkedIn post about it

TEAM 1: RESEARCH TEAM              TEAM 2: WRITING TEAM
────────────────────────           ─────────────────────
Web Searcher (searches web)        Writer (drafts the post)
Paper Finder (finds papers)        Editor (improves the draft)

SUPERVISOR orchestrates both teams
```

### Building the Multi-Agent System

#### The Shared State

```python
from typing import TypedDict, Annotated, List, Sequence
import operator
from langchain_core.messages import BaseMessage

class MultiAgentState(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add]
    next: str   # which agent/team the supervisor wants to act next
```

#### Creating Individual Agents

```python
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents import create_openai_tools_agent, AgentExecutor

def create_specialized_agent(role_name: str, tools: list, instructions: str):
    """Helper to create an agent with a specific role"""
    
    llm = ChatOpenAI(model="gpt-4o-mini")
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", instructions),                                    # role instructions
        MessagesPlaceholder(variable_name="messages"),               # conversation history
        MessagesPlaceholder(variable_name="agent_scratchpad"),       # tool call history
    ])
    
    agent = create_openai_tools_agent(llm, tools, prompt)
    return AgentExecutor(agent=agent, tools=tools, verbose=True)

# Create research agents
from langchain_community.tools.tavily_search import TavilySearchResults
search_tool = TavilySearchResults(max_results=5)

web_searcher = create_specialized_agent(
    role_name="web_searcher",
    tools=[search_tool],
    instructions="You are a web researcher. Search the web to gather information on the given topic. Return detailed findings."
)

paper_finder = create_specialized_agent(
    role_name="paper_finder",
    tools=[search_tool],
    instructions="You find relevant academic papers and technical articles. Focus on citations, key findings, and authors."
)

# Create writing agents
writer = create_specialized_agent(
    role_name="writer",
    tools=[],  # writer doesn't need tools, just writes
    instructions="""You are a LinkedIn content creator. Given research material,
    write an engaging LinkedIn post that:
    - Starts with a hook
    - Shares 3 key insights
    - Ends with a question to drive engagement
    - Is under 300 words
    - Uses professional but conversational tone"""
)

editor = create_specialized_agent(
    role_name="editor",
    tools=[],
    instructions="""You are a professional editor. Review the draft post and:
    - Fix grammar and clarity
    - Ensure it's engaging
    - Make it more concise where possible
    - Return the improved final version"""
)
```

#### Creating Agent Nodes for the Graph

```python
from langchain_core.messages import HumanMessage

def make_agent_node(agent_executor, agent_name):
    """Create a graph node function for an agent"""
    def node(state: MultiAgentState) -> dict:
        # Get the task from the message history
        result = agent_executor.invoke(state)
        # Wrap result as HumanMessage with agent name prefix for clarity
        output_message = HumanMessage(
            content=result["output"],
            name=agent_name  # tag with agent name for tracking
        )
        return {"messages": [output_message]}
    
    return node

# Create node functions
web_searcher_node = make_agent_node(web_searcher, "web_searcher")
paper_finder_node = make_agent_node(paper_finder, "paper_finder")
writer_node = make_agent_node(writer, "writer")
editor_node = make_agent_node(editor, "editor")
```

#### The Supervisor Node

```python
import json
from langchain_core.messages import SystemMessage

TEAM_MEMBERS = ["web_searcher", "paper_finder", "writer", "editor"]

SUPERVISOR_PROMPT = f"""You are a supervisor managing a research and writing team.
Your job is to coordinate the team to produce a LinkedIn post about an ML paper.

Team members: {', '.join(TEAM_MEMBERS)}

Given the conversation history, decide who should act next.
Respond with JSON: {{"next": "team_member_name"}} or {{"next": "FINISH"}} when done.

Workflow suggestion:
1. web_searcher → gather general information
2. paper_finder → find specific papers
3. writer → draft the post
4. editor → polish the draft
5. FINISH → return the final post
"""

def supervisor_node(state: MultiAgentState) -> dict:
    """The supervisor decides who acts next"""
    messages = [SystemMessage(content=SUPERVISOR_PROMPT)] + state["messages"]
    
    # Use GPT-4o (more powerful) for the supervisor's routing decision
    supervisor_llm = ChatOpenAI(model="gpt-4o")
    response = supervisor_llm.invoke(messages)
    
    # Parse JSON response
    try:
        decision = json.loads(response.content)
        next_worker = decision["next"]
    except:
        next_worker = "FINISH"  # if parsing fails, stop
    
    return {"next": next_worker}
```

#### Building the Multi-Agent Graph

```python
from langgraph.graph import StateGraph, END

# Build the graph
workflow = StateGraph(MultiAgentState)

# Add all nodes
workflow.add_node("supervisor", supervisor_node)
workflow.add_node("web_searcher", web_searcher_node)
workflow.add_node("paper_finder", paper_finder_node)
workflow.add_node("writer", writer_node)
workflow.add_node("editor", editor_node)

# Start with supervisor
workflow.set_entry_point("supervisor")

# Supervisor routes to one of the agents or FINISH
workflow.add_conditional_edges(
    "supervisor",
    lambda state: state["next"],   # use the "next" key to decide
    {
        "web_searcher": "web_searcher",
        "paper_finder": "paper_finder",
        "writer": "writer",
        "editor": "editor",
        "FINISH": END
    }
)

# After each agent, always return to supervisor
for member in ["web_searcher", "paper_finder", "writer", "editor"]:
    workflow.add_edge(member, "supervisor")

multi_agent = workflow.compile()

# Run it!
result = multi_agent.invoke({
    "messages": [HumanMessage(content="Write a LinkedIn post about the Attention is All You Need paper")]
})

# Get the last message (the final post)
print(result["messages"][-1].content)
```

### The Flow Visualized

```
"Write a LinkedIn post about Attention is All You Need"
                        │
                        ▼
                 ┌────────────┐
                 │ SUPERVISOR │ → next: "web_searcher"
                 └────────────┘
                        │
                        ▼
                 ┌──────────────┐
                 │ WEB_SEARCHER │ → searches web for paper info
                 └──────────────┘
                        │
                        ▼
                 ┌────────────┐
                 │ SUPERVISOR │ → next: "paper_finder"
                 └────────────┘
                        │
                        ▼
                 ┌──────────────┐
                 │ PAPER_FINDER │ → finds citations, key facts
                 └──────────────┘
                        │
                        ▼
                 ┌────────────┐
                 │ SUPERVISOR │ → next: "writer"
                 └────────────┘
                        │
                        ▼
                 ┌────────┐
                 │ WRITER │ → drafts the LinkedIn post
                 └────────┘
                        │
                        ▼
                 ┌────────────┐
                 │ SUPERVISOR │ → next: "editor"
                 └────────────┘
                        │
                        ▼
                 ┌────────┐
                 │ EDITOR │ → polishes the draft
                 └────────┘
                        │
                        ▼
                 ┌────────────┐
                 │ SUPERVISOR │ → next: "FINISH"
                 └────────────┘
                        │
                        ▼
                 Final LinkedIn Post!
```

### Module 06 Key Takeaways

```
┌─────────────────────────────────────────────────────┐
│              MODULE 06 SUMMARY                      │
│                                                     │
│  Multi-agent = specialized agents + supervisor     │
│  Supervisor routes to right specialist             │
│  Each agent has its own prompt and tools           │
│  After each worker → back to supervisor            │
│  Supervisor outputs "FINISH" when done             │
│  Better quality than one generalist agent          │
│  Supervisor uses more powerful LLM (gpt-4o)        │
└─────────────────────────────────────────────────────┘
```

---

<a name="module-07"></a>
## MODULE 07 — Synthetic Data Generation and LangSmith

**Session name:** "Synthetic Data Generation and LangSmith"  
**Key skill:** Auto-generate test cases using LLMs to build evaluation datasets

### The Evaluation Problem

To evaluate your RAG app, you need:
- Questions users might ask → **Hard to collect at launch**
- Correct answers to those questions → **Expensive to write manually**
- Relevant document chunks for each Q → **Tedious to identify**

**Synthetic Data Generation** = use an LLM to automatically create these from your documents.

### RAGAS Knowledge Graph Approach

RAGAS generates test data by:
1. **Parsing** your documents → extracting key entities and concepts
2. **Building a Knowledge Graph** → mapping relationships between concepts
3. **Walking the graph** → generating questions from traversal paths

```
Document: "RAG systems retrieve relevant documents before generating answers.
           They use vector databases for storage and cosine similarity for search."

Knowledge Graph:
  RAG system ──uses──► vector database
  RAG system ──uses──► cosine similarity
  RAG system ──does──► retrieve documents
  RAG system ──does──► generate answers
  vector database ──enables──► storage

Generated questions:
  Simple:       "What do RAG systems retrieve?"
  Multi-context:"How do RAG systems use vector databases and cosine similarity together?"
  Reasoning:    "Why might vector databases with cosine similarity be better than keyword search for RAG?"
```

### The Three Evolution Types (from Evol Instruct paper)

```
SIMPLE EVOLUTION:
─────────────────
Chunk: "Employees receive 15 days of paid vacation annually."
→ "How many paid vacation days do employees receive per year?"

What it tests: Can the RAG system find and return basic facts?

MULTI-CONTEXT EVOLUTION:
─────────────────────────
Chunk 1: "Full-time employees accrue vacation at 1.25 days/month"
Chunk 2: "Vacation accrual begins after 90-day probationary period"
→ "When does vacation accrual begin and at what rate?"

What it tests: Can the system retrieve and combine multiple chunks?

REASONING EVOLUTION:
─────────────────────
Chunk: "Unused vacation days expire at year end unless carried over"
→ "Why is it important for employees to track their vacation balance?"

What it tests: Can the system help users understand implications?
```

### RAGAS Code: Generating Synthetic Test Data

```python
from ragas.testset.generator import TestsetGenerator
from ragas.testset.evolutions import simple, reasoning, multi_context
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.document_loaders import DirectoryLoader

# Load your domain documents
loader = DirectoryLoader("company_docs/", glob="**/*.txt")
documents = loader.load()
print(f"Loaded {len(documents)} documents")

# Set up RAGAS generator
generator = TestsetGenerator.from_langchain(
    generator_llm=ChatOpenAI(model="gpt-4o"),    # generates questions
    critic_llm=ChatOpenAI(model="gpt-4o"),        # reviews quality
    embeddings=OpenAIEmbeddings()                 # for building knowledge graph
)

# Generate test cases
testset = generator.generate_with_langchain_docs(
    documents,
    test_size=50,       # generate 50 test cases total
    distributions={
        simple: 0.5,         # 50% = 25 simple questions
        reasoning: 0.25,     # 25% = 12-13 reasoning questions
        multi_context: 0.25  # 25% = 12-13 multi-context questions
    },
    # raise_exceptions=False  # skip bad docs instead of crashing
)

# Convert to pandas DataFrame
df = testset.to_pandas()
print(df.columns)
# → Index(['question', 'contexts', 'ground_truth', 'evolution_type', ...])

print(df.head(3))
# question       | "What is the vacation policy?"
# contexts       | ["Employees receive 15 days..."]
# ground_truth   | "Employees receive 15 days of paid vacation annually"
# evolution_type | "simple"
```

### Loading Test Data into LangSmith

```python
from langsmith import Client

client = Client()

# Create a dataset in LangSmith (cloud storage for test cases)
dataset_name = "hr_policy_rag_eval_v1"
dataset = client.create_dataset(
    dataset_name=dataset_name,
    description="Synthetic test cases for HR policy RAG system"
)

# Upload each test case
for _, row in df.iterrows():
    client.create_example(
        inputs={
            "question": row["question"]           # input to RAG
        },
        outputs={
            "answer": row["ground_truth"],         # expected output
            "contexts": row["contexts"]            # expected contexts
        },
        metadata={
            "evolution_type": row["evolution_type"]  # for filtering
        },
        dataset_id=dataset.id
    )

print(f"Uploaded {len(df)} examples to LangSmith dataset '{dataset_name}'")
```

### Evaluating Against the Dataset

```python
from langsmith.evaluation import evaluate, LangChainStringEvaluator

# How to run your RAG chain on a test case
def run_rag(inputs: dict) -> dict:
    question = inputs["question"]
    answer = chain.invoke(question)          # your LCEL chain
    return {"answer": answer}

# Evaluators — how to score each output
qa_evaluator = LangChainStringEvaluator(
    "qa",                                    # "question-answer" evaluator
    config={"llm": ChatOpenAI(model="gpt-4o")},
    prepare_data=lambda run, example: {
        "prediction": run.outputs["answer"],
        "reference": example.outputs["answer"],
        "input": example.inputs["question"]
    }
)

# Run the evaluation
results = evaluate(
    run_rag,
    data=dataset_name,           # name of the LangSmith dataset
    evaluators=[qa_evaluator],
    experiment_prefix="rag_v1",  # name for this experiment run
    num_repetitions=1            # run each test case once
)

print(results)  # shows overall score and per-example results
```

### The Improvement Loop

```
         ┌─────────────────────────────────────────────────┐
         │              RAGAS EVAL LOOP                    │
         │                                                 │
         │  1. Build RAG system (v1)                       │
         │           │                                     │
         │           ▼                                     │
         │  2. Generate synthetic test data with RAGAS    │
         │           │                                     │
         │           ▼                                     │
         │  3. Evaluate v1 against test data               │
         │     → faithfulness: 0.72, precision: 0.65      │
         │           │                                     │
         │           ▼                                     │
         │  4. Identify weaknesses                         │
         │     → low precision = too many irrelevant chunks│
         │           │                                     │
         │           ▼                                     │
         │  5. Fix: reduce k from 5 to 3                  │
         │           │                                     │
         │           ▼                                     │
         │  6. Re-evaluate (v2)                            │
         │     → faithfulness: 0.78, precision: 0.80 ✓    │
         │           │                                     │
         │           ▼                                     │
         │  7. Repeat until scores are good               │
         └─────────────────────────────────────────────────┘
```

### The Hardmode Assignment: LangGraph Agent for Evol Instruct

Build a LangGraph agent that generates synthetic data using Evol Instruct:

```python
class DataGenState(TypedDict):
    documents: List[str]           # input: raw document chunks
    simple_questions: List[dict]   # output of simple evolution
    mc_questions: List[dict]       # output of multi-context evolution
    reasoning_questions: List[dict] # output of reasoning evolution

def simple_evolution(state: DataGenState) -> dict:
    questions = []
    for chunk in state["documents"][:10]:   # limit for demo
        prompt = f"""Generate a simple factual question and answer from this text:

Text: {chunk}

Respond in JSON: {{"question": "...", "answer": "...", "context": "{chunk[:100]}..."}}
Only respond with valid JSON, nothing else."""
        
        response = llm.invoke([HumanMessage(content=prompt)])
        try:
            q = json.loads(response.content)
            q["evolution_type"] = "simple"
            questions.append(q)
        except json.JSONDecodeError:
            pass  # skip malformed responses
    
    return {"simple_questions": questions}

def reasoning_evolution(state: DataGenState) -> dict:
    """Evolve simple questions into reasoning questions"""
    questions = []
    for q in state["simple_questions"]:
        prompt = f"""Transform this simple question into a reasoning question.
A reasoning question requires inference or "why/how" thinking.

Original question: {q['question']}
Context: {q['context']}

Respond in JSON: {{"question": "...", "answer": "...", "context": "..."}}"""
        
        response = llm.invoke([HumanMessage(content=prompt)])
        try:
            evolved = json.loads(response.content)
            evolved["evolution_type"] = "reasoning"
            questions.append(evolved)
        except:
            pass
    
    return {"reasoning_questions": questions}

# Build the graph
gen_graph = StateGraph(DataGenState)
gen_graph.add_node("simple_evolution", simple_evolution)
gen_graph.add_node("reasoning_evolution", reasoning_evolution)
# Add multi_context_evolution node too...

gen_graph.set_entry_point("simple_evolution")
gen_graph.add_edge("simple_evolution", "reasoning_evolution")
gen_graph.add_edge("reasoning_evolution", END)

data_generator = gen_graph.compile()
```

### Module 07 Key Takeaways

```
┌─────────────────────────────────────────────────────┐
│              MODULE 07 SUMMARY                      │
│                                                     │
│  Synthetic data = LLM-generated test Q&A pairs    │
│  RAGAS uses Knowledge Graph to generate questions  │
│  Three types: simple, multi-context, reasoning     │
│  LangSmith stores datasets permanently in cloud   │
│  Evaluation: run RAG → compare to ground truth     │
│  The loop: evaluate → identify weakness → fix → repeat │
└─────────────────────────────────────────────────────┘
```

---

<a name="module-08"></a>
## MODULE 08 — Evaluating RAG with RAGAS

**Session name:** "Evaluating RAG with RAGAS"  
**Key skill:** Measure RAG quality with 5 rigorous metrics

### Why Metric-Based Evaluation?

| Method | What it tells you | Problem |
|--------|-------------------|---------|
| Vibe check (Module 01) | "Does it catastrophically fail?" | Not precise, not reproducible |
| Human review | Good quality judgement | Slow, expensive, inconsistent |
| RAGAS metrics | Precise numbers (0-1) | Requires test dataset |

With RAGAS metrics, you get numbers like:
```
faithfulness: 0.87
answer_relevancy: 0.92
context_precision: 0.78
```
Now you can: track improvement over time, compare configurations, set quality thresholds.

### The 5 RAGAS Metrics Deep Dive

#### Metric 1: Faithfulness (Did LLM stick to the facts?)

```
Question: "When was the company founded?"
Context: "AcmeCorp was established in 2005 by Jane Smith."
Answer: "AcmeCorp was founded in 2005 by Jane Smith, who previously worked at Google."

Claims in the answer:
  ✓ "Founded in 2005" → in context? YES
  ✓ "by Jane Smith" → in context? YES
  ✗ "previously worked at Google" → in context? NO (HALLUCINATION!)

Faithfulness = 2/3 = 0.67
```

**Why it matters:** LLMs can confidently make things up. Faithfulness < 0.8 means your LLM is adding information not in the retrieved context.

**How to fix low faithfulness:**
- Add "ONLY use the provided context" to system prompt
- Set `temperature=0`
- Use a stronger/larger LLM

#### Metric 2: Answer Relevancy (Did the answer address the question?)

```
Question: "How do I reset my password?"
Answer: "Our company was founded in 2005. We have offices in 12 countries."

Answer Relevancy = 0.0 (answer completely off-topic!)

Better answer: "To reset your password, go to login page and click 'Forgot Password'."
Answer Relevancy = 1.0
```

**How to fix:** Improve prompt template, ensure the question is clearly passed through.

#### Metric 3: Context Precision (Are retrieved chunks all relevant?)

```
Question: "What is the sick leave policy?"
Retrieved chunks:
  Chunk A: "Employees get 10 sick days per year" → RELEVANT
  Chunk B: "Office hours are 9am to 5pm" → NOT RELEVANT
  Chunk C: "Sick days reset annually on Jan 1" → RELEVANT

Context Precision = 2/3 = 0.67
(2 relevant chunks out of 3 retrieved)
```

**How to fix low precision:** Reduce `k` (retrieve fewer chunks), use metadata filtering.

#### Metric 4: Context Recall (Did we find all needed information?)

```
Question: "Explain the full refund process"

Ground truth answer needs:
  ✓ How to initiate (fill out form)
  ✓ Timeline (5-7 business days)
  ✗ Eligibility criteria (must have receipt) ← NOT retrieved!

Context Recall = 2/3 = 0.67
(we retrieved info for 2 of 3 required facts)
```

**How to fix low recall:** Increase `k`, use smaller chunk size, try query expansion.

#### Metric 5: Answer Correctness (Is the answer factually right?)

```
Ground truth: "Returns accepted within 30 days; refund processed in 5-7 business days"
Model answer: "Returns accepted within 30 days"

Answer Correctness = ~0.6 (partially right, missing processing timeline)
```

This combines faithfulness AND completeness against the ground truth.

### Running RAGAS Evaluation

```python
from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_precision,
    context_recall,
    answer_correctness
)
from datasets import Dataset

# ─── Collect RAG outputs for your test set ───────────────

evaluation_data = []

for _, row in test_df.iterrows():
    question = row["question"]
    expected_answer = row["ground_truth"]
    
    # Run your RAG chain and collect ALL intermediate data
    # We need: the question, generated answer, retrieved contexts, ground truth
    
    # Get retrieved documents
    retrieved_docs = retriever.invoke(question)
    contexts = [doc.page_content for doc in retrieved_docs]
    
    # Get generated answer
    context_text = "\n\n".join(contexts)
    prompt = f"Context: {context_text}\n\nQuestion: {question}\nAnswer:"
    generated_answer = llm.invoke([HumanMessage(content=prompt)]).content
    
    evaluation_data.append({
        "question": question,
        "answer": generated_answer,          # what the RAG system said
        "contexts": contexts,                # list of retrieved chunks
        "ground_truth": expected_answer      # what the correct answer is
    })

# Convert to HuggingFace Dataset format (RAGAS requires this)
ragas_dataset = Dataset.from_list(evaluation_data)

# ─── Run evaluation ───────────────────────────────────────

results = evaluate(
    ragas_dataset,
    metrics=[
        faithfulness,
        answer_relevancy,
        context_precision,
        context_recall,
        answer_correctness
    ],
    llm=ChatOpenAI(model="gpt-4o"),           # LLM used as evaluator/judge
    embeddings=OpenAIEmbeddings()             # used for answer_relevancy
)

# Print results
print(results)
# {'faithfulness': 0.87, 'answer_relevancy': 0.91, 
#  'context_precision': 0.76, 'context_recall': 0.83,
#  'answer_correctness': 0.79}

# Get per-question results as DataFrame
results_df = results.to_pandas()
print(results_df[["question", "faithfulness", "context_precision"]].head())
```

### Improvement Decision Table

```
┌───────────────────────┬──────────────────────────────────────────────┐
│ Low Score In          │ Try These Fixes                              │
├───────────────────────┼──────────────────────────────────────────────┤
│ Faithfulness < 0.7    │ Add "ONLY use context" to prompt             │
│                       │ Set temperature=0                            │
│                       │ Use GPT-4o instead of GPT-4o-mini            │
├───────────────────────┼──────────────────────────────────────────────┤
│ Answer Relevancy < 0.7│ Fix prompt template formatting               │
│                       │ Make sure question flows through correctly   │
├───────────────────────┼──────────────────────────────────────────────┤
│ Context Precision < 0.7│ Reduce k (retrieve 3 not 5)               │
│                       │ Add metadata filtering                       │
│                       │ Try hybrid search                            │
├───────────────────────┼──────────────────────────────────────────────┤
│ Context Recall < 0.7  │ Increase k (retrieve 5 not 3)               │
│                       │ Use smaller chunk size (500 not 1000)        │
│                       │ Try query expansion / rewriting              │
├───────────────────────┼──────────────────────────────────────────────┤
│ Answer Correctness < 0.7│ All of the above + better LLM            │
│                       │ More complete source documents               │
└───────────────────────┴──────────────────────────────────────────────┘
```

### Semantic Chunking (Advanced — Bonus Challenge)

Standard chunking splits by character count (dumb). Semantic chunking splits by meaning (smart):

```python
from langchain_experimental.text_splitter import SemanticChunker

# Creates chunks where each chunk = one coherent topic
splitter = SemanticChunker(
    OpenAIEmbeddings(),
    breakpoint_threshold_type="percentile",
    breakpoint_threshold_amount=95   # split at points where similarity drops the most
)

# This ensures sentences about the same topic stay together
smart_chunks = splitter.split_text(document_text)
```

**Typical result:** Semantic chunking improves context precision by 5-15%.

### Module 08 Key Takeaways

```
┌─────────────────────────────────────────────────────┐
│              MODULE 08 SUMMARY                      │
│                                                     │
│  5 RAGAS metrics give precise quality scores       │
│  Faithfulness = no hallucinations (0→1)            │
│  Answer Relevancy = addresses the question         │
│  Context Precision = no noise in retrieval         │
│  Context Recall = found all needed information     │
│  Answer Correctness = factually right              │
│  Each metric has specific fixes when low           │
│  Semantic chunking improves precision              │
└─────────────────────────────────────────────────────┘
```

---

<a name="module-09"></a>
## MODULE 09 — Fine-tuning Embeddings

**Session name:** "Fine-tuning Embeddings or Domain-Adapted Retrieval"  
**Key skill:** Specialize embedding models for your specific domain

### Why Fine-tune Embeddings?

Generic embedding models (like OpenAI's) were trained on general internet text. They struggle with specialized domains:

```
MEDICAL DOMAIN EXAMPLE:
─────────────────────────
Generic embedding for "MI":
  → confused between Myocardial Infarction, Michigan, Machine Intelligence

Fine-tuned medical embedding for "MI":
  → strongly points toward Myocardial Infarction

LEGAL DOMAIN EXAMPLE:
─────────────────────────
Generic: "brief" → mix of "short document", "underwear", "to brief someone"
Fine-tuned legal: "brief" → strongly → "legal brief / court filing"
```

### The Model: snowflake-arctic-embed-l

This module fine-tunes `Snowflake/snowflake-arctic-embed-l` — a top-ranked open-source embedding model available on HuggingFace.

Why this model?
- Top performance on MTEB benchmark (standard embedding leaderboard)
- Apache 2.0 license (free for commercial use)
- 335M parameters (large but fine-tunable on a single GPU)

### Triplet Loss — The Training Method

**Triplet loss** is the training technique for improving embeddings.

Each training example = 3 pieces:
```
ANCHOR:   "How many sick days do employees get?"      (the query)
POSITIVE: "Employees receive 10 sick days per year."  (relevant chunk)
NEGATIVE: "The office is located on 5th Avenue."     (irrelevant chunk)

TRAINING GOAL:
  cosine_sim(anchor, positive) should be HIGH (close to 1.0)
  cosine_sim(anchor, negative) should be LOW  (close to 0.0)

The model adjusts weights to make this true.
```

### Creating Training Data

```python
from ragas.testset.generator import TestsetGenerator
from ragas.testset.evolutions import simple
import random

# Step 1: Generate question-context pairs using RAGAS
generator = TestsetGenerator.from_langchain(
    generator_llm=ChatOpenAI(model="gpt-4o"),
    critic_llm=ChatOpenAI(model="gpt-4o"),
    embeddings=OpenAIEmbeddings()
)

testset = generator.generate_with_langchain_docs(
    domain_documents,
    test_size=100,
    distributions={simple: 1.0}  # only simple questions needed for embeddings
)
df = testset.to_pandas()

# Step 2: Create triplets from Q&A pairs
all_contexts = df["contexts"].tolist()  # list of lists

training_triplets = []
for idx, row in df.iterrows():
    anchor = row["question"]          # the question (anchor)
    positive = row["contexts"][0]     # the relevant chunk (positive)
    
    # Pick a random negative — a context from a DIFFERENT question
    negative_candidates = [
        contexts[0] for i, contexts in enumerate(all_contexts) 
        if i != idx and contexts  # different row, non-empty
    ]
    negative = random.choice(negative_candidates)
    
    training_triplets.append({
        "anchor": anchor,
        "positive": positive,
        "negative": negative
    })

print(f"Created {len(training_triplets)} training triplets")
```

### The Fine-tuning Code

```python
from sentence_transformers import (
    SentenceTransformer,
    InputExample,
    losses
)
from torch.utils.data import DataLoader

# Load the pre-trained model from HuggingFace
model = SentenceTransformer("Snowflake/snowflake-arctic-embed-l")
# This downloads ~1.3GB to your machine (cached after first run)

# Create SentenceTransformers training examples
train_examples = [
    InputExample(
        texts=[
            triplet["anchor"],    # position 0 = anchor
            triplet["positive"],  # position 1 = positive (should be close)
            triplet["negative"]   # position 2 = negative (should be far)
        ]
    )
    for triplet in training_triplets
]

# Create DataLoader (batches data for efficient GPU training)
train_loader = DataLoader(
    train_examples,
    shuffle=True,    # randomize order each epoch (prevents memorizing order)
    batch_size=16    # process 16 triplets at once
)

# Define TripletLoss
train_loss = losses.TripletLoss(
    model=model,
    distance_metric=losses.TripletDistanceMetric.COSINE,
    triplet_margin=0.5   # anchor-positive must be 0.5 closer than anchor-negative
)

# Fine-tune the model
model.fit(
    train_objectives=[(train_loader, train_loss)],
    epochs=3,               # go through all data 3 times
    warmup_steps=100,       # slowly increase learning rate at start
    output_path="models/fine_tuned_arctic_embed/",
    show_progress_bar=True  # print progress bar
)

print("Done! Model saved to models/fine_tuned_arctic_embed/")
```

### Evaluating Before vs After Fine-tuning

```python
from sentence_transformers import util
import torch

def hit_at_k(model, queries, corpus, relevant_indices, k=3):
    """
    Hit@k: Did the correct document appear in the top k results?
    
    queries: list of question strings
    corpus: list of all document chunks
    relevant_indices: list of which corpus index is correct for each query
    k: how many results to check
    
    Returns: hit rate (0.0 to 1.0)
    """
    # Encode all documents (done once)
    corpus_embeddings = model.encode(
        corpus,
        convert_to_tensor=True,   # return PyTorch tensor
        show_progress_bar=True
    )
    
    hits = 0
    for query, correct_idx in zip(queries, relevant_indices):
        # Encode the query
        query_embedding = model.encode(query, convert_to_tensor=True)
        
        # Find top k most similar corpus items
        scores = util.cos_sim(query_embedding, corpus_embeddings)[0]
        top_k = scores.argsort(descending=True)[:k].tolist()
        
        # Check if the correct document is in top k
        if correct_idx in top_k:
            hits += 1
    
    return hits / len(queries)

# Load both models
original = SentenceTransformer("Snowflake/snowflake-arctic-embed-l")
finetuned = SentenceTransformer("models/fine_tuned_arctic_embed/")

# Evaluate on test set
original_score = hit_at_k(original, test_queries, corpus, correct_indices, k=3)
finetuned_score = hit_at_k(finetuned, test_queries, corpus, correct_indices, k=3)

print(f"Original model  Hit@3: {original_score:.3f} ({original_score*100:.1f}%)")
print(f"Fine-tuned model Hit@3: {finetuned_score:.3f} ({finetuned_score*100:.1f}%)")
print(f"Improvement: +{(finetuned_score - original_score)*100:.1f} percentage points")
```

### Module 09 Key Takeaways

```
┌─────────────────────────────────────────────────────┐
│              MODULE 09 SUMMARY                      │
│                                                     │
│  Generic embeddings fail in specialized domains    │
│  Fine-tuning adapts the model to your data         │
│  Triplet = anchor + positive + negative            │
│  Triplet loss pushes relevant docs closer          │
│  RAGAS generates the Q&A pairs for training data   │
│  Evaluate with Hit@k: correct doc in top k?        │
│  Typical improvement: 5-20% on domain-specific data│
└─────────────────────────────────────────────────────┘
```

---

<a name="module-10"></a>
## MODULE 10 — Fine-tuning a Reasoning Model

**Session name:** "Fine-tuning a Reasoning Model"  
**Key skill:** Create an LLM that thinks step-by-step using PEFT + GRPO

### What Is a Reasoning Model?

Standard LLMs answer immediately. Reasoning models show their work:

```
Standard:
  Q: "A train goes 60mph for 2.5 hours. How far?"
  A: "150 miles" (may be wrong if not focused)

Reasoning model:
  Q: "A train goes 60mph for 2.5 hours. How far?"
  A: <thinking>
     Speed = 60 mph
     Time = 2.5 hours
     Distance = speed × time = 60 × 2.5 = 150 miles
     </thinking>
     150 miles ✓
```

The `<thinking>` block = the model reasoning before answering. This dramatically improves accuracy on complex problems.

### The Technical Stack for Module 10

```
PEFT (Parameter-Efficient Fine-Tuning)
  └── LoRA (Low-Rank Adaptation)  ← which parameters to train
       └── 4-bit Quantization     ← how to fit model in GPU memory
            └── Unsloth           ← optimized training library
                 └── GRPO         ← training algorithm for reasoning
```

### PEFT and LoRA Explained

**Full fine-tuning** = update all 8 billion parameters → needs 8 expensive GPUs.

**LoRA** = only update 0.1% of parameters → works on a single free Colab GPU!

```
HOW LORA WORKS:
───────────────
Original weight matrix W: 4096 × 4096 = 16.7 million parameters

LoRA adds two small matrices:
  A: 4096 × 8  = 32,768 parameters  (8 = rank "r")
  B: 8 × 4096  = 32,768 parameters

New effective weight: W_new = W + (A × B)

Total trainable params: 32,768 + 32,768 = 65,536
That's 256x fewer parameters than the full layer!

WHY IT WORKS: Most useful updates to weight matrices have "low rank"
(can be approximated as the product of two small matrices)
```

### 4-bit Quantization

```
STANDARD (32-bit float):
  Number: 3.14159265358979
  Storage: 32 bits = 4 bytes per number
  8B model: 8,000,000,000 × 4 bytes = 32 GB RAM needed!

4-BIT QUANTIZATION:
  Number: 3.1  (less precise but close enough)
  Storage: 4 bits = 0.5 bytes per number
  8B model: 8,000,000,000 × 0.5 bytes = 4 GB RAM needed!
  
  8x memory reduction! Fits in a free Colab T4 GPU (15GB VRAM)
```

### Unsloth — Faster Training

Unsloth is a library that makes fine-tuning 2-5x faster by:
- Optimized GPU memory access patterns
- Flash Attention 2 integration
- Custom CUDA kernels

```python
from unsloth import FastLanguageModel
import torch

# Load model with 4-bit quantization via Unsloth
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name="unsloth/Llama-3.1-8B-Instruct",
    # ^ Unsloth has pre-quantized versions ready to go
    max_seq_length=2048,     # maximum input+output length in tokens
    dtype=None,              # auto-detect: bf16 on Ampere GPUs, fp16 on others
    load_in_4bit=True,       # use 4-bit quantization
)

# Add LoRA adapters
model = FastLanguageModel.get_peft_model(
    model,
    r=8,                      # LoRA rank (8 is standard, 16 for more capacity)
    target_modules=[          # which layers to apply LoRA to
        "q_proj",             # query in attention
        "k_proj",             # key in attention
        "v_proj",             # value in attention
        "o_proj",             # output projection
        "gate_proj",          # first layer of MLP
        "up_proj",            # second layer of MLP
        "down_proj",          # third layer of MLP
    ],
    lora_alpha=16,            # scaling = alpha/r = 16/8 = 2.0
    lora_dropout=0.0,         # Unsloth optimized for 0 dropout
    bias="none",              # don't train bias terms
    use_gradient_checkpointing="unsloth",  # memory optimization trick
    random_state=42           # for reproducibility
)

# Check how many parameters we're actually training
model.print_trainable_parameters()
# trainable params: 41,943,040 || all params: 8,072,204,288 || 0.52% trainable
```

### GRPO — Group Relative Policy Optimization

GRPO is the training algorithm that teaches the model to reason. It's based on reinforcement learning:

```
HOW GRPO WORKS:
───────────────
1. Show the model a math problem:
   "What is 17 × 23?"

2. Model generates 4 different solutions:
   Solution A: "<thinking>17×23=17×20+17×3=340+51=391</thinking> 391" ← CORRECT
   Solution B: "<thinking>17×23=...</thinking> 390"                    ← WRONG
   Solution C: "391" (no thinking)                                     ← CORRECT but no reasoning
   Solution D: "<thinking>...</thinking> 391"                          ← CORRECT

3. Assign rewards:
   Solution A: reward = 1.5  (correct + has thinking + boxed format)
   Solution B: reward = 0.0  (wrong)
   Solution C: reward = 0.5  (correct but missing thinking format)
   Solution D: reward = 1.5  (correct + has thinking + boxed format)

4. Calculate relative advantage:
   Average reward = (1.5 + 0 + 0.5 + 1.5) / 4 = 0.875
   A's advantage: 1.5 - 0.875 = +0.625  (better than average → reinforce!)
   B's advantage: 0.0 - 0.875 = -0.875  (worse than average → discourage!)
   
5. Update model to make A more likely, B less likely
```

### Training with GRPO

```python
from trl import GRPOConfig, GRPOTrainer
import re

# Define reward functions — these score the model's outputs

def reward_correctness(completions, **kwargs):
    """Give reward 1.0 if answer is correct, else 0.0"""
    rewards = []
    answers = kwargs.get("answer", [])  # ground truth answers
    
    for completion, correct_answer in zip(completions, answers):
        # Look for \boxed{answer} pattern in the completion
        match = re.search(r'\\boxed\{([^}]+)\}', completion)
        if match:
            predicted = match.group(1).strip()
            is_correct = (predicted == str(correct_answer).strip())
            rewards.append(1.0 if is_correct else 0.0)
        else:
            rewards.append(0.0)  # no boxed answer = 0 reward
    
    return rewards

def reward_format(completions, **kwargs):
    """Give reward for proper reasoning format"""
    rewards = []
    for completion in completions:
        score = 0.0
        # Check for <thinking>...</thinking> block
        if re.search(r'<thinking>.*?</thinking>', completion, re.DOTALL):
            score += 0.3
        # Check for \boxed{...} final answer
        if re.search(r'\\boxed\{', completion):
            score += 0.2
        rewards.append(score)
    return rewards

# Configure training
grpo_config = GRPOConfig(
    output_dir="reasoning_model_output",
    num_train_epochs=1,
    per_device_train_batch_size=2,
    gradient_accumulation_steps=8,   # effective batch size = 2×8 = 16
    num_generations=4,               # generate 4 solutions per problem (for comparison)
    learning_rate=1e-5,
    max_completion_length=512,       # max tokens in the generated solution
    temperature=0.9,                 # some randomness during training
    report_to="wandb",               # log to Weights & Biases for tracking
)

# Create trainer
trainer = GRPOTrainer(
    model=model,
    config=grpo_config,
    reward_funcs=[
        reward_correctness,   # primary: is the answer right?
        reward_format,        # secondary: did it show reasoning?
    ],
    train_dataset=math_train_dataset,  # your training problems
)

# Train!
trainer.train()

# Save the trained model
model.save_pretrained("models/reasoning_llama3.1_8b/")
tokenizer.save_pretrained("models/reasoning_llama3.1_8b/")
```

### Module 10 Key Takeaways

```
┌─────────────────────────────────────────────────────┐
│              MODULE 10 SUMMARY                      │
│                                                     │
│  Reasoning models show work in <thinking> blocks   │
│  PEFT = train only 0.1-1% of parameters            │
│  LoRA = two small matrices A×B instead of big W    │
│  4-bit quantization = 8x memory savings            │
│  Unsloth = 2-5x faster training                    │
│  GRPO = reward correct reasoning, punish wrong     │
│  reward_correctness + reward_format = two signals  │
│  Result: model reasons step-by-step before answer  │
└─────────────────────────────────────────────────────┘
```

---

## PART 1 COMPLETE — FOUNDATIONS SUMMARY

You now understand the complete foundation of AI Engineering:

```
MODULE 01: Prompt engineering → how to talk to LLMs effectively
MODULE 02: RAG basics → teach LLM about your private documents
MODULE 03: Deployment → ship your app to the world
MODULE 04: LangChain + LangGraph → use proper production frameworks
MODULE 05: Agents → LLM that decides what actions to take
MODULE 06: Multi-agent → teams of specialized LLMs
MODULE 07: Synthetic data → auto-generate test cases
MODULE 08: RAGAS evaluation → measure quality with 5 metrics
MODULE 09: Fine-tune embeddings → specialize retrieval for your domain
MODULE 10: Fine-tune reasoning → make LLM smarter at your tasks
```

**Continue to PART 2** for Advanced Topics (Modules 13–18): Advanced Retrieval, LLMOps, On-Prem Agents, Quantization.

**Continue to PART 3** for Specialized Tracks (Modules 21–32): Full production pipelines, arXiv Paper Curator production system.
