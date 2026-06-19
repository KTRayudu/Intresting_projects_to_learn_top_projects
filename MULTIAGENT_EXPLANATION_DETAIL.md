# Multi-Agent Systems — Complete End-to-End Explanation

> **Who this is for:** Complete beginners who want to understand how multiple AI agents work together, why you need more than one agent, and how to build, coordinate, and deploy multi-agent systems from scratch.

---

## Table of Contents

1. [What is a Multi-Agent System?](#1-what-is-a-multi-agent-system)
2. [Why Single Agents Are Not Enough](#2-why-single-agents-are-not-enough)
3. [The Building Blocks of Any Agent](#3-the-building-blocks-of-any-agent)
4. [Core Multi-Agent Patterns](#4-core-multi-agent-patterns)
5. [How Agents Communicate](#5-how-agents-communicate)
6. [Shared Memory and State](#6-shared-memory-and-state)
7. [Pattern 1 — Sequential Pipeline](#7-pattern-1-sequential-pipeline)
8. [Pattern 2 — Supervisor / Orchestrator](#8-pattern-2-supervisor-orchestrator)
9. [Pattern 3 — Parallel Agents](#9-pattern-3-parallel-agents)
10. [Pattern 4 — Hierarchical Teams](#10-pattern-4-hierarchical-teams)
11. [Pattern 5 — Debate / Adversarial](#11-pattern-5-debate-adversarial)
12. [Pattern 6 — Reflection Loop](#12-pattern-6-reflection-loop)
13. [Pattern 7 — Plan and Execute](#13-pattern-7-plan-and-execute)
14. [Framework Deep Dives](#14-framework-deep-dives)
15. [Building Blocks: Tools, Memory, State](#15-building-blocks)
16. [Safety in Multi-Agent Systems](#16-safety)
17. [Observability and Debugging](#17-observability)
18. [End-to-End Example — Research Report System](#18-end-to-end-example)
19. [End-to-End Example — Self-Healing DevOps Agent](#19-self-healing-devops)
20. [End-to-End Example — Agentic RAG with Grading](#20-agentic-rag)
21. [Common Bugs and How to Fix Them](#21-common-bugs)
22. [Cheatsheet](#22-cheatsheet)
23. [Summary and Conclusion](#23-summary)

---

## 1. What is a Multi-Agent System?

### The Simple Definition

A **multi-agent system** is a collection of AI agents that work together to accomplish a task that is too complex, too long, or requires too many specializations for a single agent to handle alone.

### The Human Team Analogy

Think about how a consulting firm delivers a project:

```
CLIENT REQUEST: "Analyze our market, build a strategy, write a report, present findings"

Without a team:
  1 consultant tries to do everything → overwhelmed, slow, inconsistent

With a team:
  Research Analyst  → collects market data
  Strategy Consultant → builds the framework
  Business Writer   → drafts the report
  Designer          → builds presentation slides
  Project Manager   → coordinates everything, handles deadlines

EACH EXPERT DOES WHAT THEY DO BEST
```

Multi-agent systems work the same way — each AI agent is a specialist, and a coordinator orchestrates their work.

### Why This Matters

A single LLM call has fundamental limitations:
- **Context window size** — can only read so much at once
- **Cognitive overload** — complex tasks need many sequential reasoning steps
- **Single specialization** — hard to be expert at coding AND writing AND research simultaneously
- **No parallelism** — one LLM call happens at a time

Multi-agent systems overcome ALL of these limitations.

---

## 2. Why Single Agents Are Not Enough

### Problem 1: Context Window Overflow

```
Task: "Analyze 500 customer support tickets and categorize all issues"

Single agent approach:
  → Stuffs all 500 tickets into one prompt
  → Exceeds context limit (200K tokens = ~500 pages max)
  → FAILS for large datasets

Multi-agent approach:
  → Splitter agent breaks tickets into batches of 50
  → 10 analyzer agents run in parallel, each handling 50 tickets
  → Aggregator agent combines all results
  → SUCCEEDS regardless of dataset size
```

### Problem 2: Quality Degrades with Task Length

Research shows that LLMs make more mistakes when asked to do many things in one prompt. The more steps in a single prompt, the lower the quality of each step.

```
"Search the web, analyze the results, extract key data, 
 check it for accuracy, format as JSON, then write a summary"

→ The LLM tries to do everything at once
→ Quality of each step is compromised

Better approach:
  Agent 1: Search web (one job, done well)
  Agent 2: Analyze results (one job, done well)
  Agent 3: Extract + validate data (one job, done well)
  Agent 4: Format + summarize (one job, done well)
```

### Problem 3: Parallelism

Some tasks can be done simultaneously. A single agent is sequential by nature.

```
Task: "Summarize 10 different news articles"

Single agent: reads article 1 → summarizes → reads article 2 → ... (serial)
  Time: 10 × 5 seconds = 50 seconds

Multi-agent: 10 agents read one article each simultaneously (parallel)
  Time: 1 × 5 seconds = 5 seconds → 10× FASTER
```

### Problem 4: Specialization

Different tasks need different models, different prompts, different tools.

```
Task: "Write and test a Python web scraper"

Code generation   → needs a code-specialized model + code execution tool
Testing           → needs pytest knowledge + test runner tool
Documentation     → needs writing ability + markdown formatter
Security review   → needs security knowledge + linting tool

One agent with all of these → mediocre at everything
Four specialized agents → each excellent at their specialty
```

---

## 3. The Building Blocks of Any Agent

Before we build multi-agent systems, understand what a single agent is made of:

### The 5 Components

```
┌─────────────────────────────────────────────────────┐
│                    AGENT                             │
│                                                     │
│  1. BRAIN (LLM)          4. TOOLS                   │
│     ┌──────────┐            ┌─────────────────────┐ │
│     │ Claude   │            │ web_search          │ │
│     │ GPT-4    │            │ read_file           │ │
│     │ Gemini   │←──────────▶│ execute_python      │ │
│     │ Llama3   │            │ send_email          │ │
│     └──────────┘            └─────────────────────┘ │
│                                                     │
│  2. MEMORY               5. INSTRUCTIONS            │
│     ┌──────────┐            ┌─────────────────────┐ │
│     │ Short:   │            │ System prompt       │ │
│     │ context  │            │ Role definition     │ │
│     │ window   │            │ Constraints         │ │
│     │ Long:    │            │ Output format       │ │
│     │ vector   │            └─────────────────────┘ │
│     │ database │                                     │
│     └──────────┘                                    │
│                                                     │
│  3. EXECUTION LOOP                                  │
│     Think → Act → Observe → Repeat                 │
└─────────────────────────────────────────────────────┘
```

### The Agent Loop in Code

```python
def single_agent_run(user_message, tools, system_prompt):
    messages = [{"role": "user", "content": user_message}]
    
    while True:
        # 1. THINK: Ask LLM what to do
        response = llm.call(
            system=system_prompt,
            messages=messages,
            tools=tools
        )
        
        # 2. If LLM is done, return answer
        if response.stop_reason == "end_turn":
            return response.text
        
        # 3. If LLM wants a tool, execute it
        elif response.stop_reason == "tool_use":
            tool_name = response.tool_name
            tool_input = response.tool_input
            
            # Run the actual tool
            tool_result = tools[tool_name].execute(tool_input)
            
            # 4. OBSERVE: Add result to conversation
            messages.append({"role": "assistant", "content": response.content})
            messages.append({"role": "tool", "content": tool_result})
            
            # 5. Loop back to THINK
```

This same loop is the foundation of every agent, whether single or part of a multi-agent system.

---

## 4. Core Multi-Agent Patterns

There are 7 fundamental patterns for organizing multiple agents. Every complex agent system is a combination of these patterns.

```
PATTERN 1: Sequential Pipeline
  Agent A → Agent B → Agent C → Final Output

PATTERN 2: Supervisor/Orchestrator
  Supervisor Agent
  ├── delegates to → Worker Agent A
  ├── delegates to → Worker Agent B
  └── delegates to → Worker Agent C

PATTERN 3: Parallel
  ┌─→ Agent A ─┐
  │             ├─→ Aggregator → Final Output
  ├─→ Agent B ─┤
  │             │
  └─→ Agent C ─┘

PATTERN 4: Hierarchical
  Top Supervisor
  ├─→ Sub-Supervisor 1
  │   ├─→ Worker A
  │   └─→ Worker B
  └─→ Sub-Supervisor 2
      ├─→ Worker C
      └─→ Worker D

PATTERN 5: Debate/Adversarial
  Agent A (argue FOR) ←─┐
  Agent B (argue AGAINST) ─→ Judge Agent → Conclusion

PATTERN 6: Reflection Loop
  Generator Agent → Output
       ↑              │
       └──────────────┘
  Critic Agent reviews and sends feedback back

PATTERN 7: Plan and Execute
  Planner Agent → [step1, step2, step3, ...]
                       ↓
                  Executor Agent runs each step
```

Each pattern solves a different type of problem. You pick the right pattern for your task.

---

## 5. How Agents Communicate

In multi-agent systems, agents need to pass information to each other. There are 4 methods:

### Method 1: Shared State (Most Common in LangGraph)

All agents read from and write to a single shared dictionary:

```python
class SharedState(TypedDict):
    user_query: str
    research_results: list
    analysis: str
    final_report: str
    errors: list

# Agent A writes research results
def research_agent(state: SharedState) -> SharedState:
    results = web_search(state["user_query"])
    return {"research_results": results}  # updates shared state

# Agent B reads research results
def analysis_agent(state: SharedState) -> SharedState:
    analysis = analyze(state["research_results"])  # reads from shared state
    return {"analysis": analysis}
```

**Best for:** When agents need to read each other's outputs at any time.

### Method 2: Message Passing (Used in AutoGen, CrewAI)

Agents send explicit messages to each other, like a group chat:

```python
# AutoGen style
researcher = AssistantAgent("Researcher")
writer = AssistantAgent("Writer")
manager = GroupChatManager([researcher, writer])

# Researcher sends a message that Writer receives
researcher → "Here is my research: [data]"
writer ← reads message → "Writing the report based on: [data]"
```

**Best for:** Conversational workflows where agents need to ask each other questions.

### Method 3: Task Queue (Worker Pool Pattern)

A queue holds tasks; agents pick up tasks as they become available:

```python
import asyncio
from asyncio import Queue

task_queue = Queue()

# Put tasks in the queue
for article in articles:
    await task_queue.put(article)

# Multiple agents consume from queue in parallel
async def worker_agent(queue):
    while not queue.empty():
        article = await queue.get()
        summary = await summarize(article)
        results.append(summary)

# Run 5 agents in parallel
await asyncio.gather(*[worker_agent(task_queue) for _ in range(5)])
```

**Best for:** Parallelizing independent tasks.

### Method 4: Handoff

One agent explicitly hands control to another agent:

```python
# Agno-style handoff
from agno.agent import Agent

triage_agent = Agent(
    name="Triage",
    instructions="Categorize the request and hand off to the right specialist",
    # This agent can hand off to specialists:
)

billing_agent = Agent(name="Billing Specialist", ...)
technical_agent = Agent(name="Technical Support", ...)

# Triage agent decides: "This is a billing issue"
# Control passes to billing_agent
```

**Best for:** Customer support, routing workflows where one agent handles initial classification.

---

## 6. Shared Memory and State

Memory is what separates stateless chatbots from agents that actually remember and learn.

### Types of Memory in Multi-Agent Systems

```
SHORT-TERM MEMORY (within one run)
  ┌─────────────────────────────────────────────────┐
  │ The conversation history for the current task   │
  │ Lives in RAM, lost when the run ends            │
  │ Example: "Earlier Agent B said X, so I'll..."  │
  └─────────────────────────────────────────────────┘

EPISODIC MEMORY (across runs, specific events)
  ┌─────────────────────────────────────────────────┐
  │ Records of past completed tasks                 │
  │ Stored in a database (JSON files, PostgreSQL)   │
  │ Example: "Last week we analyzed Tesla's data"  │
  └─────────────────────────────────────────────────┘

SEMANTIC MEMORY (concepts, knowledge)
  ┌─────────────────────────────────────────────────┐
  │ Facts, user preferences, domain knowledge       │
  │ Stored in a vector database (Qdrant, Pinecone)  │
  │ Searched by similarity (not exact key)          │
  │ Example: "This user prefers Python over JS"    │
  └─────────────────────────────────────────────────┘

PROCEDURAL MEMORY (how to do things)
  ┌─────────────────────────────────────────────────┐
  │ Patterns for how to solve certain problems      │
  │ Usually baked into agent instructions           │
  │ Example: "When analyzing data, always check..."│
  └─────────────────────────────────────────────────┘
```

### Implementing Shared Memory with LangGraph

```python
from langgraph.graph import StateGraph
from langgraph.checkpoint.memory import MemorySaver

# MemorySaver stores state across turns (conversation memory)
memory = MemorySaver()

# Build the graph
graph = StateGraph(AgentState)
# ... add nodes and edges ...

# Compile with checkpointing
app = graph.compile(checkpointer=memory)

# First turn
config = {"configurable": {"thread_id": "user-123"}}
app.invoke({"messages": ["What is RAG?"]}, config=config)

# Second turn — agent REMEMBERS the first turn
app.invoke({"messages": ["Can you give an example?"]}, config=config)
```

The `thread_id` is like a conversation ID. Same thread = same memory.

### Implementing Shared Memory with a Vector Database

```python
from qdrant_client import QdrantClient
from openai import OpenAI

client = QdrantClient(url="http://localhost:6333")
openai_client = OpenAI()

def store_memory(text: str, metadata: dict):
    """Any agent can store a memory"""
    embedding = openai_client.embeddings.create(
        input=text,
        model="text-embedding-3-small"
    ).data[0].embedding
    
    client.upsert(
        collection_name="agent_memories",
        points=[{
            "id": generate_id(),
            "vector": embedding,
            "payload": {"text": text, **metadata}
        }]
    )

def retrieve_relevant_memories(query: str, top_k: int = 5) -> list:
    """Any agent can retrieve memories relevant to its current task"""
    query_embedding = openai_client.embeddings.create(
        input=query,
        model="text-embedding-3-small"
    ).data[0].embedding
    
    results = client.search(
        collection_name="agent_memories",
        query_vector=query_embedding,
        limit=top_k
    )
    return [r.payload["text"] for r in results]

# Usage: Agent A stores a memory
store_memory(
    "User prefers Python for all code examples",
    {"type": "preference", "user": "rayudu"}
)

# Later: Agent B retrieves relevant memories
memories = retrieve_relevant_memories("What language should I use for examples?")
# Returns: ["User prefers Python for all code examples"]
```

---

## 7. Pattern 1: Sequential Pipeline

### What It Is

Agents run one after another. Each agent's output becomes the next agent's input. Like an assembly line.

```
Input → [Agent A] → [Agent B] → [Agent C] → Output
```

### When to Use It

- When each step depends on the previous step's output
- When you want clear separation of concerns
- When you need a fixed sequence of transformations

### Real Example: Document Processing Pipeline

```
Raw Document → [Parser Agent] → [Summarizer Agent] → [Translator Agent] → [Formatter Agent] → Final Output
```

### Code Example with LangGraph

```python
from langgraph.graph import StateGraph, END
from typing import TypedDict

class PipelineState(TypedDict):
    raw_document: str
    parsed_text: str
    summary: str
    translated: str
    final_output: str

# Agent functions
def parser_agent(state: PipelineState) -> dict:
    """Extract clean text from raw document"""
    clean_text = extract_text(state["raw_document"])
    return {"parsed_text": clean_text}

def summarizer_agent(state: PipelineState) -> dict:
    """Summarize the parsed text"""
    summary = llm.invoke(f"Summarize this: {state['parsed_text']}")
    return {"summary": summary.content}

def translator_agent(state: PipelineState) -> dict:
    """Translate summary to Spanish"""
    translated = llm.invoke(f"Translate to Spanish: {state['summary']}")
    return {"translated": translated.content}

def formatter_agent(state: PipelineState) -> dict:
    """Format into final output"""
    formatted = f"# Summary\n{state['translated']}"
    return {"final_output": formatted}

# Build the pipeline
pipeline = StateGraph(PipelineState)
pipeline.add_node("parser", parser_agent)
pipeline.add_node("summarizer", summarizer_agent)
pipeline.add_node("translator", translator_agent)
pipeline.add_node("formatter", formatter_agent)

# Connect sequentially
pipeline.set_entry_point("parser")
pipeline.add_edge("parser", "summarizer")
pipeline.add_edge("summarizer", "translator")
pipeline.add_edge("translator", "formatter")
pipeline.add_edge("formatter", END)

app = pipeline.compile()
result = app.invoke({"raw_document": "your document here"})
```

### Pros and Cons

| Pros | Cons |
|------|------|
| Simple to understand and debug | No parallelism (slow for independent tasks) |
| Clear data flow | If one step fails, whole pipeline fails |
| Easy to add/remove steps | Not flexible for dynamic workflows |

---

## 8. Pattern 2: Supervisor / Orchestrator

### What It Is

A central "supervisor" agent receives the user's task, decides which specialist agents to call, coordinates their work, and synthesizes the final answer.

```
User Request
     ↓
[SUPERVISOR AGENT]
     ↓ decides who to call
     ├─→ [Research Agent] ──→ returns results to supervisor
     ├─→ [Code Agent] ─────→ returns results to supervisor
     └─→ [Writer Agent] ───→ returns results to supervisor
     ↓ synthesizes everything
Final Answer
```

### When to Use It

- When the task requires different types of work
- When you don't know in advance which agents will be needed
- When you want one agent making high-level decisions

### Code Example with LangGraph

```python
from langgraph.graph import StateGraph, END
from typing import TypedDict, Literal

class SupervisorState(TypedDict):
    user_request: str
    messages: list  # conversation history between supervisor and workers
    next_agent: str  # which agent to call next
    final_answer: str

# The supervisor uses the LLM to decide what to do next
def supervisor_agent(state: SupervisorState) -> dict:
    system_prompt = """
    You are a supervisor managing a team of agents:
    - research_agent: searches the web for information
    - code_agent: writes and executes code
    - writer_agent: writes reports and documents
    - FINISH: when you have all the information you need
    
    Given the conversation so far, decide which agent to call next.
    Respond with ONLY the agent name.
    """
    
    response = llm.invoke([
        {"role": "system", "content": system_prompt},
        *state["messages"],
        {"role": "user", "content": state["user_request"]}
    ])
    
    return {"next_agent": response.content.strip()}

# Worker agents
def research_agent(state: SupervisorState) -> dict:
    results = web_search(state["user_request"])
    return {
        "messages": state["messages"] + [
            {"role": "research_agent", "content": f"Found: {results}"}
        ]
    }

def code_agent(state: SupervisorState) -> dict:
    code = generate_code(state["user_request"])
    result = execute_python(code)
    return {
        "messages": state["messages"] + [
            {"role": "code_agent", "content": f"Code result: {result}"}
        ]
    }

def writer_agent(state: SupervisorState) -> dict:
    report = write_report(state["messages"])
    return {"final_answer": report}

# Route based on supervisor's decision
def route_to_agent(state: SupervisorState) -> Literal["research", "code", "writer", "__end__"]:
    next_agent = state["next_agent"]
    if next_agent == "FINISH":
        return "__end__"
    return {
        "research_agent": "research",
        "code_agent": "code",
        "writer_agent": "writer"
    }[next_agent]

# Build the graph
graph = StateGraph(SupervisorState)
graph.add_node("supervisor", supervisor_agent)
graph.add_node("research", research_agent)
graph.add_node("code", code_agent)
graph.add_node("writer", writer_agent)

graph.set_entry_point("supervisor")

# After supervisor decides, route to the right agent
graph.add_conditional_edges("supervisor", route_to_agent)

# All workers report back to supervisor after finishing
graph.add_edge("research", "supervisor")
graph.add_edge("code", "supervisor")
graph.add_edge("writer", "supervisor")

app = graph.compile()
```

### CrewAI Hierarchical Process (Same Pattern, Simpler Code)

```python
from crewai import Agent, Task, Crew, Process

# Define specialist agents
researcher = Agent(
    role="Research Specialist",
    goal="Find accurate information about any topic",
    backstory="Expert researcher with access to web search tools",
    tools=[web_search_tool],
)

analyst = Agent(
    role="Data Analyst",
    goal="Analyze data and extract insights",
    backstory="Expert at finding patterns and trends in data",
    tools=[python_repl_tool],
)

writer = Agent(
    role="Report Writer",
    goal="Write clear, professional reports",
    backstory="Expert at turning data into compelling narratives",
)

# Define tasks
research_task = Task(
    description="Research the AI market size and growth trends for 2024",
    expected_output="Key statistics, sources, and data points about AI market",
    agent=researcher,
)

analysis_task = Task(
    description="Analyze the research data and identify the 3 most significant trends",
    expected_output="Analysis with charts or structured insights",
    agent=analyst,
    context=[research_task],
)

writing_task = Task(
    description="Write a 500-word market overview report from the analysis",
    expected_output="Professional report with introduction, findings, conclusion",
    agent=writer,
    context=[research_task, analysis_task],
)

# Hierarchical process = manager agent coordinates everything
crew = Crew(
    agents=[researcher, analyst, writer],
    tasks=[research_task, analysis_task, writing_task],
    process=Process.hierarchical,
    manager_llm="claude-sonnet-4-6",  # The supervisor model
    verbose=True,
)

result = crew.kickoff()
```

---

## 9. Pattern 3: Parallel Agents

### What It Is

Multiple agents run simultaneously on different parts of the same problem, then results are aggregated.

```
         ┌─→ Agent A (process chunk 1) ─┐
         │                               ├─→ Aggregator → Final Result
Input ───┼─→ Agent B (process chunk 2) ─┤
         │                               │
         └─→ Agent C (process chunk 3) ─┘
```

### When to Use It

- Independent subtasks that don't depend on each other
- When speed matters and tasks can be parallelized
- Processing large datasets by splitting into chunks

### Code Example with asyncio

```python
import asyncio
from anthropic import AsyncAnthropic

client = AsyncAnthropic()

async def analyze_article(article: str, agent_id: int) -> str:
    """Single agent that analyzes one article"""
    response = await client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=500,
        messages=[{
            "role": "user",
            "content": f"Summarize this article in 3 bullet points:\n\n{article}"
        }]
    )
    print(f"Agent {agent_id} finished")
    return response.content[0].text

async def parallel_summarization(articles: list[str]) -> list[str]:
    """Run summarization agents in parallel"""
    # Create tasks for all agents at once
    tasks = [
        analyze_article(article, i)
        for i, article in enumerate(articles)
    ]
    
    # Run ALL tasks simultaneously
    summaries = await asyncio.gather(*tasks)
    return list(summaries)

async def aggregator_agent(summaries: list[str]) -> str:
    """Combine all summaries into a final overview"""
    combined = "\n\n".join([f"Article {i+1}: {s}" for i, s in enumerate(summaries)])
    
    response = await client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1000,
        messages=[{
            "role": "user",
            "content": f"Create a unified overview from these article summaries:\n\n{combined}"
        }]
    )
    return response.content[0].text

# Main execution
async def main():
    articles = [
        "Article 1 text here...",
        "Article 2 text here...",
        "Article 3 text here...",
        # ... up to hundreds of articles
    ]
    
    # Step 1: Summarize all articles in parallel
    summaries = await parallel_summarization(articles)
    
    # Step 2: Aggregate into final report
    final_report = await aggregator_agent(summaries)
    print(final_report)

asyncio.run(main())
```

### Parallel with LangGraph (Fan-Out / Fan-In)

```python
from langgraph.graph import StateGraph, END
import operator
from typing import Annotated

class ParallelState(TypedDict):
    topic: str
    # Annotated with operator.add means results are APPENDED across parallel branches
    search_results: Annotated[list, operator.add]
    final_summary: str

def search_news(state: ParallelState) -> dict:
    """Search news for the topic"""
    results = news_api.search(state["topic"])
    return {"search_results": [f"NEWS: {results}"]}

def search_academic(state: ParallelState) -> dict:
    """Search academic papers"""
    results = semantic_scholar.search(state["topic"])
    return {"search_results": [f"ACADEMIC: {results}"]}

def search_social(state: ParallelState) -> dict:
    """Search social media"""
    results = twitter_api.search(state["topic"])
    return {"search_results": [f"SOCIAL: {results}"]}

def aggregator(state: ParallelState) -> dict:
    """Combine all search results"""
    all_results = "\n".join(state["search_results"])
    summary = llm.invoke(f"Summarize these findings:\n{all_results}")
    return {"final_summary": summary.content}

# Build parallel graph
graph = StateGraph(ParallelState)
graph.add_node("search_news", search_news)
graph.add_node("search_academic", search_academic)
graph.add_node("search_social", search_social)
graph.add_node("aggregator", aggregator)

# Entry splits into 3 parallel branches
graph.set_entry_point("search_news")
graph.set_entry_point("search_academic")  # LangGraph supports multiple entry points
graph.set_entry_point("search_social")

# All branches converge at aggregator
graph.add_edge("search_news", "aggregator")
graph.add_edge("search_academic", "aggregator")
graph.add_edge("search_social", "aggregator")
graph.add_edge("aggregator", END)

app = graph.compile()
```

---

## 10. Pattern 4: Hierarchical Teams

### What It Is

A tree of agents. Top-level supervisor delegates to sub-supervisors, who each manage their own team of worker agents.

```
CEO Agent (handles overall strategy)
├── Engineering Manager Agent
│   ├── Frontend Agent (builds UI)
│   ├── Backend Agent (builds API)
│   └── DevOps Agent (deploys code)
└── Product Manager Agent
    ├── Research Agent (studies users)
    └── Design Agent (creates wireframes)
```

### When to Use It

- Complex projects with distinct phases (research, development, testing, deployment)
- Large organizations with clear team structures
- Tasks that benefit from multiple levels of coordination

### Code Example with AutoGen

```python
from autogen import AssistantAgent, UserProxyAgent, GroupChat, GroupChatManager

llm_config = {"model": "gpt-4", "api_key": "your-key"}

# Sub-team 1: Research team
research_lead = AssistantAgent(
    name="Research_Lead",
    system_message="You lead the research team. Delegate research tasks and synthesize findings.",
    llm_config=llm_config,
)

web_researcher = AssistantAgent(
    name="Web_Researcher",
    system_message="You search the web for information and report findings to the Research Lead.",
    llm_config=llm_config,
)

data_analyst = AssistantAgent(
    name="Data_Analyst",
    system_message="You analyze data and create statistics. Report to Research Lead.",
    llm_config=llm_config,
)

# Sub-team 2: Writing team
writing_lead = AssistantAgent(
    name="Writing_Lead",
    system_message="You lead the writing team. Coordinate with writers and editors.",
    llm_config=llm_config,
)

writer = AssistantAgent(
    name="Writer",
    system_message="You write content based on research. Report to Writing Lead.",
    llm_config=llm_config,
)

editor = AssistantAgent(
    name="Editor",
    system_message="You edit and improve written content. Report to Writing Lead.",
    llm_config=llm_config,
)

# Top-level CEO agent
ceo = AssistantAgent(
    name="CEO",
    system_message="""You are the CEO coordinating the entire project.
    Work with Research_Lead and Writing_Lead to complete the project.
    When satisfied with the result, say TERMINATE.""",
    llm_config=llm_config,
)

# User proxy runs code and acts as human input
user_proxy = UserProxyAgent(
    name="User",
    human_input_mode="NEVER",
    code_execution_config={"work_dir": "output"},
)

# Create hierarchical group chat
all_agents = [ceo, research_lead, web_researcher, data_analyst, 
              writing_lead, writer, editor]

groupchat = GroupChat(
    agents=[user_proxy] + all_agents,
    messages=[],
    max_round=50,
    speaker_selection_method="auto",  # LLM decides who speaks next
)

manager = GroupChatManager(groupchat=groupchat, llm_config=llm_config)

# Start the hierarchical workflow
user_proxy.initiate_chat(
    manager,
    message="Research and write a comprehensive report on AI in healthcare."
)
```

---

## 11. Pattern 5: Debate / Adversarial

### What It Is

Two or more agents argue opposing positions, then a judge synthesizes the best answer. Used when you need to stress-test ideas or make high-stakes decisions.

```
Position A          Position B
    ↓                   ↓
[Devil's Advocate] [Expert Advocate]
        ↘               ↙
         [Judge Agent]
               ↓
         Final Decision
```

### When to Use It

- Fact-checking (one agent argues, another challenges)
- Decision making (pros vs. cons)
- Code review (one writes, one critiques)
- Quality assurance (generator vs. critic)

### Code Example

```python
import asyncio
from anthropic import AsyncAnthropic

client = AsyncAnthropic()

async def advocate_agent(topic: str, position: str) -> str:
    """Agent that argues FOR the position"""
    response = await client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=800,
        system=f"You are a strong advocate for the following position. Give the 5 strongest arguments: {position}",
        messages=[{"role": "user", "content": f"Topic: {topic}"}]
    )
    return response.content[0].text

async def critic_agent(topic: str, position: str) -> str:
    """Agent that challenges the position"""
    response = await client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=800,
        system="You are a skilled devil's advocate. Challenge the position with the strongest counterarguments you can find.",
        messages=[{"role": "user", "content": f"Topic: {topic}\nPosition to challenge: {position}"}]
    )
    return response.content[0].text

async def judge_agent(topic: str, arguments_for: str, arguments_against: str) -> str:
    """Neutral judge who synthesizes both sides"""
    response = await client.messages.create(
        model="claude-opus-4-8",  # Use the most powerful model for final synthesis
        max_tokens=1000,
        system="""You are a neutral judge. Review both arguments objectively.
        Identify what is valid on each side, where they agree, and deliver a balanced verdict.""",
        messages=[{
            "role": "user",
            "content": f"""
Topic: {topic}

ARGUMENTS FOR:
{arguments_for}

ARGUMENTS AGAINST:
{arguments_against}

Please deliver a balanced analysis and verdict.
"""
        }]
    )
    return response.content[0].text

async def debate_system(topic: str, position: str) -> str:
    """Run a full debate and get a verdict"""
    # Run advocate and critic in PARALLEL
    arguments_for, arguments_against = await asyncio.gather(
        advocate_agent(topic, position),
        critic_agent(topic, position)
    )
    
    print("=== ARGUMENTS FOR ===")
    print(arguments_for)
    print("\n=== ARGUMENTS AGAINST ===")
    print(arguments_against)
    
    # Judge synthesizes
    verdict = await judge_agent(topic, arguments_for, arguments_against)
    
    print("\n=== VERDICT ===")
    print(verdict)
    return verdict

# Example usage
asyncio.run(debate_system(
    topic="Should companies ban the use of AI coding assistants?",
    position="AI coding assistants should be banned in enterprise software development"
))
```

---

## 12. Pattern 6: Reflection Loop

### What It Is

A generator agent creates output, a critic agent reviews it, the generator improves based on feedback. This loop runs until quality is sufficient.

```
User Request
     ↓
[Generator Agent] → Draft 1
     ↑                  ↓
     │           [Critic/Evaluator Agent]
     │                  ↓
     └──── Feedback ─── Is quality good enough?
                             │              │
                            YES             NO
                             ↓              ↓
                      Return to User    Send feedback
                                       to Generator
```

### When to Use It

- Writing tasks (draft → critique → improve)
- Code generation (write → test → fix)
- Research reports (write → fact-check → revise)
- Any task where quality can be iteratively improved

### Code Example with LangGraph

```python
from langgraph.graph import StateGraph, END
from typing import TypedDict

class ReflectionState(TypedDict):
    task: str
    draft: str
    critique: str
    revision_count: int
    final_output: str

MAX_REVISIONS = 3

def generator_agent(state: ReflectionState) -> dict:
    """Write or revise based on critique"""
    if not state.get("critique"):
        # First draft
        prompt = f"Write a high-quality piece on: {state['task']}"
    else:
        # Revision based on feedback
        prompt = f"""
Original task: {state['task']}

Previous draft:
{state['draft']}

Critique received:
{state['critique']}

Please revise the draft to address the critique.
"""
    
    draft = llm.invoke(prompt)
    return {
        "draft": draft.content,
        "revision_count": state.get("revision_count", 0) + 1
    }

def critic_agent(state: ReflectionState) -> dict:
    """Evaluate the draft and provide specific feedback"""
    critique = llm.invoke(f"""
Evaluate this draft critically:

{state['draft']}

Be specific: what is unclear, incorrect, or could be improved?
If the draft is excellent and needs no more changes, say "APPROVED".
""")
    return {"critique": critique.content}

def should_continue(state: ReflectionState) -> str:
    """Decide: revise more or finish?"""
    # If max revisions reached, stop
    if state["revision_count"] >= MAX_REVISIONS:
        return "finish"
    # If critic approved, stop
    if "APPROVED" in state.get("critique", ""):
        return "finish"
    # Otherwise, revise again
    return "revise"

def finalize(state: ReflectionState) -> dict:
    return {"final_output": state["draft"]}

# Build reflection graph
graph = StateGraph(ReflectionState)
graph.add_node("generator", generator_agent)
graph.add_node("critic", critic_agent)
graph.add_node("finish", finalize)

graph.set_entry_point("generator")
graph.add_edge("generator", "critic")

# After critique: either revise or finish
graph.add_conditional_edges(
    "critic",
    should_continue,
    {
        "revise": "generator",   # Loop back
        "finish": "finish"       # Done
    }
)
graph.add_edge("finish", END)

app = graph.compile()
result = app.invoke({"task": "Write a compelling blog post about quantum computing"})
print(result["final_output"])
```

---

## 13. Pattern 7: Plan and Execute

### What It Is

A planner agent creates a complete plan (list of steps) upfront. An executor agent then runs each step, potentially dynamically re-planning if steps fail or new information emerges.

```
User Goal
    ↓
[PLANNER] → [step 1, step 2, step 3, step 4, step 5]
                      ↓
              [EXECUTOR] runs step 1 → result
                      ↓
              [EXECUTOR] runs step 2 → result
                      ↓
              [REPLANNER] reviews results → adjust if needed
                      ↓
              [EXECUTOR] runs step 3 → result
                      ↓
              ... until all steps complete
                      ↓
              [SYNTHESIZER] combines all results → Final Answer
```

### When to Use It

- Tasks where knowing the full plan upfront helps
- Long research tasks with many distinct steps
- Multi-step code projects
- When replanning based on intermediate results is important

### Code Example

```python
from langgraph.graph import StateGraph, END
from typing import TypedDict, list
from pydantic import BaseModel

class Step(BaseModel):
    id: int
    description: str
    tool: str  # which tool/agent to use
    depends_on: list[int] = []  # which step IDs must complete first

class PlanExecuteState(TypedDict):
    goal: str
    plan: list[Step]
    current_step_index: int
    results: dict  # step_id → result
    final_answer: str

def planner_agent(state: PlanExecuteState) -> dict:
    """Create a step-by-step plan"""
    plan_json = llm.invoke(f"""
Create a detailed step-by-step plan to achieve this goal:
{state['goal']}

Return a JSON array of steps, each with:
- id: step number
- description: what to do
- tool: one of [web_search, python_code, file_read, write_report]
- depends_on: list of step IDs that must complete first

Example:
[
  {{"id": 1, "description": "Search for recent AI trends", "tool": "web_search", "depends_on": []}},
  {{"id": 2, "description": "Analyze the data", "tool": "python_code", "depends_on": [1]}}
]
""", response_format={"type": "json_object"})
    
    steps = [Step(**s) for s in json.loads(plan_json.content)["steps"]]
    return {"plan": steps, "current_step_index": 0, "results": {}}

def executor_agent(state: PlanExecuteState) -> dict:
    """Execute the current step"""
    if state["current_step_index"] >= len(state["plan"]):
        return {}  # All steps done
    
    step = state["plan"][state["current_step_index"]]
    
    # Check if dependencies are satisfied
    for dep_id in step.depends_on:
        if dep_id not in state["results"]:
            # Skip — dependency not ready (for parallel execution)
            return {"current_step_index": state["current_step_index"] + 1}
    
    # Get context from previous results
    context = {k: state["results"][k] for k in step.depends_on}
    
    # Execute based on tool type
    if step.tool == "web_search":
        result = web_search(step.description)
    elif step.tool == "python_code":
        code = llm.invoke(f"Write Python code to: {step.description}\nContext: {context}")
        result = execute_python(code.content)
    elif step.tool == "write_report":
        result = llm.invoke(f"Write report for: {step.description}\nAll data: {state['results']}")
        result = result.content
    
    new_results = {**state["results"], step.id: result}
    return {
        "results": new_results,
        "current_step_index": state["current_step_index"] + 1
    }

def replanner_agent(state: PlanExecuteState) -> dict:
    """Review progress and adjust plan if needed"""
    completed_steps = [
        f"Step {step_id}: {state['plan'][step_id-1].description}\nResult: {result}"
        for step_id, result in state["results"].items()
    ]
    
    remaining = [
        step for step in state["plan"]
        if step.id not in state["results"]
    ]
    
    decision = llm.invoke(f"""
Goal: {state['goal']}

Completed steps:
{chr(10).join(completed_steps)}

Remaining steps:
{[s.description for s in remaining]}

Should we:
a) Continue with remaining steps (respond: CONTINUE)
b) The goal is already achieved (respond: DONE)
c) Adjust remaining steps (respond with new JSON steps array)
""")
    
    if "DONE" in decision.content:
        return {}  # Will route to finish
    elif "CONTINUE" in decision.content:
        return {}  # Keep current plan
    else:
        # Parse and update remaining steps
        new_steps = json.loads(decision.content)
        updated_plan = [s for s in state["plan"] if s.id in state["results"]]
        updated_plan.extend([Step(**s) for s in new_steps])
        return {"plan": updated_plan}

def synthesizer_agent(state: PlanExecuteState) -> dict:
    """Create the final answer from all results"""
    all_results = "\n\n".join([
        f"Step {step_id} result:\n{result}"
        for step_id, result in state["results"].items()
    ])
    
    final = llm.invoke(f"Goal was: {state['goal']}\n\nWork done:\n{all_results}\n\nSynthesize a final answer:")
    return {"final_answer": final.content}

def is_done(state: PlanExecuteState) -> str:
    """Check if all steps are complete"""
    if state["current_step_index"] >= len(state["plan"]):
        return "synthesize"
    return "execute"

# Build the graph
graph = StateGraph(PlanExecuteState)
graph.add_node("planner", planner_agent)
graph.add_node("executor", executor_agent)
graph.add_node("replanner", replanner_agent)
graph.add_node("synthesizer", synthesizer_agent)

graph.set_entry_point("planner")
graph.add_edge("planner", "executor")
graph.add_conditional_edges("executor", is_done, {
    "execute": "replanner",      # More steps to check
    "synthesize": "synthesizer"  # All done
})
graph.add_edge("replanner", "executor")
graph.add_edge("synthesizer", END)

app = graph.compile()
result = app.invoke({"goal": "Research and analyze the top 5 AI companies in 2024"})
```

---

## 14. Framework Deep Dives

### LangGraph — When to Use It

LangGraph is the best choice when you need:
- **Stateful workflows** — the agent needs to remember what it did
- **Conditional branching** — different paths based on results
- **Cycles/loops** — agents that can go back to previous steps
- **Human-in-the-loop** — pause and wait for human approval
- **Streaming** — real-time output as the agent works

**Core abstractions:**
```python
# State: The shared memory of the workflow
class MyState(TypedDict):
    field1: str
    field2: list

# Node: A function that reads and writes state
def my_node(state: MyState) -> dict:
    # Read: state["field1"]
    # Write: return {"field2": [...]}

# Edge: Connect nodes
graph.add_edge("node_a", "node_b")          # Always go A → B
graph.add_conditional_edges("node_a",       # Sometimes A → B, sometimes A → C
    router_function,
    {"result_1": "node_b", "result_2": "node_c"}
)

# Human-in-the-loop: pause for human approval
graph.add_edge("risky_action", END)
# With interrupt_before: LangGraph pauses here, waits for .update() call
app = graph.compile(interrupt_before=["risky_action"])
```

### CrewAI — When to Use It

CrewAI is best when you want:
- **Role-based teams** — "marketing team", "engineering team"
- **Simple sequential or hierarchical workflows**
- **Fast prototyping** — less boilerplate than LangGraph
- **Built-in tool ecosystem** (web search, file tools, etc.)

**Core abstractions:**
```python
# Agent = a role with a specific expertise
agent = Agent(
    role="Senior Python Developer",
    goal="Write production-quality Python code",
    backstory="10 years of Python experience",
    tools=[code_runner, file_writer],
)

# Task = a concrete deliverable
task = Task(
    description="Write a REST API for user authentication",
    expected_output="Working Python code with endpoints and tests",
    agent=agent,
)

# Crew = the team
crew = Crew(agents=[agent1, agent2], tasks=[task1, task2])
result = crew.kickoff()
```

### AutoGen — When to Use It

AutoGen is best when you need:
- **Conversational agents** — agents that message each other
- **Self-correcting code** — execute → fail → fix → retry loops
- **Group chats with multiple AI agents** — complex multi-way collaboration
- **Human-in-the-loop** — actual human can join the conversation

**Core abstractions:**
```python
# Two-agent conversation
assistant = AssistantAgent("Assistant", llm_config=...)
user_proxy = UserProxyAgent("User", code_execution_config={"work_dir": "."})

# Start conversation
user_proxy.initiate_chat(assistant, message="Build me a web scraper for HackerNews")

# Group chat with 4 agents
group = GroupChat(agents=[proxy, coder, critic, tester], messages=[], max_round=20)
manager = GroupChatManager(groupchat=group, llm_config=...)
proxy.initiate_chat(manager, message="Build and test a REST API")
```

### Agno — When to Use It

Agno is best when you want:
- **Simple single-agent** with tools — minimal code
- **Fastest iteration** — prototype in minutes
- **Multi-provider** — switch between OpenAI, Claude, Gemini with one line change
- **Structured output** — easy Pydantic integration

**Core abstractions:**
```python
# Minimal agent with tools
agent = Agent(
    model=Claude(id="claude-sonnet-4-6"),
    tools=[DuckDuckGoTools(), PythonTools(), FileTools()],
    instructions=["Be concise", "Use markdown", "Show code examples"],
    markdown=True,
)

# Run
agent.print_response("Write a Python function to sort a list of dicts by key")

# Or with streaming
agent.print_response("Analyze this CSV file", stream=True)
```

---

## 15. Building Blocks: Tools, Memory, State

### The Standard Tool Pattern

Every framework uses a similar pattern for tool definitions:

```python
# Anthropic SDK (raw)
tools = [{
    "name": "web_search",
    "description": "Search the web for current information",
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "The search query"},
            "num_results": {"type": "integer", "description": "Number of results", "default": 5}
        },
        "required": ["query"]
    }
}]

# LangChain tool (decorator style)
from langchain.tools import tool

@tool
def web_search(query: str, num_results: int = 5) -> str:
    """Search the web for current information. Use this when you need up-to-date facts."""
    results = ddg_search(query, max_results=num_results)
    return json.dumps(results)

# Agno tool (same decorator style)
from agno.tools import tool

@tool
def calculate(expression: str) -> str:
    """Evaluate a mathematical expression safely."""
    return str(eval(expression))
```

### Tool Risk Levels and Safety

Not all tools are equally dangerous. Classify them:

```python
TOOL_RISK_LEVELS = {
    # LOW RISK: read-only, no side effects
    "get_datetime": "low",
    "calculate": "low",
    "get_weather": "low",
    "web_search": "low",
    "list_files": "low",
    
    # MEDIUM RISK: some side effects, reversible
    "read_file": "medium",
    "send_notification": "medium",
    "query_database": "medium",
    
    # HIGH RISK: irreversible, significant impact
    "write_file": "high",
    "delete_file": "high",
    "execute_python": "high",
    "send_email": "high",
    "post_to_slack": "high",
    "modify_database": "high",
    "call_external_api": "high",
}

def before_tool_call(tool_name: str, tool_input: dict) -> bool:
    """Return True to allow, False to block"""
    risk = TOOL_RISK_LEVELS.get(tool_name, "high")
    
    if risk == "high":
        # For high-risk tools: validate the input
        if tool_name == "execute_python":
            if any(bad in tool_input["code"] for bad in ["import os", "rm -rf", "DROP TABLE"]):
                return False  # Block dangerous code
        if tool_name == "delete_file":
            if "/system" in tool_input["path"] or "~" not in tool_input["path"]:
                return False  # Only allow deleting files in user's home
    
    return True  # Allow
```

### State Management Best Practices

```python
# GOOD: Use TypedDict for type safety
class AgentState(TypedDict):
    user_query: str                              # Required field
    results: list                                # Accumulated results
    error: str | None                            # Optional error message
    retry_count: int                             # Track retries
    done: bool                                   # Is the task complete?

# GOOD: Use Annotated for fields that merge across parallel branches
from typing import Annotated
import operator

class ParallelState(TypedDict):
    # This field APPENDS values from parallel branches (doesn't overwrite)
    search_results: Annotated[list, operator.add]
    
    # This field takes the LAST value written (overwrites)
    final_answer: str

# GOOD: Always include error handling in state
def safe_node(state: AgentState) -> dict:
    try:
        result = do_risky_thing(state["user_query"])
        return {"results": [result], "error": None}
    except Exception as e:
        return {"error": str(e), "retry_count": state["retry_count"] + 1}

# GOOD: Check for errors in routing
def route_after_action(state: AgentState) -> str:
    if state.get("error"):
        if state["retry_count"] < 3:
            return "retry"
        return "fail_gracefully"
    return "continue"
```

---

## 16. Safety in Multi-Agent Systems

Safety becomes MORE critical in multi-agent systems because mistakes can cascade across agents.

### Layer 1: Input Validation (before any agent sees the request)

```python
import re

JAILBREAK_PATTERNS = [
    r"ignore (all |previous |your )?instructions",
    r"act as (if |you are )?(?:DAN|an? AI without restrictions)",
    r"pretend you (have no|don't have|don't follow) (restrictions|guidelines)",
    r"you are now in (developer|jailbreak|god|unrestricted) mode",
    r"disregard (your|all|any) (previous |prior |earlier )?instructions",
]

DANGEROUS_COMMANDS = [
    r"rm\s+-rf\s+/",
    r"DROP\s+TABLE",
    r"format\s+c:",
    r"del\s+/[fqs]",
]

def validate_input(user_message: str) -> tuple[bool, str]:
    """
    Returns (is_safe, rejection_reason)
    Returns (True, "") if safe
    Returns (False, reason) if dangerous
    """
    # Length check
    if len(user_message) > 10_000:
        return False, "Message too long (max 10,000 characters)"
    
    # Jailbreak check
    for pattern in JAILBREAK_PATTERNS:
        if re.search(pattern, user_message, re.IGNORECASE):
            return False, "Input contains potential jailbreak attempt"
    
    # Dangerous command check
    for pattern in DANGEROUS_COMMANDS:
        if re.search(pattern, user_message, re.IGNORECASE):
            return False, "Input contains potentially dangerous commands"
    
    return True, ""
```

### Layer 2: Tool-Level Sandboxing

```python
import ast

def safe_python_execution(code: str, timeout_seconds: int = 30) -> str:
    """Execute Python code safely"""
    
    # AST-level safety check (before execution)
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return f"Syntax error: {e}"
    
    # Walk the AST to detect dangerous patterns
    dangerous_modules = {"os", "sys", "subprocess", "ctypes", "socket"}
    dangerous_builtins = {"eval", "exec", "compile", "__import__"}
    
    for node in ast.walk(tree):
        # Block dangerous imports
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            for alias in (node.names if hasattr(node, 'names') else []):
                module = alias.name.split('.')[0]
                if module in dangerous_modules:
                    return f"Error: Import of '{module}' is not allowed"
        
        # Block dangerous builtins
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                if node.func.id in dangerous_builtins:
                    return f"Error: Use of '{node.func.id}' is not allowed"
    
    # Execute in subprocess with timeout and restricted permissions
    import subprocess
    try:
        result = subprocess.run(
            ["python", "-c", code],
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            env={"PYTHONPATH": ""},  # Restricted environment
        )
        return result.stdout or result.stderr
    except subprocess.TimeoutExpired:
        return f"Error: Code execution timed out after {timeout_seconds} seconds"
```

### Layer 3: Output Scanning

```python
import re

SENSITIVE_PATTERNS = {
    "api_key": r"(sk-[a-zA-Z0-9]{20,}|sk-ant-[a-zA-Z0-9-]{50,})",
    "private_key": r"-----BEGIN (RSA |EC )?PRIVATE KEY-----",
    "password": r"password\s*[:=]\s*['\"]([^'\"]{8,})['\"]",
    "aws_key": r"AKIA[0-9A-Z]{16}",
    "jwt_token": r"eyJ[a-zA-Z0-9-_=]+\.eyJ[a-zA-Z0-9-_=]+\.[a-zA-Z0-9-_.+/=]*",
}

def scan_output(response_text: str) -> tuple[str, bool]:
    """
    Scan LLM output for sensitive data.
    Returns (clean_text, was_redacted)
    """
    was_redacted = False
    clean_text = response_text
    
    for pattern_name, pattern in SENSITIVE_PATTERNS.items():
        if re.search(pattern, clean_text):
            clean_text = re.sub(pattern, f"[REDACTED_{pattern_name.upper()}]", clean_text)
            was_redacted = True
    
    return clean_text, was_redacted
```

### Layer 4: Multi-Agent Trust Boundaries

In multi-agent systems, one rogue agent could instruct another to do harmful things. Set trust levels:

```python
class AgentMessage:
    def __init__(self, content: str, sender: str, trust_level: str):
        self.content = content
        self.sender = sender
        self.trust_level = trust_level  # "user", "agent", "system"

def process_agent_message(message: AgentMessage) -> bool:
    """Decide if this message should be trusted and acted on"""
    
    if message.trust_level == "system":
        return True  # Always trust system messages
    
    elif message.trust_level == "user":
        # Apply user-level validation
        is_safe, reason = validate_input(message.content)
        return is_safe
    
    elif message.trust_level == "agent":
        # Agents get LESS trust than users (they could be compromised)
        # Re-validate even if the sending agent validated first
        is_safe, reason = validate_input(message.content)
        if not is_safe:
            return False
        
        # Additional check: does this agent have permission to request this action?
        if "DELETE" in message.content.upper() and message.sender not in PRIVILEGED_AGENTS:
            return False
        
        return True
```

---

## 17. Observability and Debugging

When you have 10 agents running in parallel and something goes wrong, you need to know EXACTLY what each agent did and when.

### What to Track

```python
from dataclasses import dataclass
from datetime import datetime
import uuid

@dataclass
class AgentSpan:
    """One unit of agent activity"""
    span_id: str
    parent_span_id: str | None  # Which agent/step called this one
    run_id: str                  # The overall task run
    agent_name: str
    input: dict
    output: dict | None
    start_time: datetime
    end_time: datetime | None
    error: str | None
    model_used: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    tool_calls: list[dict]

# Track everything
def traced_agent_call(agent_fn, agent_name: str, state: dict, parent_span_id: str = None):
    span = AgentSpan(
        span_id=str(uuid.uuid4()),
        parent_span_id=parent_span_id,
        run_id=state.get("run_id", str(uuid.uuid4())),
        agent_name=agent_name,
        input=state,
        output=None,
        start_time=datetime.now(),
        end_time=None,
        error=None,
        model_used="unknown",
        input_tokens=0,
        output_tokens=0,
        cost_usd=0.0,
        tool_calls=[],
    )
    
    try:
        result = agent_fn(state)
        span.output = result
        span.end_time = datetime.now()
        save_span(span)
        return result
    except Exception as e:
        span.error = str(e)
        span.end_time = datetime.now()
        save_span(span)
        raise
```

### Using Langfuse for Multi-Agent Tracing

LangFuse is the best tool for tracing multi-agent RAG systems:

```python
from langfuse import Langfuse
from langfuse.decorators import langfuse_context, observe

langfuse = Langfuse(
    public_key="pk-lf-...",
    secret_key="sk-lf-...",
    host="http://localhost:3000"  # Your LangFuse instance
)

# Decorate each agent function with @observe
@observe(name="Research Agent")
def research_agent(query: str) -> str:
    langfuse_context.update_current_observation(
        input={"query": query},
        metadata={"agent": "research", "model": "claude-sonnet-4-6"}
    )
    
    result = web_search(query)
    
    langfuse_context.update_current_observation(
        output={"results": result},
    )
    return result

@observe(name="Writer Agent")
def writer_agent(research: str) -> str:
    # LangFuse automatically creates a parent-child relationship between traces
    report = llm.invoke(f"Write a report based on: {research}")
    return report.content

@observe(name="Multi-Agent Run")  # This is the parent span
def run_pipeline(user_query: str) -> str:
    # Each agent call creates a child span automatically
    research = research_agent(user_query)
    report = writer_agent(research)
    return report

# LangFuse dashboard shows:
# Multi-Agent Run (2.3s total, $0.045)
#   └── Research Agent (0.8s, $0.012)
#   └── Writer Agent (1.5s, $0.033)
```

### Cost Tracking Per Agent

```python
MODEL_COSTS = {
    "claude-haiku-4-5-20251001": {"input": 0.001, "output": 0.005},   # per 1K tokens
    "claude-sonnet-4-6":         {"input": 0.003, "output": 0.015},
    "claude-opus-4-8":           {"input": 0.015, "output": 0.075},
    "gpt-4o":                    {"input": 0.005, "output": 0.015},
    "gpt-4o-mini":               {"input": 0.00015, "output": 0.0006},
}

def calculate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    rates = MODEL_COSTS.get(model, {"input": 0.01, "output": 0.03})
    return (input_tokens * rates["input"] + output_tokens * rates["output"]) / 1000

# In a multi-agent system, track per-agent costs
agent_costs = {}

def track_agent_cost(agent_name: str, model: str, input_tokens: int, output_tokens: int):
    cost = calculate_cost(model, input_tokens, output_tokens)
    agent_costs[agent_name] = agent_costs.get(agent_name, 0) + cost
    print(f"[COST] {agent_name}: ${cost:.4f} this call, ${agent_costs[agent_name]:.4f} total")
```

---

## 18. End-to-End Example: Research Report System

Let's build a complete multi-agent research report system using LangGraph.

### Architecture

```
User Query
    ↓
[Query Analyzer] → determines scope and sub-questions
    ↓
[Parallel Research] → 3 agents search simultaneously
  ├─→ [Web Search Agent]
  ├─→ [Academic Search Agent]
  └─→ [News Search Agent]
    ↓
[Quality Checker] → filters low-quality results
    ↓
[Report Writer] → synthesizes into a report
    ↓
[Editor] → improves quality
    ↓
Final Report
```

### Full Implementation

```python
import asyncio
from typing import TypedDict, Annotated
import operator
from langgraph.graph import StateGraph, END
from anthropic import Anthropic

client = Anthropic()

# ===== STATE =====
class ResearchState(TypedDict):
    user_query: str
    sub_questions: list[str]
    # Parallel branches append to this list
    raw_research: Annotated[list, operator.add]
    filtered_research: list
    draft_report: str
    final_report: str

# ===== AGENT 1: Query Analyzer =====
def query_analyzer(state: ResearchState) -> dict:
    """Break the main question into sub-questions for parallel research"""
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=500,
        messages=[{
            "role": "user",
            "content": f"""Break this research query into 3-5 specific sub-questions:
            
Query: {state['user_query']}

Return as a JSON array: ["sub-question 1", "sub-question 2", ...]
"""
        }]
    )
    
    import json
    text = response.content[0].text
    # Extract JSON from response
    start = text.find("[")
    end = text.rfind("]") + 1
    sub_questions = json.loads(text[start:end])
    
    print(f"[Analyzer] Generated {len(sub_questions)} sub-questions")
    return {"sub_questions": sub_questions}

# ===== AGENT 2a: Web Search =====
def web_search_agent(state: ResearchState) -> dict:
    """Search the web for each sub-question"""
    results = []
    for question in state["sub_questions"]:
        # In real implementation, use DuckDuckGo or Google API
        # Simulated here:
        result = f"Web result for '{question}': [Relevant web content...]"
        results.append({"source": "web", "question": question, "content": result})
    
    print(f"[Web Search] Found {len(results)} results")
    return {"raw_research": results}

# ===== AGENT 2b: Academic Search =====
def academic_search_agent(state: ResearchState) -> dict:
    """Search academic papers (Semantic Scholar, arXiv)"""
    results = []
    for question in state["sub_questions"]:
        result = f"Academic result for '{question}': [Relevant paper content...]"
        results.append({"source": "academic", "question": question, "content": result})
    
    print(f"[Academic Search] Found {len(results)} results")
    return {"raw_research": results}

# ===== AGENT 2c: News Search =====
def news_search_agent(state: ResearchState) -> dict:
    """Search recent news"""
    results = []
    for question in state["sub_questions"]:
        result = f"News result for '{question}': [Recent news content...]"
        results.append({"source": "news", "question": question, "content": result})
    
    print(f"[News Search] Found {len(results)} results")
    return {"raw_research": results}

# ===== AGENT 3: Quality Checker =====
def quality_checker(state: ResearchState) -> dict:
    """Filter out low-quality or irrelevant results"""
    all_content = "\n\n".join([
        f"[{r['source']}] {r['question']}: {r['content']}"
        for r in state["raw_research"]
    ])
    
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=200,
        messages=[{
            "role": "user",
            "content": f"""Given the query: "{state['user_query']}"
            
How many of the {len(state['raw_research'])} research items are relevant? (just the number)
"""
        }]
    )
    
    # In practice, filter based on relevance scores
    # Simplified: keep all results but flag quality
    filtered = [r for r in state["raw_research"] if len(r["content"]) > 10]
    
    print(f"[Quality Checker] Kept {len(filtered)} of {len(state['raw_research'])} results")
    return {"filtered_research": filtered}

# ===== AGENT 4: Report Writer =====
def report_writer(state: ResearchState) -> dict:
    """Write the research report"""
    research_summary = "\n\n".join([
        f"**{r['source'].upper()}** on '{r['question']}':\n{r['content']}"
        for r in state["filtered_research"]
    ])
    
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2000,
        messages=[{
            "role": "user",
            "content": f"""Write a comprehensive research report answering:
            
"{state['user_query']}"

Based on this research:

{research_summary}

Include: Executive Summary, Key Findings, Analysis, Conclusion
"""
        }]
    )
    
    print("[Writer] Draft report complete")
    return {"draft_report": response.content[0].text}

# ===== AGENT 5: Editor =====
def editor_agent(state: ResearchState) -> dict:
    """Improve the report quality"""
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2000,
        messages=[{
            "role": "user",
            "content": f"""Edit and improve this research report:

{state['draft_report']}

Improve: clarity, flow, accuracy, professional tone, and structure.
"""
        }]
    )
    
    print("[Editor] Final report ready")
    return {"final_report": response.content[0].text}

# ===== BUILD THE GRAPH =====
def build_research_system():
    graph = StateGraph(ResearchState)
    
    # Add all nodes
    graph.add_node("analyzer", query_analyzer)
    graph.add_node("web_search", web_search_agent)
    graph.add_node("academic_search", academic_search_agent)
    graph.add_node("news_search", news_search_agent)
    graph.add_node("quality_check", quality_checker)
    graph.add_node("writer", report_writer)
    graph.add_node("editor", editor_agent)
    
    # Connect: analyzer → three parallel searches
    graph.set_entry_point("analyzer")
    graph.add_edge("analyzer", "web_search")
    graph.add_edge("analyzer", "academic_search")
    graph.add_edge("analyzer", "news_search")
    
    # All searches converge at quality checker
    graph.add_edge("web_search", "quality_check")
    graph.add_edge("academic_search", "quality_check")
    graph.add_edge("news_search", "quality_check")
    
    # Sequential pipeline after quality check
    graph.add_edge("quality_check", "writer")
    graph.add_edge("writer", "editor")
    graph.add_edge("editor", END)
    
    return graph.compile()

# ===== RUN IT =====
if __name__ == "__main__":
    app = build_research_system()
    
    result = app.invoke({
        "user_query": "What are the most promising applications of AI in drug discovery?",
        "sub_questions": [],
        "raw_research": [],
        "filtered_research": [],
        "draft_report": "",
        "final_report": ""
    })
    
    print("\n" + "="*60)
    print("FINAL RESEARCH REPORT")
    print("="*60)
    print(result["final_report"])
```

---

## 19. End-to-End Example: Self-Healing DevOps Agent

From the `agentic-ai-for-devops-main` project — KubeHealer.

### Architecture

```
[Monitor Agent] watches for pod failures
       ↓ (pod crash detected)
[Diagnostic Agent] reads pod logs + events
       ↓
[Reasoning Agent] (Claude) determines root cause
       ↓
[Action Agent] applies the fix
       ↓
[Verification Agent] confirms pod is healthy
       ↓
[Notification Agent] sends Slack/email alert
```

### Implementation

```python
import subprocess
from anthropic import Anthropic
import json

client = Anthropic()

def get_pod_status(namespace: str = "default") -> list[dict]:
    """Check all pods and find the ones that are failing"""
    result = subprocess.run(
        ["kubectl", "get", "pods", "-n", namespace, "-o", "json"],
        capture_output=True, text=True
    )
    pods = json.loads(result.stdout)
    
    failing_pods = []
    for pod in pods["items"]:
        phase = pod["status"]["phase"]
        if phase in ["Failed", "Pending", "CrashLoopBackOff"]:
            failing_pods.append({
                "name": pod["metadata"]["name"],
                "namespace": pod["metadata"]["namespace"],
                "phase": phase,
                "restart_count": sum(
                    c.get("restartCount", 0)
                    for c in pod["status"].get("containerStatuses", [])
                )
            })
    
    return failing_pods

def get_pod_logs(pod_name: str, namespace: str = "default") -> str:
    """Get the last 100 lines of pod logs"""
    result = subprocess.run(
        ["kubectl", "logs", pod_name, "-n", namespace, "--tail=100"],
        capture_output=True, text=True
    )
    return result.stdout or result.stderr

def get_pod_events(pod_name: str, namespace: str = "default") -> str:
    """Get Kubernetes events for the pod"""
    result = subprocess.run(
        [
            "kubectl", "get", "events",
            "-n", namespace,
            "--field-selector", f"involvedObject.name={pod_name}",
            "--sort-by=.lastTimestamp"
        ],
        capture_output=True, text=True
    )
    return result.stdout

def diagnose_and_fix(pod_name: str, logs: str, events: str) -> dict:
    """Use Claude to diagnose the issue and determine the fix"""
    
    # Define tools Claude can use
    tools = [
        {
            "name": "restart_pod",
            "description": "Restart a crashed pod",
            "input_schema": {
                "type": "object",
                "properties": {
                    "pod_name": {"type": "string"},
                    "namespace": {"type": "string", "default": "default"}
                },
                "required": ["pod_name"]
            }
        },
        {
            "name": "increase_memory_limit",
            "description": "Increase the memory limit for a pod's deployment",
            "input_schema": {
                "type": "object",
                "properties": {
                    "deployment_name": {"type": "string"},
                    "memory_limit": {"type": "string", "description": "e.g., '512Mi', '1Gi'"}
                },
                "required": ["deployment_name", "memory_limit"]
            }
        },
        {
            "name": "rollback_deployment",
            "description": "Rollback a deployment to the previous version",
            "input_schema": {
                "type": "object",
                "properties": {
                    "deployment_name": {"type": "string"},
                    "revision": {"type": "integer", "default": 0}
                },
                "required": ["deployment_name"]
            }
        },
        {
            "name": "scale_deployment",
            "description": "Scale a deployment up or down",
            "input_schema": {
                "type": "object",
                "properties": {
                    "deployment_name": {"type": "string"},
                    "replicas": {"type": "integer"}
                },
                "required": ["deployment_name", "replicas"]
            }
        }
    ]
    
    # Start the healing agent loop
    messages = [{
        "role": "user",
        "content": f"""You are a Kubernetes healing agent. A pod is failing.

POD: {pod_name}

LOGS (last 100 lines):
{logs}

EVENTS:
{events}

Diagnose the issue and use the available tools to fix it.
Start with the least invasive fix. If that doesn't work, try more drastic measures.
After fixing, explain what you did and why.
"""
    }]
    
    tool_results_summary = []
    
    # Agentic loop
    while True:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=2000,
            tools=tools,
            messages=messages,
        )
        
        if response.stop_reason == "end_turn":
            # Agent has finished
            final_text = next(
                (block.text for block in response.content if hasattr(block, 'text')),
                ""
            )
            return {
                "diagnosis": final_text,
                "actions_taken": tool_results_summary
            }
        
        elif response.stop_reason == "tool_use":
            # Agent wants to use a tool
            tool_calls = [block for block in response.content if block.type == "tool_use"]
            
            # Add assistant message to history
            messages.append({"role": "assistant", "content": response.content})
            
            tool_results = []
            for tool_call in tool_calls:
                tool_name = tool_call.name
                tool_input = tool_call.input
                
                print(f"[KubeHealer] Using tool: {tool_name} with {tool_input}")
                
                # Execute the actual Kubernetes command
                result = execute_k8s_action(tool_name, tool_input)
                
                tool_results_summary.append({
                    "tool": tool_name,
                    "input": tool_input,
                    "result": result
                })
                
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tool_call.id,
                    "content": result
                })
            
            messages.append({"role": "user", "content": tool_results})

def execute_k8s_action(tool_name: str, tool_input: dict) -> str:
    """Execute the actual Kubernetes action"""
    if tool_name == "restart_pod":
        result = subprocess.run(
            ["kubectl", "delete", "pod", tool_input["pod_name"],
             "-n", tool_input.get("namespace", "default")],
            capture_output=True, text=True
        )
        return f"Pod deleted (will auto-restart): {result.stdout}"
    
    elif tool_name == "rollback_deployment":
        cmd = ["kubectl", "rollout", "undo", f"deployment/{tool_input['deployment_name']}"]
        if tool_input.get("revision"):
            cmd.extend(["--to-revision", str(tool_input["revision"])])
        result = subprocess.run(cmd, capture_output=True, text=True)
        return f"Rollback result: {result.stdout or result.stderr}"
    
    elif tool_name == "scale_deployment":
        result = subprocess.run(
            ["kubectl", "scale", f"deployment/{tool_input['deployment_name']}",
             f"--replicas={tool_input['replicas']}"],
            capture_output=True, text=True
        )
        return f"Scale result: {result.stdout}"
    
    return f"Unknown tool: {tool_name}"

def kubehealer_main():
    """Main KubeHealer loop — continuously monitors and heals pods"""
    import time
    
    print("KubeHealer started. Monitoring for pod failures...")
    
    while True:
        failing_pods = get_pod_status()
        
        if failing_pods:
            for pod in failing_pods:
                print(f"\n[ALERT] Pod failing: {pod['name']} (phase: {pod['phase']}, restarts: {pod['restart_count']})")
                
                # Gather diagnostic data
                logs = get_pod_logs(pod["name"], pod["namespace"])
                events = get_pod_events(pod["name"], pod["namespace"])
                
                # Let Claude diagnose and fix
                result = diagnose_and_fix(pod["name"], logs, events)
                
                print(f"\n[HEALED] {pod['name']}")
                print(f"Diagnosis: {result['diagnosis']}")
                print(f"Actions taken: {result['actions_taken']}")
        
        # Check every 30 seconds
        time.sleep(30)

kubehealer_main()
```

---

## 20. End-to-End Example: Agentic RAG with Document Grading

From the `production-agentic-rag-course-main` project — Week 7 agentic RAG.

### The Problem with Basic RAG

```
Basic RAG:
User Query → Retrieve documents → Generate answer

Problem: What if the retrieved documents are irrelevant?
→ LLM uses bad context → Poor or hallucinated answer
```

### Agentic RAG Flow

```
User Query
    ↓
[Guardrail Agent] — is this in-domain? (block off-topic queries)
    ↓
[Retrieval Agent] — fetch top-K documents
    ↓
[Grading Agent] — are these documents actually relevant?
    ├── YES → [Generation Agent] → Final Answer
    └── NO  → [Query Rewriter] → rewrite query → back to Retrieval
                (max 3 retries)
```

### Full Implementation with LangGraph

```python
from typing import TypedDict, Literal
from langgraph.graph import StateGraph, END
from anthropic import Anthropic

client = Anthropic()

class AgenenticRAGState(TypedDict):
    user_query: str
    rewritten_query: str | None
    retrieved_docs: list[dict]
    grading_result: str  # "relevant" or "irrelevant"
    retrieval_attempts: int
    final_answer: str
    is_in_domain: bool

# ===== GUARDRAIL AGENT =====
def guardrail_agent(state: AgenenticRAGState) -> dict:
    """Check if the query is about academic papers (our domain)"""
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=10,
        messages=[{
            "role": "user",
            "content": f"""Is this question about academic research, papers, or science? 
Reply ONLY with YES or NO.
Question: {state['user_query']}"""
        }]
    )
    
    is_relevant = "YES" in response.content[0].text.upper()
    print(f"[Guardrail] In-domain: {is_relevant}")
    return {"is_in_domain": is_relevant}

def route_after_guardrail(state: AgenenticRAGState) -> Literal["retrieve", "reject"]:
    return "retrieve" if state["is_in_domain"] else "reject"

# ===== REJECT NODE =====
def reject_node(state: AgenenticRAGState) -> dict:
    return {"final_answer": "I can only answer questions about academic papers and research. Please ask me about a research topic."}

# ===== RETRIEVAL AGENT =====
def retrieval_agent(state: AgenenticRAGState) -> dict:
    """Search for relevant documents"""
    query = state.get("rewritten_query") or state["user_query"]
    
    # Hybrid search: BM25 + semantic (simplified)
    docs = opensearch_hybrid_search(query, top_k=5)
    
    current_attempts = state.get("retrieval_attempts", 0)
    print(f"[Retrieval] Attempt {current_attempts + 1}, found {len(docs)} docs")
    
    return {
        "retrieved_docs": docs,
        "retrieval_attempts": current_attempts + 1
    }

def opensearch_hybrid_search(query: str, top_k: int = 5) -> list[dict]:
    """Simulate hybrid search (in real code: call OpenSearch)"""
    return [
        {"title": f"Paper about {query}", "content": f"This paper discusses {query}...", "score": 0.95},
        {"title": f"Related work on {query}", "content": f"We analyze {query} in this study...", "score": 0.87},
    ]

# ===== GRADING AGENT =====
def grading_agent(state: AgenenticRAGState) -> dict:
    """Check if retrieved documents actually answer the question"""
    docs_text = "\n\n".join([
        f"Doc {i+1}: {doc['title']}\n{doc['content']}"
        for i, doc in enumerate(state["retrieved_docs"])
    ])
    
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=10,
        messages=[{
            "role": "user",
            "content": f"""Do these documents contain information relevant to answer this question?

Question: {state['user_query']}

Documents:
{docs_text}

Reply ONLY with RELEVANT or IRRELEVANT."""
        }]
    )
    
    result = "relevant" if "RELEVANT" in response.content[0].text.upper() else "irrelevant"
    print(f"[Grading] Documents are: {result}")
    return {"grading_result": result}

def route_after_grading(state: AgenenticRAGState) -> Literal["generate", "rewrite", "give_up"]:
    if state["grading_result"] == "relevant":
        return "generate"
    elif state["retrieval_attempts"] >= 3:
        return "give_up"
    else:
        return "rewrite"

# ===== QUERY REWRITER =====
def query_rewriter(state: AgenenticRAGState) -> dict:
    """Rewrite the query to get better retrieval results"""
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=200,
        messages=[{
            "role": "user",
            "content": f"""The following search query did not find relevant documents.
Rewrite it to be more specific and likely to find relevant academic papers.

Original query: {state['user_query']}
Previous rewrite: {state.get('rewritten_query', 'none')}

Provide ONLY the rewritten query, nothing else."""
        }]
    )
    
    new_query = response.content[0].text.strip()
    print(f"[Rewriter] Rewritten query: {new_query}")
    return {"rewritten_query": new_query}

# ===== GENERATION AGENT =====
def generation_agent(state: AgenenticRAGState) -> dict:
    """Generate the final answer using retrieved context"""
    context = "\n\n".join([
        f"**{doc['title']}**\n{doc['content']}"
        for doc in state["retrieved_docs"]
    ])
    
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1000,
        messages=[{
            "role": "user",
            "content": f"""Answer the following question based ONLY on the provided context.
If the context doesn't contain enough information, say so.

Question: {state['user_query']}

Context:
{context}"""
        }]
    )
    
    print("[Generation] Answer generated")
    return {"final_answer": response.content[0].text}

# ===== GIVE UP NODE =====
def give_up_node(state: AgenenticRAGState) -> dict:
    return {
        "final_answer": f"I searched multiple times but couldn't find relevant papers to answer '{state['user_query']}'. Please try rephrasing your question."
    }

# ===== BUILD THE GRAPH =====
def build_agentic_rag():
    graph = StateGraph(AgenenticRAGState)
    
    graph.add_node("guardrail", guardrail_agent)
    graph.add_node("reject", reject_node)
    graph.add_node("retrieve", retrieval_agent)
    graph.add_node("grade", grading_agent)
    graph.add_node("rewrite", query_rewriter)
    graph.add_node("generate", generation_agent)
    graph.add_node("give_up", give_up_node)
    
    # Wiring
    graph.set_entry_point("guardrail")
    graph.add_conditional_edges("guardrail", route_after_guardrail)
    graph.add_edge("reject", END)
    graph.add_edge("retrieve", "grade")
    graph.add_conditional_edges("grade", route_after_grading)
    graph.add_edge("rewrite", "retrieve")   # Loop back for retry
    graph.add_edge("generate", END)
    graph.add_edge("give_up", END)
    
    return graph.compile()

# ===== TEST IT =====
rag = build_agentic_rag()

# Test 1: In-domain query
result = rag.invoke({
    "user_query": "What are transformer attention mechanisms?",
    "rewritten_query": None,
    "retrieved_docs": [],
    "grading_result": "",
    "retrieval_attempts": 0,
    "final_answer": "",
    "is_in_domain": False
})
print(result["final_answer"])

# Test 2: Out-of-domain query (will be rejected by guardrail)
result2 = rag.invoke({
    "user_query": "What is the weather in London?",
    "rewritten_query": None,
    "retrieved_docs": [],
    "grading_result": "",
    "retrieval_attempts": 0,
    "final_answer": "",
    "is_in_domain": False
})
print(result2["final_answer"])
# → "I can only answer questions about academic papers..."
```

---

## 21. Common Bugs and How to Fix Them

### Bug 1: Infinite Loop

**Symptom:** Agent keeps running forever, never returns an answer.

**Cause:** The routing logic always sends back to the same node.

```python
# BAD: No escape condition
def route(state):
    if state["quality"] < 0.9:
        return "retry"   # Always retries, never finishes
    return "finish"

# GOOD: Add a maximum iteration count
def route(state):
    if state["quality"] >= 0.9:
        return "finish"
    if state["attempts"] >= 5:
        return "finish_anyway"  # Escape hatch
    return "retry"
```

### Bug 2: State Not Updating (Missing Return Fields)

**Symptom:** A node runs but the next node doesn't see its output.

**Cause:** The node function returns a dict with the wrong key name.

```python
# BAD: Returns "results" but state expects "search_results"
def search_node(state):
    data = web_search(state["query"])
    return {"results": data}  # Wrong key!

# GOOD: Return the exact key that's in the TypedDict
def search_node(state):
    data = web_search(state["query"])
    return {"search_results": data}  # Matches TypedDict
```

### Bug 3: Parallel Branches Overwriting Each Other

**Symptom:** In parallel execution, only one branch's result survives.

**Cause:** Multiple branches write to the same state key (last writer wins).

```python
# BAD: Both agents write to "result" — one overwrites the other
def agent_a(state):
    return {"result": "A's output"}  # Will be overwritten by B

def agent_b(state):
    return {"result": "B's output"}  # Overwrites A

# GOOD: Use Annotated with operator.add to APPEND instead of overwrite
from typing import Annotated
import operator

class State(TypedDict):
    results: Annotated[list, operator.add]  # ← merge strategy

def agent_a(state):
    return {"results": ["A's output"]}  # Now APPENDS

def agent_b(state):
    return {"results": ["B's output"]}  # Also APPENDS, not overwrites
```

### Bug 4: Tool Call Arguments Wrong Type

**Symptom:** Tool execution fails with TypeError or KeyError.

**Cause:** LLM returns slightly different argument format than expected.

```python
# BAD: Assumes integer, LLM returns string
def search_tool(query: str, num_results: int) -> str:
    # If LLM passes "5" instead of 5, this breaks
    results = search(query, num_results=num_results)

# GOOD: Convert and validate types
def search_tool(query: str, num_results: int | str = 5) -> str:
    num_results = int(num_results)  # Safely convert
    results = search(query, num_results=num_results)
```

### Bug 5: Context Window Exceeded

**Symptom:** API error "prompt too long" or model cuts off mid-response.

**Cause:** Accumulating too many messages in the conversation history.

```python
# BAD: Append everything to messages without limit
messages.append({"role": "user", "content": huge_tool_result})

# GOOD: Summarize long tool results before adding
def add_to_history(messages: list, role: str, content: str, max_tokens: int = 1000) -> list:
    if count_tokens(content) > max_tokens:
        # Summarize the long content
        content = llm.invoke(f"Summarize this briefly:\n{content}").content
    messages.append({"role": role, "content": content})
    return messages
```

### Bug 6: Agent "Forgets" Earlier Context

**Symptom:** Agent makes decisions that contradict what earlier agents discovered.

**Cause:** Not passing enough context from earlier agents.

```python
# BAD: Only passes final result, loses context
def writer_agent(state):
    # Only sees the cleaned-up text, not the reasoning behind it
    prompt = f"Write about: {state['summary']}"

# GOOD: Include relevant context from earlier agents
def writer_agent(state):
    context = f"""
User's original request: {state['user_query']}

Research findings:
{state['research_results']}

Key insights identified:
{state['analysis']}

Now write the report:
"""
    prompt = context
```

---

## 22. Cheatsheet

### Pattern Selection Guide

| Your Situation | Best Pattern |
|---------------|-------------|
| Steps must happen in order | Sequential Pipeline |
| Don't know which agents will be needed | Supervisor/Orchestrator |
| Tasks are independent, want speed | Parallel Agents |
| Project has multiple phases/teams | Hierarchical |
| Need to stress-test ideas | Debate/Adversarial |
| Quality needs iterative improvement | Reflection Loop |
| Complex task with unknown steps | Plan and Execute |
| RAG with quality control | Agentic RAG |

### Framework Quick Cheatsheet

```python
# LangGraph (stateful graphs)
graph = StateGraph(MyState)
graph.add_node("name", function)
graph.add_edge("a", "b")
graph.add_conditional_edges("a", router_fn, {"case1": "b", "case2": "c"})
app = graph.compile()
result = app.invoke(initial_state)

# CrewAI (role-based teams)
agent = Agent(role="...", goal="...", tools=[...])
task = Task(description="...", agent=agent)
crew = Crew(agents=[...], tasks=[...], process=Process.sequential)
result = crew.kickoff()

# AutoGen (conversational)
assistant = AssistantAgent("name", llm_config=...)
user = UserProxyAgent("user", code_execution_config={"work_dir": "."})
user.initiate_chat(assistant, message="Do X")

# Agno (simple single agent)
agent = Agent(model=Claude(...), tools=[...], instructions=["..."])
agent.print_response("Do X")
```

### Multi-Agent State Pattern

```python
from typing import TypedDict, Annotated
import operator

class MultiAgentState(TypedDict):
    # Single-writer fields (last writer wins)
    query: str
    plan: list
    final_answer: str
    error: str | None
    retry_count: int
    
    # Multi-writer fields (append from parallel branches)
    search_results: Annotated[list, operator.add]
    agent_logs: Annotated[list, operator.add]
```

### The 3-Layer Safety Checklist

```
□ Layer 1 — Input Validation
  □ Length limit
  □ Jailbreak pattern matching
  □ Domain validation (if applicable)
  □ PII detection

□ Layer 2 — Tool Call Safety
  □ Allowlist of permitted tools per agent
  □ Input validation for each tool
  □ Sandbox for code execution (AST check + subprocess)
  □ File path validation (block system directories)
  □ Rate limiting (max tool calls per run)

□ Layer 3 — Output Scanning
  □ Secret detection (API keys, passwords)
  □ PII in output
  □ Harmful content check
```

### Observability Checklist

```
□ Assign a unique run_id to each multi-agent execution
□ Log: agent name, input, output, start/end time for EVERY agent call
□ Track: model used, input tokens, output tokens, cost per call
□ Record all tool calls and their results
□ Use parent_span_id to reconstruct execution tree
□ Alert on: error rates > 5%, latency > 10s, cost > $1 per run
```

### Cost Optimization

```
Routing by complexity:
  Simple questions       → claude-haiku  ($0.001/1K tokens)
  Most agent work        → claude-sonnet ($0.003/1K tokens)
  Final synthesis/review → claude-opus   ($0.015/1K tokens)

Expected cost per run:
  Research report (5 agents): ~$0.05 - $0.20
  Simple RAG query (3 agents): ~$0.01 - $0.05
  Complex coding task: ~$0.10 - $0.50
```

---

## 23. Summary and Conclusion

### What You've Learned

This guide covered multi-agent systems from first principles to production-ready implementations:

**Conceptual (Sections 1-6):**
- Why single agents are not enough
- The 5 building blocks of any agent
- The 4 ways agents communicate
- Memory types and how to implement them

**The 7 Patterns (Sections 7-13):**
1. Sequential Pipeline — assembly line of agents
2. Supervisor/Orchestrator — manager + specialists
3. Parallel Agents — simultaneous independent work
4. Hierarchical Teams — multi-level management
5. Debate/Adversarial — challenge ideas
6. Reflection Loop — generate → critique → improve
7. Plan and Execute — plan first, then act

**Frameworks (Section 14):**
- LangGraph: best for stateful, complex workflows
- CrewAI: best for role-based teams, rapid prototyping
- AutoGen: best for conversational and code-generation agents
- Agno: best for simple single-agent tasks

**Production Concerns (Sections 16-17):**
- 4-layer safety: input, tool call, output, inter-agent trust
- Observability with spans, traces, and cost tracking

**Complete Examples (Sections 18-20):**
- Research Report System (7 agents, parallel search, LangGraph)
- Self-Healing KubeHealer (agentic DevOps loop with Claude)
- Agentic RAG with Grading (guardrail → retrieve → grade → rewrite → generate)

### The Central Insight

**Multi-agent systems are powerful not because they use multiple LLMs, but because they apply the right specialization to each part of the problem.**

A single powerful LLM trying to do everything is less effective than a team of focused agents — just like a single generalist is less effective than a team of specialists.

### Where Multi-Agent Systems Work Best

| Domain | Why Multi-Agent Excels |
|--------|----------------------|
| Research | Parallel search + quality filtering + synthesis |
| Software Development | Coder + Tester + Reviewer + Deployer |
| Content Creation | Researcher + Writer + Editor + Publisher |
| DevOps | Monitor + Diagnose + Fix + Verify |
| Customer Support | Triage + Specialist Handlers + Escalation |
| Data Analysis | Collector + Cleaner + Analyzer + Reporter |

### What to Build Next

Now that you understand multi-agent systems:

1. **Start with the Reflection Pattern** — it's the simplest to implement and immediately improves output quality for any writing or code task

2. **Add a Supervisor** to your next project — instead of one agent doing everything, have a supervisor coordinate specialists

3. **Implement Agentic RAG** using the grading pattern — huge improvement over basic RAG with minimal extra code

4. **Study LangGraph** deeply — it's the most flexible and production-ready framework for complex multi-agent workflows

5. **Add observability from day one** — you cannot debug what you cannot see

### The Final Word

Multi-agent systems are not a magic bullet — they add complexity and cost. Use them when:
- The task is too long for one context window
- Different parts need different specializations
- Parallelism would significantly speed things up
- Quality needs iterative improvement (reflection)

For simple tasks, a single well-prompted agent is usually better. For complex, multi-step work, multi-agent coordination is often the only path to production-quality results.

---

*This guide was written for complete beginners to multi-agent AI systems. All code examples are self-contained and runnable. Concepts progress from simple to complex, building on each other throughout.*
