# Arcturus — Complete Explanation Guide

> **Who this is for:** Beginners who want to understand how a full-stack, production-grade AI operating system is built — with multiple specialized agents, memory, sandboxed code execution, and an admin dashboard.

---

## Table of Contents

1. [What is Arcturus?](#what-is-arcturus)
2. [The Architecture Overview](#architecture-overview)
3. [Core Component: AgentLoop4](#agentloop4)
4. [The Agent Registry — Specialized Agents](#agent-registry)
5. [Tools and Sandboxed Execution](#tools-and-sandbox)
6. [Memory Systems](#memory-systems)
7. [RAG and Knowledge Systems](#rag-and-knowledge)
8. [The Frontend — React + Electron + Vite](#frontend)
9. [Observability — Watchtower Admin Dashboard](#watchtower)
10. [Multi-Model Support](#multi-model-support)
11. [The App Engine](#app-engine)
12. [How Pieces Fit Together — Full Request Lifecycle](#full-request-lifecycle)
13. [Repository Structure](#repository-structure)
14. [Cheatsheet](#cheatsheet)
15. [Summary and Conclusion](#summary-and-conclusion)

---

## What is Arcturus?

Arcturus is a **unified agentic operating system** — a comprehensive platform that lets you:

- Chat with specialized AI agents (code writer, web browser, document researcher, debugger)
- Have agents remember your preferences and past interactions
- Execute AI-generated code in a safe sandbox
- Search your documents using hybrid RAG
- Browse the web with an AI-controlled browser
- Build and view dynamic "apps" generated from your data
- Monitor all of this with a full observability dashboard

The closest analogy: **Arcturus is like having a team of specialized AI assistants** all connected to a shared memory, all observable, all safe.

### What Makes It Different from Simple Chatbots

| Simple Chatbot | Arcturus |
|----------------|---------|
| One conversation at a time | Persistent sessions with memory |
| One LLM model | Multiple models (Gemini, Ollama) per agent |
| No tools | Web browser, code sandbox, RAG, file system |
| No memory | Episodic + semantic memory |
| No observability | Full OpenTelemetry tracing, cost tracking |
| No safety | AST-based code safety checks |

---

## Architecture Overview

```
User (Web Browser or Electron Desktop App)
         ↓
   Vite + React Frontend
         ↓
   FastAPI Server (Python backend)
         ↓
   Router Layer
   ├── /api/rag      → RAG and document search
   ├── /api/git      → Git operations
   ├── /api/ide      → IDE agent (codebase chat)
   ├── /api/explorer → File system exploration
   └── /api/runs     → Main agent runs
         ↓
   AgentLoop4 (The Core Execution Engine)
         ↓
   AgentRunner
   ├── Registry → SkillManager → (Coder, Browser, Planner skills)
   └── MultiMCP Client
           ├── UniversalSandbox MCP (code execution)
           ├── RAG MCP (document retrieval)
           └── Browser MCP (web automation)
         ↓
   Episodic Memory (JSON files)
```

---

## Core Component: AgentLoop4

AgentLoop4 is the heart of Arcturus — the engine that runs all agents.

### What is a DAG-Based Planner-Executor?

**DAG** = Directed Acyclic Graph. A flowchart where:
- Each node is a step/task
- Edges show which step comes next
- No loops allowed (no step appears twice in the same execution)

```
Example plan for "Research Python async patterns and write a tutorial":

[Start]
  ↓
[PlannerAgent] → Creates the execution graph
  ↓
[RetrieverAgent] → Searches knowledge base for async info
  ↓
[BrowserAgent] → Fetches additional examples from web
  ↓
[CoderAgent] → Writes code examples
  ↓
[SummarizerAgent] → Combines everything into a tutorial
  ↓
[End]
```

### Dynamic Plan Generation

Unlike static workflows, AgentLoop4 can **add new steps at runtime**:

```
User: "Debug this Python code"

Initial plan: [Coder] → [Debugger]

But after reading the code, Planner realizes it needs web research:
Updated plan: [Coder] → [Browser → fetch documentation] → [Debugger]
```

This is "dynamic execution" — the plan adapts as the agent learns more.

### The ReAct Implementation

AgentLoop4 implements the ReAct (Reasoning + Acting) pattern:

```python
# Conceptual implementation of AgentLoop4
class AgentLoop4:
    def run(self, task, session_id):
        # 1. Load relevant past memories
        memories = self.memory.retrieve(task)
        
        # 2. PlannerAgent creates execution graph
        plan = self.planner.create_plan(task, memories)
        
        # 3. Execute each node in the plan
        results = []
        for node in plan.topological_sort():
            agent = self.registry.get_agent(node.agent_type)
            result = agent.execute(node.task, results)
            results.append(result)
            
            # Dynamic: Planner can add nodes based on what we found
            new_nodes = self.planner.maybe_expand(node, result)
            plan.add_nodes(new_nodes)
        
        # 4. Save to episodic memory
        self.memory.record(session_id, task, results)
        
        return results[-1]
```

### Token Budget Management

LLMs have limited context windows. AgentLoop4 tracks token usage:
- Truncates old context when approaching limits
- Summarizes long conversations to save tokens
- Prioritizes recent information

---

## The Agent Registry: Specialized Agents

Arcturus has 10+ specialized agent types, each defined in `config/agent_config.yaml`:

### PlannerAgent
**Role:** Reads the user's goal and creates an execution graph.

The Planner doesn't execute tasks — it just figures out WHO should do WHAT in which ORDER.

Input: "Write a data analysis report on the uploaded CSV"
Output:
```yaml
plan:
  - step: 1
    agent: RetrieverAgent
    task: "Load and summarize the CSV structure"
  - step: 2
    agent: CoderAgent
    task: "Write pandas analysis code"
    depends_on: [1]
  - step: 3
    agent: SummarizerAgent
    task: "Combine analysis into report"
    depends_on: [2]
```

### CoderAgent
**Role:** Writes and iterates on code to solve programming tasks.

Uses both Gemini and Ollama (for local code privacy). When privacy mode is on, code never leaves your machine.

Capabilities:
- Generate code from requirements
- Debug existing code
- Write tests
- Refactor for efficiency

### BrowserAgent
**Role:** Controls a real web browser to fetch information.

Uses the `browser` MCP server which runs Playwright/Selenium:
```
User: "Find the latest Python version and its release date"

BrowserAgent:
1. Navigate to python.org/downloads
2. Extract version numbers and dates
3. Return structured data
```

### RetrieverAgent
**Role:** Searches the knowledge base using RAG.

Calls the `rag` MCP server:
- Semantic search (meaning-based)
- Keyword/regex search
- Returns relevant document chunks

### IDE Agent (Special: Separate System)
**Role:** Chat with your entire codebase.

Uses Ollama directly (everything stays local) and supports images/screenshots.

You can say: "Explain the authentication flow" and it reads your entire codebase to answer.

Supports **vision** — paste a screenshot of an error and ask "What's wrong here?"

### Other Agents

| Agent | Purpose |
|-------|---------|
| **SummarizerAgent** | Compress long outputs into concise summaries |
| **DistillerAgent** | Extract key information from large documents |
| **ThinkerAgent** | Deep reasoning, chain-of-thought analysis |
| **FormatterAgent** | Format output (JSON, markdown, HTML) |
| **ClarificationAgent** | Ask clarifying questions when task is ambiguous |
| **QAAgent** | Quality assurance — review and critique outputs |
| **TestAgent** | Generate and run tests for code |
| **DebuggerAgent** | Systematic debugging with error analysis |

---

## Tools and Sandboxed Execution

### The Universal Sandbox

AI-generated code is **inherently unsafe** — it might accidentally delete files, make unauthorized network requests, or consume infinite CPU.

Arcturus solves this with the **Universal Sandbox** MCP server.

**How it works:**

```
AI generates code:
│
├─► AST Safety Check (before execution)
│   ├── Blocks: os.system(), subprocess, open() for writes
│   ├── Blocks: network requests to dangerous domains
│   └── Blocks: dangerous imports (ctypes, etc.)
│
├─► If safe → Execute in isolated environment
│   ├── Memory limit: configurable (e.g., 512 MB)
│   ├── Time limit: configurable (e.g., 30 seconds)
│   └── File system: sandboxed directory only
│
└─► Capture output → Return to agent
    ├── stdout (print statements)
    ├── stderr (error messages)
    └── return value (if any)
```

**What "AST-based" means:**
AST = Abstract Syntax Tree. Python can parse code into a tree structure **without executing it**, then analyze the tree for dangerous patterns:

```python
import ast

code = "import os; os.system('rm -rf /')"
tree = ast.parse(code)

# Walk the tree looking for dangerous patterns
for node in ast.walk(tree):
    if isinstance(node, ast.Import):
        if any(alias.name == 'os' for alias in node.names):
            raise SafetyError("Import of 'os' is blocked")
```

### Multi-MCP Architecture

MCP (Model Context Protocol) is a standard for connecting LLMs to tools.

Arcturus runs **multiple MCP servers simultaneously**:

```
MultiMCP Client (coordinates all servers)
├── Sandbox MCP Server
│   └── Tools: execute_python, execute_javascript, run_shell
├── RAG MCP Server
│   └── Tools: semantic_search, keyword_search, fetch_document
└── Browser MCP Server
    └── Tools: navigate, click, extract_text, screenshot, fill_form
```

Each MCP server is an independent process. MultiMCP handles:
- Routing requests to the right server
- Handling server crashes (restart automatically)
- Capability discovery (which server has which tools?)

---

## Memory Systems

### Episodic Memory

Every conversation is saved as an "episode":

```json
{
  "session_id": "abc123",
  "timestamp": "2024-01-15T10:30:00Z",
  "task": "Write a Python web scraper for news headlines",
  "steps": [
    {"agent": "PlannerAgent", "output": "..."},
    {"agent": "CoderAgent", "output": "..."},
    {"agent": "BrowserAgent", "output": "..."}
  ],
  "final_output": "Here is the web scraper...",
  "metadata": {
    "tokens_used": 4521,
    "cost_usd": 0.045,
    "models_used": ["gemini-1.5-pro"]
  }
}
```

Stored as JSON files on disk. Simple but effective.

### Semantic Memory

The more powerful memory. For every run, key insights are extracted and stored in a vector database (Qdrant).

When a new task comes in, the system searches semantic memory for **relevant past experiences**:

```
New task: "Build a Flask REST API"

Semantic search: "previous tasks related to API, Flask, web server"

Found memories:
- "3 months ago: Built a FastAPI server for user authentication"
  → Inject this memory into the planner's context
- "2 months ago: Debugged CORS issues in a Flask app"
  → Inject as potential issue to watch for
```

### RemMe — User Profiling

RemMe (Remember Me) is a background system that analyzes sessions to build a user profile:

```json
{
  "user_id": "rayudu",
  "compact_preferences": [
    "Prefers Python over JavaScript",
    "Uses async/await patterns frequently",
    "Wants code comments in docstring format",
    "Prefers dark theme examples"
  ],
  "psychological_profile": {
    "communication_style": "technical, concise",
    "expertise_level": "senior",
    "primary_domains": ["backend", "AI/ML", "DevOps"]
  }
}
```

The `compact_preferences` are injected into every agent's prompt, personalizing responses without the agent needing to ask each time.

---

## RAG and Knowledge Systems

### Deep Search

The RAG system in Arcturus combines:

1. **Semantic Search:** FAISS/Qdrant vector database
   - Convert query to embedding vector
   - Find similar document chunks

2. **Keyword/Regex Search:** MongoDB text search
   - Find documents containing specific terms
   - Useful for exact matches (function names, IDs)

3. **Hybrid Retrieval:** Combine both with Reciprocal Rank Fusion

### Document Processing Pipeline

When you upload a document:
```
File Upload
    ↓
Text Extraction (PDF → text, DOCX → text, code → text)
    ↓
Chunking (split into ~500 token pieces with overlap)
    ↓
Embedding (OpenAI/Gemini embeddings → 1536-dim vectors)
    ↓
Storage
├── Qdrant (vectors for semantic search)
├── MongoDB (metadata, full text for keyword search)
└── File system (original files)
```

---

## The Frontend: React + Electron + Vite

### Technology Stack

```
React          → Component-based UI library
Vite           → Fast build tool (replaces webpack)
TailwindCSS    → Utility-first CSS framework (fast styling)
Electron       → Wraps the web app as a desktop app
Monaco Editor  → VS Code's editor running in the browser
XTerm.js       → Terminal emulator in the browser
```

### Key UI Sections

**Chat Interface:**
- Text + image input (paste screenshots)
- Real-time streaming responses
- Collapsible agent steps (see what each agent did)
- DAG visualizer (see the execution graph)

**App Dashboard:**
- Renders `ui.json` files as interactive apps
- Displays charts, tables, cards generated by agents

**Graph Visualizer:**
- Visual representation of the agent DAG
- See plan → execution in real time

**Integrated Terminal + Editor:**
- Monaco Editor: Edit code with VS Code-like syntax highlighting
- XTerm: Run shell commands, see real-time output

**Admin Dashboard (9 tabs):**
1. Traces — OpenTelemetry trace viewer
2. Cost — Cost analytics per session/model/agent
3. Errors — Error rates and stack traces
4. Health — Service health monitoring
5. Flags — Feature flags control
6. Config — Configuration viewer and diff
7. Diagnostics — Automated health checks
8. Audit — User action audit log
9. Cache — Cache management

---

## Observability: Watchtower Admin Dashboard

Arcturus has a production-grade observability system called **Watchtower**.

### Distributed Tracing

Uses **OpenTelemetry** — the industry standard for distributed tracing.

The trace hierarchy:
```
run_span (the overall agent run)
└── agent_loop_run (the loop execution)
    └── planner (planning phase)
    └── DAG (the execution graph)
        ├── node: PlannerAgent (individual agent execution)
        │   ├── iteration (one LLM call)
        │   │   ├── llm_span (Claude/Gemini API call)
        │   │   └── tool_use_span (tool execution)
        │   └── iteration (retry if needed)
        └── node: CoderAgent
            └── iteration
                ├── llm_span
                └── code_execution_span (sandbox run)
```

Every span includes: timestamps, model used, tokens consumed, cost, agent name.

### Cost Analytics

Every LLM API call is tracked:

```python
# From ops/cost/calculator.py
cost_per_1k_tokens = {
    "gemini-1.5-pro": {"input": 0.00125, "output": 0.005},
    "gemini-1.5-flash": {"input": 0.000075, "output": 0.0003},
    "claude-sonnet-4-6": {"input": 0.003, "output": 0.015},
}

# Track per run:
cost = (input_tokens / 1000) * cost_per_1k_tokens[model]["input"] + \
       (output_tokens / 1000) * cost_per_1k_tokens[model]["output"]
```

The cost API aggregates by: session, model, agent, date range.

### Throttle Policy

To prevent runaway costs, Arcturus has global budget limits:
- Hourly cost limit (e.g., $5/hour max)
- Daily cost limit (e.g., $20/day max)
- Auto-pause when limits are hit
- Admin override capability

### Health Monitoring

Periodic background checks for all dependent services:
- MongoDB (is it running? query latency?)
- Qdrant (vector DB health)
- Ollama (local LLM available?)
- MCP servers (are they responding?)
- Neo4J (graph database)

### GDPR Compliance

`SessionDataManager` can delete ALL user data across 6 stores:
- Session files
- MongoDB spans
- Qdrant vectors
- Neo4j graph
- Chronicle checkpoints
- Audit logs

One API call: `DELETE /admin/data/{session_id}` removes everything.

---

## Multi-Model Support

Arcturus is **model-agnostic** — different agents can use different models:

```yaml
# config/agent_config.yaml
PlannerAgent:
  model: gemini-1.5-pro  # Best at planning
  
CoderAgent:
  model: ollama:codestral  # Local model, private, specialized for code
  
BrowserAgent:
  model: gemini-1.5-flash  # Fast and cheap for web scraping
  
IDE Agent:
  model: ollama:llama3.2   # Always local (your code stays private)
```

The benefit: optimize cost vs. quality vs. privacy per agent type.

---

## The App Engine

An unusual feature: Arcturus can generate **interactive UI apps** from data.

**How it works:**

1. Agent runs a data analysis task
2. Instead of returning text, it generates a `ui.json` file describing a UI layout:
   ```json
   {
     "layout": "grid",
     "components": [
       {"type": "kpi_card", "title": "Total Revenue", "value": "$1.2M"},
       {"type": "line_chart", "data": [...], "x": "date", "y": "revenue"},
       {"type": "data_table", "columns": [...], "rows": [...]}
     ]
   }
   ```
3. The React frontend renders this as an actual interactive dashboard

**Current limitations:**
- If data extraction fails, defaults to text-heavy cards
- Can update data in existing apps but can't redesign the layout

---

## Full Request Lifecycle

Let's trace a complete request: "Analyze my sales data CSV and find the top 5 customers"

```
1. User pastes CSV or uploads file
   → Frontend sends to /api/runs with task description

2. FastAPI receives request
   → Creates session_id
   → Calls AgentLoop4.run(task, session_id)

3. AgentLoop4 starts
   → Loads semantic memories related to "CSV analysis, sales data"
   → Injects user's compact_preferences (e.g., "prefers pandas over raw Python")

4. PlannerAgent generates DAG:
   Node 1: RetrieverAgent - "Load and understand the CSV structure"
   Node 2: CoderAgent - "Write pandas code to find top 5 customers"
   Node 3: FormatterAgent - "Format results as a table"

5. RetrieverAgent executes
   → Reads the CSV file using RAG tools
   → Returns: "CSV has columns: customer_id, date, amount, product"

6. CoderAgent executes
   → Generates Python code:
     import pandas as pd
     df = pd.read_csv('sales.csv')
     top5 = df.groupby('customer_id')['amount'].sum().nlargest(5)
   → Sends to Sandbox MCP Server for execution
   → AST check: safe! (no dangerous imports)
   → Executes: returns DataFrame with top 5 customers

7. FormatterAgent executes
   → Formats results as markdown table

8. Results streamed back to frontend in real-time
   → Each agent step shows as it completes
   → Final answer displayed in chat

9. Episodic memory saved
   → "User analyzed sales CSV, found top customers with pandas"
   → Session saved to JSON
   → Key insights extracted to Qdrant for future semantic search

10. OpenTelemetry span closed
    → Cost recorded: 0.023 tokens used, $0.008 total cost
    → Trace available in Watchtower admin
```

---

## Repository Structure

```
Arcturus-master/
├── api/                    # Backend Python API
│   ├── core/               # Core execution engine
│   │   ├── loop.py         # AgentLoop4
│   │   ├── runner.py       # AgentRunner
│   │   └── skills/         # Skill implementations
│   ├── routers/            # FastAPI route handlers
│   │   ├── runs.py         # Main agent runs
│   │   ├── rag.py          # RAG search
│   │   ├── ide_agent.py    # IDE agent (codebase chat)
│   │   ├── apps.py         # App generation/hydration
│   │   └── admin.py        # Admin dashboard API
│   ├── mcp_servers/        # MCP tool servers
│   │   ├── server_sandbox.py   # Code execution sandbox
│   │   ├── browser/            # Web browser automation
│   │   └── rag/                # RAG server
│   ├── ops/                # Observability and operations
│   │   ├── tracing/        # OpenTelemetry integration
│   │   ├── cost/           # Cost analytics
│   │   ├── health/         # Service health monitoring
│   │   ├── audit/          # Audit logging
│   │   └── admin/          # Feature flags, config, diagnostics
│   ├── memory/             # Memory systems
│   │   ├── episodic.py     # Episodic memory (JSON)
│   │   └── semantic.py     # Semantic memory (Qdrant)
│   └── config/
│       └── agent_config.yaml  # Agent definitions
├── apps/                   # Frontend React app
│   ├── src/
│   │   ├── features/       # UI features (chat, apps, admin)
│   │   └── components/     # Reusable UI components
│   └── electron/           # Desktop app wrapper
├── ARCHITECTURE.md         # System architecture overview
└── CAPSTONE/               # Project planning documents
```

---

## Cheatsheet

### Agent Types Quick Reference

| Agent | Input | Output | Model |
|-------|-------|--------|-------|
| PlannerAgent | Task description | Execution graph (DAG) | Gemini 1.5 Pro |
| CoderAgent | Code task | Code + execution results | Ollama (local) |
| BrowserAgent | URL or search query | Web content | Gemini 1.5 Flash |
| RetrieverAgent | Search query | Document chunks | Gemini 1.5 Flash |
| IDE Agent | Code question + codebase | Explanation | Ollama (always local) |
| SummarizerAgent | Long text | Concise summary | Gemini 1.5 Flash |
| DebuggerAgent | Error + code | Debug analysis | Gemini 1.5 Pro |

### MCP Server Capabilities

| Server | Tools Available |
|--------|----------------|
| Sandbox | execute_python, execute_js, run_shell (sandboxed) |
| RAG | semantic_search, keyword_search, list_documents |
| Browser | navigate, click, fill_form, extract_text, screenshot |

### Watchtower Tabs Reference

| Tab | What You See |
|-----|-------------|
| Traces | Full execution traces with timing |
| Cost | Cost breakdown by session, model, agent |
| Errors | Error rates, stack traces, frequency |
| Health | Service status, uptime, response times |
| Flags | Feature flag toggles |
| Config | Current config vs. defaults diff |
| Diagnostics | Automated health checks with suggestions |
| Audit | Who did what, when |
| Cache | Cache contents and flush controls |

---

## Summary and Conclusion

### What Arcturus Represents

Arcturus is a **fully integrated AI operating system** that demonstrates what production agentic AI actually looks like:

1. **Multi-agent coordination** — 10+ specialized agents working together
2. **Safe code execution** — AST-based safety checks + sandboxed environment
3. **Persistent memory** — Episodic + semantic memory that improves over time
4. **Multi-model architecture** — Right model for each agent (cost + privacy optimization)
5. **Production observability** — OpenTelemetry tracing, cost analytics, health monitoring
6. **Privacy-first** — IDE Agent and CoderAgent can use local models (Ollama) — your data never leaves

### What Makes It Particularly Educational

The CAPSTONE directory contains extensive planning documents showing:
- How complex features were designed
- What decisions were made and why
- Known limitations and future plans

This is rare — most open-source projects only show the code, not the thinking behind it.

### Key Lessons for Beginners

1. **Production AI is systems engineering** — the LLM is just one part of a much larger system
2. **Safety requires multiple layers** — input checks, AST analysis, sandbox, output validation
3. **Memory transforms agents** — stateless agents forget everything; memory makes them actually useful
4. **Observability is non-negotiable** — you cannot improve what you cannot measure
5. **Multi-model routing saves money** — use expensive models only when necessary

### What's Particularly Impressive

Arcturus goes far beyond "wrap an LLM in a FastAPI server." It implements:
- Complete OpenTelemetry integration from day one
- GDPR-compliant data deletion across 6 data stores
- Adaptive cost throttling with admin overrides
- Dynamic DAG-based execution with runtime plan modification
- AST-level code safety that blocks dangerous patterns before execution

This level of engineering is what separates a toy project from a production-ready system.

---

*This guide explains Arcturus from the perspective of someone new to agentic AI systems. Technical concepts are introduced progressively with analogies and concrete examples.*
