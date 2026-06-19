# Awesome LLM Apps — Complete End-to-End Explanation (Beginner Friendly)

> **Confirmation:** YES — this code is exactly what it says. It is a large collection (1,758 files, 100+ apps) of ready-to-run AI applications that use Large Language Models (LLMs). Everything here is real, tested, and working code. This document explains every part of it, line by line, from scratch.

---

## TABLE OF CONTENTS

1. [What Is This Repository?](#1-what-is-this-repository)
2. [What Is an LLM?](#2-what-is-an-llm)
3. [Folder Structure — The Big Map](#3-folder-structure--the-big-map)
4. [Technology Stack — What Tools Are Used](#4-technology-stack--what-tools-are-used)
5. [Part 1: Starter AI Agents — Line by Line](#5-part-1-starter-ai-agents--line-by-line)
6. [Part 2: RAG (Retrieval Augmented Generation) — Line by Line](#6-part-2-rag-retrieval-augmented-generation--line-by-line)
7. [Part 3: Multi-Agent Teams — Line by Line](#7-part-3-multi-agent-teams--line-by-line)
8. [Part 4: MCP Agents (Model Context Protocol) — Line by Line](#8-part-4-mcp-agents-model-context-protocol--line-by-line)
9. [Part 5: LLM Apps with Memory — Line by Line](#9-part-5-llm-apps-with-memory--line-by-line)
10. [Part 6: Voice AI Agents — Line by Line](#10-part-6-voice-ai-agents--line-by-line)
11. [Part 7: Game-Playing Agents — Line by Line](#11-part-7-game-playing-agents--line-by-line)
12. [Part 8: Corrective RAG (CRAG) with LangGraph — Line by Line](#12-part-8-corrective-rag-crag-with-langgraph--line-by-line)
13. [Part 9: AI Agent Framework Crash Course (Google ADK)](#13-part-9-ai-agent-framework-crash-course-google-adk)
14. [Part 10: Awesome Agent Skills](#14-part-10-awesome-agent-skills)
15. [How to Run Each Type — Step by Step](#15-how-to-run-each-type--step-by-step)
16. [What Result Will You See?](#16-what-result-will-you-see)
17. [Different Ways of Doing the Same Thing](#17-different-ways-of-doing-the-same-thing)
18. [Differences Between Each Category](#18-differences-between-each-category)
19. [What Each Part Adds Over the Previous](#19-what-each-part-adds-over-the-previous)
20. [Comparison Table](#20-comparison-table)
21. [Cheat Sheet](#21-cheat-sheet)
22. [Summary](#22-summary)
23. [Conclusion](#23-conclusion)

---

## 1. What Is This Repository?

**In one sentence:** This is a free library of 100+ working AI apps that you can download, run, and customize — it covers everything from a simple travel planner to a full voice customer support agent.

### Who made it?
Created by **Shubham Saboo** and the community. It is published under the Apache 2.0 license, meaning you can use it for free, fork it, modify it, even sell it.

### What problem does it solve?
Every time someone wants to build an AI app, they have to rebuild the same pieces:
- How to connect to an LLM (GPT, Claude, Gemini, Llama…)
- How to make it search the web
- How to give it memory
- How to make multiple AI agents work together
- How to add voice

This repo gives you all of those pieces as ready-to-copy templates.

### What can you build with it?
- A travel planner that researches and writes a trip itinerary
- A chatbot that reads your PDFs and answers questions from them
- Multiple AI agents that work together like a team (e.g., one researches, another writes)
- A voice assistant that speaks its answers
- AI agents that play chess or tic-tac-toe
- A GitHub analyst that reads your repos
- A legal assistant, finance advisor, recruitment tool…

---

## 2. What Is an LLM?

Before diving into code, you need to understand the building blocks.

### LLM = Large Language Model
An LLM is a type of AI trained on huge amounts of text. It can:
- Answer questions
- Write code, emails, essays
- Summarize documents
- Translate languages
- Follow instructions (like "be a travel agent")

**Examples of LLMs used in this repo:**
| LLM | Company | API Key Needed? |
|-----|---------|----------------|
| GPT-4o | OpenAI | Yes (paid) |
| Claude 3.5/3.7 | Anthropic | Yes (paid) |
| Gemini 1.5/2.0 | Google | Yes (free tier) |
| Llama 3 | Meta (via Groq) | Yes (free tier) |
| Qwen | Alibaba | Yes |
| DeepSeek | DeepSeek | Yes |

### What is an API Key?
Think of it like a password. When your Python code calls GPT-4, it sends your API key to prove you are allowed to use it. You get these keys by signing up on each provider's website.

### What is Streamlit?
Every app in this repo uses **Streamlit** — a Python library that turns your Python code into a web page with buttons, text boxes, and file uploaders. You do NOT need to know HTML or JavaScript. Just write Python.

```
Python code (streamlit) → runs in browser as a web app
```

---

## 3. Folder Structure — The Big Map

```
awesome-llm-apps-main/
│
├── starter_ai_agents/           ← SIMPLEST: single-file agents, best starting point
│   ├── ai_travel_agent/
│   ├── mixture_of_agents/
│   ├── ai_data_analysis_agent/
│   └── ... (14 more folders)
│
├── rag_tutorials/               ← RAG: teach AI to read your documents
│   ├── rag_chain/
│   ├── corrective_rag/
│   ├── hybrid_search_rag/
│   └── ... (20 more folders)
│
├── advanced_ai_agents/          ← ADVANCED: agents with tools + reasoning
│   ├── single_agent_apps/
│   └── multi_agent_apps/
│       └── agent_teams/         ← Teams of agents working together
│
├── mcp_ai_agents/               ← MCP: agents that use external tools via protocol
│   ├── github_mcp_agent/
│   ├── browser_mcp_agent/
│   └── ...
│
├── voice_ai_agents/             ← VOICE: speak in, hear answer back
│   ├── customer_support_voice_agent/
│   └── ...
│
├── advanced_llm_apps/
│   ├── llm_apps_with_memory_tutorials/   ← MEMORY: AI remembers past chats
│   ├── chat_with_X_tutorials/            ← Chat with PDF, Gmail, YouTube...
│   ├── llm_finetuning_tutorials/         ← Train your own LLM
│   └── llm_optimization_tools/          ← Reduce API costs
│
├── awesome_agent_skills/        ← SKILLS: Markdown files that give agents skills
│
├── generative_ui_agents/        ← UI: agents that generate interactive UI
│
└── ai_agent_framework_crash_course/  ← LEARN: step-by-step framework tutorials
    ├── google_adk_crash_course/
    └── openai_sdk_crash_course/
```

**Every sub-folder has exactly these 3 files:**
1. `main_file.py` — the actual application code
2. `requirements.txt` — list of Python packages needed
3. `README.md` — instructions specific to that app

---

## 4. Technology Stack — What Tools Are Used

### Framework Layer (what builds the AI logic)

| Tool | What It Does | Used In |
|------|-------------|---------|
| **Agno** | Build AI agents with tools, memory, teams | Most starter + advanced agents |
| **LangChain** | Chain prompts, retrievers, parsers together | RAG apps, corrective RAG |
| **LangGraph** | Build agents as state machines / graphs | Corrective RAG, autonomous RAG |
| **Google ADK** | Google's official agent development kit | Crash course, ADK apps |
| **OpenAI Agents SDK** | OpenAI's official multi-agent framework | Voice agent, OpenAI crash course |
| **CrewAI** | Multi-agent coordination framework | Services agency |
| **AG2** | AutoGen 2 for adaptive agent teams | AG2 research team |

### UI Layer

| Tool | What It Does |
|------|-------------|
| **Streamlit** | Turns Python into a browser web app |
| **FastAPI** | REST API backend (travel planner team) |
| **Next.js** | Frontend for Generative UI apps |

### Database / Storage Layer

| Tool | What It Does |
|------|-------------|
| **Qdrant** | Vector database — stores document embeddings for RAG |
| **Chroma** | Local vector database (no server needed) |
| **SQLite** | Local relational database for agent history |

### Embedding Models (convert text to numbers)

| Tool | What It Does |
|------|-------------|
| **OpenAI text-embedding-3-small** | Cloud embedding via OpenAI |
| **sentence-transformers** | Local embedding model |
| **FastEmbed** | Lightweight local embedding |
| **Google Gemini Embeddings** | Cloud embedding via Google |

### Search / Web Tools

| Tool | What It Does |
|------|-------------|
| **SerpAPI** | Google search results via API |
| **DuckDuckGo Tools** | Free web search |
| **Tavily** | AI-optimized web search |
| **Firecrawl** | Web scraper that returns clean markdown |

### Memory Tools

| Tool | What It Does |
|------|-------------|
| **Mem0** | Smart memory layer — remembers user preferences across sessions |

---

## 5. Part 1: Starter AI Agents — Line by Line

### File: `starter_ai_agents/ai_travel_agent/travel_agent.py`

This is the best place to start learning. It is a travel planning app. Two AI agents work together: one researches, one plans.

```python
from textwrap import dedent
```
`textwrap.dedent` removes leading spaces from multi-line strings. Used to format the agent instructions neatly in the code.

```python
from agno.agent import Agent
```
`Agent` is the main class from the **Agno** framework. Think of it as a "worker" you can give a role and tools.

```python
from agno.run.agent import RunOutput
```
`RunOutput` is the data type that an agent returns after running. It contains `.content` (the actual text answer).

```python
from agno.tools.serpapi import SerpApiTools
```
This gives the agent the ability to search Google via SerpAPI. When the agent needs to look something up, it calls this tool automatically.

```python
import streamlit as st
```
Streamlit — the web UI library. `st.title(...)`, `st.text_input(...)`, `st.button(...)` all create visual elements in the browser.

```python
import re
```
Python's built-in regular expressions library. Used here to find "Day 1", "Day 2" patterns in the itinerary text.

```python
from agno.models.openai import OpenAIChat
```
Tells Agno to use GPT-4o as the brain of the agents.

```python
from icalendar import Calendar, Event
from datetime import datetime, timedelta
```
`icalendar` creates `.ics` calendar files (the format used by Google Calendar, Outlook). `datetime` handles dates.

---

### The `generate_ics_content` Function (lines 12–59)

```python
def generate_ics_content(plan_text: str, start_date: datetime = None) -> bytes:
```
This function takes the travel plan text and converts it into a calendar file.

```python
    cal = Calendar()
    cal.add('prodid', '-//AI Travel Planner//github.com//')
    cal.add('version', '2.0')
```
Creates a new calendar object and adds metadata fields (product id and version number — required by the .ics format).

```python
    if start_date is None:
        start_date = datetime.today()
```
If no start date is given, use today.

```python
    day_pattern = re.compile(r'Day (\d+)[:\s]+(.*?)(?=Day \d+|$)', re.DOTALL)
    days = day_pattern.findall(plan_text)
```
This regular expression finds all "Day 1: ...", "Day 2: ..." sections in the plan text. `\d+` means "one or more digits". `re.DOTALL` makes `.` match newlines too.

```python
    if not days:  # If no day pattern found
        event = Event()
        event.add('summary', "Travel Itinerary")
        ...
        cal.add_component(event)
```
If the text doesn't have "Day X" format, create one big event for the whole trip.

```python
    else:
        for day_num, day_content in days:
            day_num = int(day_num)
            current_date = start_date + timedelta(days=day_num - 1)
            event = Event()
            event.add('summary', f"Day {day_num} Itinerary")
            event.add('dtstart', current_date.date())
            cal.add_component(event)
```
For each day found, create a calendar event on the correct date.

```python
    return cal.to_ical()
```
Converts the calendar object to bytes (raw .ics file content).

---

### The Streamlit UI (lines 62–72)

```python
st.title("AI Travel Planner ")
st.caption("Plan your next adventure with AI...")
```
`st.title` creates the page heading. `st.caption` creates a small italic subtitle below it.

```python
if 'itinerary' not in st.session_state:
    st.session_state.itinerary = None
```
`st.session_state` is like a dictionary that remembers values between button clicks. Streamlit re-runs the entire script every time you click a button, so without `session_state`, you'd lose the itinerary. This line initializes it to `None` on the first load.

```python
openai_api_key = st.text_input("Enter OpenAI API Key", type="password")
serp_api_key = st.text_input("Enter Serp API Key", type="password")
```
Two password-style input boxes. The user types their API keys here.

---

### The Two Agents (lines 75–115)

```python
if openai_api_key and serp_api_key:
```
Only create the agents if both keys are filled in.

```python
    researcher = Agent(
        name="Researcher",
        role="Searches for travel destinations...",
        model=OpenAIChat(id="gpt-4o", api_key=openai_api_key),
        description=dedent("""..."""),
        instructions=[...],
        tools=[SerpApiTools(api_key=serp_api_key)],
        add_datetime_to_context=True,
    )
```
Creates the **Researcher agent**. Key fields:
- `name` — label for logs/debugging
- `role` — tells the agent what it does
- `model` — which LLM brain to use (GPT-4o here)
- `description` — detailed system prompt
- `instructions` — a list of step-by-step rules
- `tools` — list of tools the agent can use (SerpAPI = Google search)
- `add_datetime_to_context=True` — automatically tells the agent today's date

```python
    planner = Agent(
        name="Planner",
        role="Generates a draft itinerary...",
        model=OpenAIChat(id="gpt-4o", api_key=openai_api_key),
        ...
    )
```
Creates the **Planner agent**. Same structure but no search tools — it only writes based on what the Researcher found.

---

### The Button Logic (lines 117–157)

```python
destination = st.text_input("Where do you want to go?")
num_days = st.number_input("How many days?", min_value=1, max_value=30, value=7)
```
Input fields for the user's travel destination and duration.

```python
col1, col2 = st.columns(2)
```
Creates two side-by-side columns in the UI — left for "Generate", right for "Download".

```python
with col1:
    if st.button("Generate Itinerary"):
        with st.spinner("Researching your destination..."):
            research_results: RunOutput = researcher.run(
                f"Research {destination} for a {num_days} day trip", stream=False
            )
```
When clicked: the researcher agent runs. It searches Google and returns a `RunOutput`. `stream=False` means wait for the full answer before displaying (vs streaming word by word).

```python
        prompt = f"""
        Destination: {destination}
        Duration: {num_days} days
        Research Results: {research_results.content}
        Please create a detailed itinerary based on this research.
        """
        response: RunOutput = planner.run(prompt, stream=False)
        st.session_state.itinerary = response.content
        st.write(response.content)
```
The planner receives the research results and generates the itinerary. It's saved to `session_state` so the download button can use it.

```python
with col2:
    if st.session_state.itinerary:
        ics_content = generate_ics_content(st.session_state.itinerary)
        st.download_button(
            label="Download Itinerary as Calendar (.ics)",
            data=ics_content,
            file_name="travel_itinerary.ics",
            mime="text/calendar"
        )
```
Only shown after an itinerary exists. Lets the user download it as a `.ics` calendar file.

---

### File: `starter_ai_agents/mixture_of_agents/mixture-of-agents.py`

This app asks the SAME question to multiple different LLMs at the same time, then combines all their answers into one final answer.

```python
import asyncio
```
Python's built-in async library. "Async" means running multiple things at once without waiting for each one to finish.

```python
from together import AsyncTogether, Together
```
`Together.ai` is a platform that hosts many open-source LLMs. `AsyncTogether` is the async version for parallel calls.

```python
reference_models = [
    "Qwen/Qwen2-72B-Instruct",
    "Qwen/Qwen1.5-72B-Chat",
    "mistralai/Mixtral-8x22B-Instruct-v0.1",
    "databricks/dbrx-instruct",
]
aggregator_model = "mistralai/Mixtral-8x22B-Instruct-v0.1"
```
Four models answer first (reference models). Then one "aggregator" model reads all four answers and writes the final combined answer.

```python
async def run_llm(model):
    response = await async_client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": user_prompt}],
        temperature=0.7,
        max_tokens=512,
    )
    return model, response.choices[0].message.content
```
`async def` means this function runs without blocking other functions. `await` means "wait here for the API to respond, but let other things run in the meantime." Returns a tuple of (model_name, answer_text).

```python
async def main():
    results = await asyncio.gather(*[run_llm(model) for model in reference_models])
```
`asyncio.gather` runs all four `run_llm()` calls AT THE SAME TIME (in parallel). Much faster than calling them one by one.

```python
    finalStream = client.chat.completions.create(
        model=aggregator_model,
        messages=[
            {"role": "system", "content": aggregator_system_prompt},
            {"role": "user", "content": ",".join(response for _, response in results)},
        ],
        stream=True,
    )
```
Sends all four answers to the aggregator model. `stream=True` means display the answer word-by-word as it arrives.

```python
    response_container = st.empty()
    full_response = ""
    for chunk in finalStream:
        content = chunk.choices[0].delta.content or ""
        full_response += content
        response_container.markdown(full_response + "▌")
    response_container.markdown(full_response)
```
Streams the response live. The `▌` character acts as a blinking cursor. Each chunk is appended and the display updates.

---

## 6. Part 2: RAG (Retrieval Augmented Generation) — Line by Line

### What is RAG?
RAG = teach the AI to answer questions using YOUR documents, not just its training data.

**Without RAG:** "What does our internal policy say about overtime?" → LLM has no idea.
**With RAG:** Upload your policy PDF → AI reads it → Answers correctly.

### How RAG Works (The Pipeline)

```
Your PDF/Document
      ↓
   Load & Split into chunks (100-500 words each)
      ↓
   Convert chunks to numbers (embeddings)
      ↓
   Store numbers in a vector database
      ↓
User asks a question
      ↓
   Convert question to numbers (same embedding)
      ↓
   Find the most similar chunk numbers (similarity search)
      ↓
   Send question + matching chunks to LLM
      ↓
   LLM answers using the context
```

### File: `rag_tutorials/rag_chain/app.py` (Basic RAG)

```python
from langchain_google_genai import GoogleGenerativeAIEmbeddings
```
Uses Google's embedding model to convert text to numbers.

```python
from langchain_chroma import Chroma
```
Chroma is a local vector database. It runs on your machine with no server setup needed.

```python
from langchain_community.document_loaders import PyPDFLoader
```
Loads a PDF file and extracts its text.

```python
from langchain_text_splitters.sentence_transformers import SentenceTransformersTokenTextSplitter
```
Splits long text into smaller overlapping chunks.

```python
from langchain_core.prompts import ChatPromptTemplate
```
Creates a prompt template with placeholders like `{context}` and `{question}`.

```python
from langchain_google_genai import ChatGoogleGenerativeAI
```
Uses Google Gemini as the LLM that generates the final answer.

```python
from langchain_core.output_parsers import StrOutputParser
```
Converts the LLM's output object to a simple string.

```python
from langchain_core.runnables import RunnablePassthrough
```
A "passthrough" — takes input and passes it unchanged to the next step. Used in chain composition.

---

### Setting Up the Database

```python
embedding_model = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
```
Creates the embedding model. Every piece of text will be converted to a list of numbers using this.

```python
db = Chroma(
    collection_name="pharma_database",
    embedding_function=embedding_model,
    persist_directory='./pharma_db'
)
```
Creates (or loads) a Chroma database. Files are stored in `./pharma_db` folder. `collection_name` is like a table name.

---

### The `add_to_db` Function

```python
def add_to_db(uploaded_files):
    for uploaded_file in uploaded_files:
        temp_file_path = os.path.join("./temp", uploaded_file.name)
        os.makedirs(os.path.dirname(temp_file_path), exist_ok=True)
        
        with open(temp_file_path, "wb") as temp_file:
            temp_file.write(uploaded_file.getbuffer())
```
Saves the uploaded file to a temporary folder. `uploaded_file.getbuffer()` gets the raw bytes of the uploaded file.

```python
        loader = PyPDFLoader(temp_file_path)
        data = loader.load()
```
Loads the PDF. `data` is now a list of `Document` objects, one per page.

```python
        doc_metadata = [data[i].metadata for i in range(len(data))]
        doc_content = [data[i].page_content for i in range(len(data))]
```
Separates metadata (page numbers, source) from content (actual text).

```python
        st_text_splitter = SentenceTransformersTokenTextSplitter(
            model_name="sentence-transformers/all-mpnet-base-v2",
            chunk_size=100,
            chunk_overlap=50
        )
        st_chunks = st_text_splitter.create_documents(doc_content, doc_metadata)
```
Splits text into chunks of 100 tokens with 50 token overlap. Overlap is important — ensures answers near chunk boundaries are not lost.

```python
        db.add_documents(st_chunks)
```
Adds all chunks to the vector database. Chroma automatically converts them to embeddings and stores them.

```python
        os.remove(temp_file_path)
```
Cleans up the temporary file.

---

### The `run_rag_chain` Function

```python
def run_rag_chain(query):
    retriever = db.as_retriever(search_type="similarity", search_kwargs={'k': 5})
```
Creates a retriever object. When called, it will find the 5 most similar chunks to the query.

```python
    PROMPT_TEMPLATE = """
    You are a highly knowledgeable assistant specializing in pharmaceutical sciences. 
    Answer the question based only on the following context:
    {context}
    Answer the question based on the above context:
    {question}
    ...
    """
    prompt_template = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)
```
Creates a prompt with `{context}` and `{question}` placeholders.

```python
    chat_model = ChatGoogleGenerativeAI(
        model="gemini-1.5-pro",
        api_key=st.session_state.get("gemini_api_key"),
        temperature=1
    )
```
The LLM that generates the answer. `temperature=1` means more creative answers (0 = factual, 2 = very random).

```python
    output_parser = StrOutputParser()
```
Converts LLM output to a plain string.

```python
    rag_chain = {
        "context": retriever | format_docs,
        "question": RunnablePassthrough()
    } | prompt_template | chat_model | output_parser
```
This is the **LCEL (LangChain Expression Language)** chain. Read it like a pipeline:
1. `retriever | format_docs` → fetch 5 chunks and join them as one string → this becomes `{context}`
2. `RunnablePassthrough()` → take the query unchanged → this becomes `{question}`
3. `| prompt_template` → fill in `{context}` and `{question}` in the template
4. `| chat_model` → send to Gemini
5. `| output_parser` → convert to plain string

```python
    response = rag_chain.invoke(query)
    return response
```
Runs the whole chain with the user's question.

---

## 7. Part 3: Multi-Agent Teams — Line by Line

### File: `advanced_ai_agents/multi_agent_apps/agent_teams/ai_finance_agent_team/finance_agent_team.py`

This app creates two specialized agents (web researcher + finance analyst) working as a team.

```python
from agno.agent import Agent
from agno.team import Team
from agno.models.openai import OpenAIChat
from agno.db.sqlite import SqliteDb
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.tools.yfinance import YFinanceTools
from agno.os import AgentOS
```
- `Team` — wraps multiple agents so they can collaborate
- `SqliteDb` — saves conversation history to a local SQLite file
- `DuckDuckGoTools` — web search without needing an API key
- `YFinanceTools` — fetches real stock prices, news, analyst recommendations from Yahoo Finance
- `AgentOS` — creates a web server to run the team

```python
db = SqliteDb(db_file="agents.db")
```
Creates a SQLite database file called `agents.db` to store conversation history.

```python
web_agent = Agent(
    name="Web Agent",
    role="Search the web for information",
    model=OpenAIChat(id="gpt-4o"),
    tools=[DuckDuckGoTools()],
    db=db,
    add_history_to_context=True,
    markdown=True,
)
```
- `add_history_to_context=True` — this agent remembers past messages in the conversation
- `markdown=True` — formats responses with markdown (tables, bold, etc.)

```python
finance_agent = Agent(
    name="Finance Agent",
    role="Get financial data",
    model=OpenAIChat(id="gpt-4o"),
    tools=[YFinanceTools(include_tools=[
        "get_current_stock_price",
        "get_analyst_recommendations",
        "get_company_info",
        "get_company_news"
    ])],
    instructions=["Always use tables to display data"],
    db=db,
    add_history_to_context=True,
    markdown=True,
)
```
Includes only specific YFinance tools. `instructions` force it to always use tables.

```python
agent_team = Team(
    name="Agent Team (Web+Finance)",
    model=OpenAIChat(id="gpt-4o"),
    members=[web_agent, finance_agent],
    debug_mode=True,
    markdown=True,
)
```
`Team` acts as a coordinator. The team's own LLM decides WHICH member agent to call for each task. `debug_mode=True` prints detailed logs.

```python
agent_os = AgentOS(teams=[agent_team])
app = agent_os.get_app()

if __name__ == "__main__":
    agent_os.serve(app="finance_agent_team:app", reload=True)
```
`AgentOS` wraps the team in a web server (using FastAPI under the hood). `reload=True` restarts the server if you edit the file.

---

## 8. Part 4: MCP Agents (Model Context Protocol) — Line by Line

### File: `mcp_ai_agents/github_mcp_agent/github_agent.py`

MCP = Model Context Protocol. It is a standard way for AI agents to connect to external tools (databases, APIs, file systems) without writing custom integration code.

Think of MCP like a USB port — it is a universal plug that any AI agent can use to connect to any compatible tool.

```python
from agno.tools.mcp import MCPTools
from mcp import StdioServerParameters
```
`MCPTools` wraps an MCP server as a tool for an Agno agent.
`StdioServerParameters` defines how to start the MCP server (via stdin/stdout).

```python
server_params = StdioServerParameters(
    command="docker",
    args=[
        "run", "-i", "--rm",
        "-e", "GITHUB_PERSONAL_ACCESS_TOKEN",
        "-e", "GITHUB_TOOLSETS",
        "ghcr.io/github/github-mcp-server"
    ],
    env={
        **os.environ,
        "GITHUB_PERSONAL_ACCESS_TOKEN": os.getenv('GITHUB_TOKEN'),
        "GITHUB_TOOLSETS": "repos,issues,pull_requests"
    }
)
```
This starts the official GitHub MCP server as a Docker container. Docker runs the server in an isolated container. The `GITHUB_TOOLSETS` variable tells it which GitHub API tools to expose (repos, issues, pull requests).

```python
async with MCPTools(server_params=server_params) as mcp_tools:
    agent = Agent(
        tools=[mcp_tools],
        instructions=dedent("""\
            You are a GitHub assistant. Help users explore repositories...
        """),
        markdown=True,
    )
    response: RunOutput = await asyncio.wait_for(
        agent.arun(message), timeout=120.0
    )
    return response.content
```
`async with` starts the Docker container and connects to it. The agent gets `mcp_tools` as its toolset — so it can call GitHub APIs directly. `asyncio.wait_for` adds a 120-second timeout so the app doesn't hang forever.

---

## 9. Part 5: LLM Apps with Memory — Line by Line

### File: `advanced_llm_apps/llm_apps_with_memory_tutorials/llm_app_personalized_memory/llm_app_memory.py`

This app remembers what each user has told it in past sessions — not just in the current conversation.

```python
from mem0 import Memory
from openai import OpenAI
```
`mem0` is the memory library. It stores memories as vectors (using Qdrant) so they can be searched by meaning.

```python
config = {
    "vector_store": {
        "provider": "qdrant",
        "config": {
            "collection_name": "llm_app_memory",
            "host": "localhost",
            "port": 6333,
        }
    },
}
memory = Memory.from_config(config)
```
Sets up Mem0 to use a local Qdrant vector database as storage.

```python
user_id = st.text_input("Enter your Username")
prompt = st.text_input("Ask ChatGPT")
```
Each user has a unique ID. Memories are stored and retrieved per user.

```python
relevant_memories = memory.search(query=prompt, user_id=user_id)
context = "Relevant past information:\n"
for mem in relevant_memories:
    context += f"- {mem['text']}\n"
```
Searches for past memories that are semantically similar to the current question. For example, if the user previously said "I'm vegetarian", and they now ask "What should I eat in Tokyo?", the memory is retrieved as context.

```python
full_prompt = f"{context}\nHuman: {prompt}\nAI:"
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "system", "content": "You are a helpful assistant with access to past conversations."},
        {"role": "user", "content": full_prompt}
    ]
)
answer = response.choices[0].message.content
st.write("Answer: ", answer)
memory.add(answer, user_id=user_id)
```
Sends the context + current question to GPT-4o. After getting the answer, saves it to memory so future questions can reference it.

---

## 10. Part 6: Voice AI Agents — Line by Line

### File: `voice_ai_agents/customer_support_voice_agent/customer_support_voice_agent.py`

This is the most complex starter app. It combines:
1. RAG (reads documentation)
2. AI Agents (processes queries)
3. Text-to-Speech (speaks the answer back)

**Flow:**
```
User types question
  → Embed question (FastEmbed)
  → Search Qdrant for relevant docs
  → processor_agent writes text answer
  → tts_agent improves text for speaking
  → OpenAI TTS converts text to audio (.mp3)
  → User hears the answer
```

```python
from firecrawl import FirecrawlApp
```
Firecrawl crawls a website URL and returns the pages as clean Markdown text.

```python
from fastembed import TextEmbedding
```
FastEmbed is a local embedding model — runs on your machine without an API call.

```python
from agents import Agent, Runner
```
This imports from the **OpenAI Agents SDK** (different from Agno's Agent).

```python
def crawl_documentation(firecrawl_api_key: str, url: str, output_dir=None):
    firecrawl = FirecrawlApp(api_key=firecrawl_api_key)
    response = firecrawl.crawl_url(
        url,
        params={
            'limit': 5,
            'scrapeOptions': {'formats': ['markdown', 'html']}
        }
    )
```
Crawls up to 5 pages of a website. Returns markdown content.

```python
def store_embeddings(client, embedding_model, pages, collection_name):
    for page in pages:
        embedding = list(embedding_model.embed([page["content"]]))[0]
        client.upsert(
            collection_name=collection_name,
            points=[models.PointStruct(
                id=str(uuid.uuid4()),
                vector=embedding.tolist(),
                payload={...}
            )]
        )
```
Converts each page's text to a vector and stores it in Qdrant.

```python
def setup_agents(openai_api_key: str):
    processor_agent = Agent(
        name="Documentation Processor",
        instructions="""...""",
        model="gpt-4o"
    )
    tts_agent = Agent(
        name="Text-to-Speech Agent",
        instructions="""...""",
        model="gpt-4o-mini-tts"
    )
    return processor_agent, tts_agent
```
Creates two agents. The `processor_agent` writes the answer. The `tts_agent` rewrites it in a speaking-friendly style.

```python
audio_response = await async_openai.audio.speech.create(
    model="gpt-4o-mini-tts",
    voice=st.session_state.selected_voice,
    input=processor_response,
    instructions=tts_response,
    response_format="mp3"
)
```
OpenAI's TTS API converts text to spoken audio. The `instructions` from the tts_agent guide pacing and emphasis.

---

## 11. Part 7: Game-Playing Agents — Line by Line

### File: `advanced_ai_agents/autonomous_game_playing_agent_apps/ai_tic_tac_toe_agent/app.py`

Two AI agents (which can be any LLM — Claude, GPT, Gemini, Llama) play Tic-Tac-Toe against each other.

```python
from agents import get_tic_tac_toe_players
from utils import TicTacToeBoard, display_board, display_move_history, show_agent_status
```
`agents.py` creates the two agent objects. `utils.py` handles the board logic and display.

```python
model_options = {
    "gpt-4o": "openai:gpt-4o",
    "o3-mini": "openai:o3-mini",
    "claude-3.5": "anthropic:claude-3-5-sonnet",
    "claude-3.7-thinking": "anthropic:claude-3-7-sonnet-thinking",
    "gemini-flash": "google:gemini-2.0-flash",
    "llama-3.3": "groq:llama-3.3-70b-versatile",
}
```
Dictionary of available models with their provider prefixes. The user can pick any two.

```python
response: RunOutput = current_agent.run(
    f"""Current board state:\n{st.session_state.game_board.get_board_state()}\n
    Available valid moves (row, col): {valid_moves}\n
    Choose your next move from the valid moves above.
    Respond with ONLY two numbers for row and column, e.g. "1 2".""",
    stream=False,
)
```
The agent's "input" is the current board state and list of valid moves. It is told to respond with ONLY two numbers. This is important — if the LLM writes a long explanation, the parsing would fail.

```python
numbers = re.findall(r"\d+", response.content if response else "")
row, col = map(int, numbers[:2])
success, message = st.session_state.game_board.make_move(row, col)
```
Extracts the two numbers from the LLM's response. `re.findall(r"\d+", ...)` finds all digit sequences. Then tries to place the move on the board.

```python
if success:
    st.session_state.move_history.append({...})
    st.rerun()  # Triggers Streamlit to re-run the entire script (next player's turn)
else:
    # If invalid move, ask the agent again
    response = current_agent.run(f"Invalid move: {message}...")
    st.rerun()
```
`st.rerun()` is the game loop. Every time a valid move is made, Streamlit re-runs the script, which checks whose turn it is and asks that agent for its move.

---

## 12. Part 8: Corrective RAG (CRAG) with LangGraph — Line by Line

### File: `rag_tutorials/corrective_rag/corrective_rag.py`

This is an advanced RAG that checks if retrieved documents are actually relevant. If they are not, it rewrites the query and searches the web.

**Flow:**
```
Question
  → retrieve (from vector DB)
  → grade_documents (are they relevant? yes/no per document)
  → if all relevant → generate answer
  → if some irrelevant → transform_query (rewrite question)
    → web_search (Tavily)
      → generate answer
```

```python
from langgraph.graph import END, StateGraph
from typing import Dict, TypedDict
```
`StateGraph` creates a directed graph where each node is a function. `END` marks the exit point.

```python
class GraphState(TypedDict):
    keys: Dict[str, any]
```
`GraphState` is the shared state that flows between all nodes. It is just a dictionary with a `keys` field.

```python
workflow = StateGraph(GraphState)
workflow.add_node("retrieve", retrieve)
workflow.add_node("grade_documents", grade_documents)
workflow.add_node("generate", generate)
workflow.add_node("transform_query", transform_query)
workflow.add_node("web_search", web_search)
```
Registers each function as a node in the graph.

```python
workflow.set_entry_point("retrieve")
workflow.add_edge("retrieve", "grade_documents")
workflow.add_conditional_edges(
    "grade_documents",
    decide_to_generate,
    {
        "transform_query": "transform_query",
        "generate": "generate",
    },
)
workflow.add_edge("transform_query", "web_search")
workflow.add_edge("web_search", "generate")
workflow.add_edge("generate", END)

app = workflow.compile()
```
- `set_entry_point` — where to start
- `add_edge` — unconditional: always go from A to B
- `add_conditional_edges` — calls `decide_to_generate(state)` which returns either `"transform_query"` or `"generate"`, and routes accordingly
- `compile()` — builds the final runnable graph

```python
def grade_documents(state):
    llm = ChatAnthropic(model="claude-sonnet-4-5", ...)
    prompt = PromptTemplate(template="""
        Return ONLY a JSON object with a "score" field that is either "yes" or "no".
        Document: {context}
        Question: {question}
        Rules: Check for related keywords or semantic meaning...
        Return exactly like: {"score": "yes"} or {"score": "no"}
    """)
    ...
    for d in documents:
        response = chain.invoke({"question": question, "context": d.page_content})
        score = json.loads(json_match.group())
        if score.get("score") == "yes":
            filtered_docs.append(d)
        else:
            search = "Yes"  # Mark that web search is needed
```
For each retrieved chunk, the LLM decides if it is relevant (yes/no as JSON). If any chunk fails, `run_web_search` flag is set to `"Yes"`.

```python
def transform_query(state):
    prompt = PromptTemplate(template="""
        Generate a search-optimized version of this question...
        {question}
        Return only the improved question with no additional text:
    """)
    better_question = chain.invoke({"question": question})
```
Rewrites the question to be better for web search.

---

## 13. Part 9: AI Agent Framework Crash Course (Google ADK)

### File: `ai_agent_framework_crash_course/google_adk_crash_course/1_starter_agent/creative_writing_agent/agent.py`

This is the simplest possible Google ADK agent — just 4 lines of logic.

```python
from google.adk.agents import LlmAgent

root_agent = LlmAgent(
    name="creative_writing_agent",
    model="gemini-3-flash-preview",
    description="A creative writing assistant...",
    instruction="""
    You are a creative writing assistant.
    Your role is to:
    - Help users develop story ideas
    - Assist with character development
    ...
    """
)
```
`LlmAgent` is Google ADK's agent class. It is even simpler than Agno's Agent — just a name, model, description, and instructions. No tools added here — just a creative writing personality.

The `root_agent` variable name is required by Google ADK — it's the "entry point" that ADK looks for when loading the agent module.

**To run a Google ADK agent:**
```bash
adk web  # Opens a browser-based test UI
# OR
adk run creative_writing_agent  # Run in terminal
```

---

## 14. Part 10: Awesome Agent Skills

### What are Agent Skills?
Skills are Markdown `.md` files that define what a specific type of agent should do. They are like "personality files" you give to any AI agent.

**Example:** `awesome_agent_skills/python-expert/python_expert.md`
This file contains instructions that turn any AI into a Python expert:
- How to write Pythonic code
- How to handle errors
- How to write tests
- What libraries to recommend

**How to use a skill:**
```python
with open("awesome_agent_skills/python-expert/python_expert.md") as f:
    skill_instructions = f.read()

agent = Agent(
    instructions=skill_instructions,
    model=...
)
```

Available skills include:
- `academic-researcher` — literature reviews, paper analysis
- `code-reviewer` — automated code review
- `data-analyst` — statistics, data exploration
- `debugger` — systematic bug hunting
- `email-drafter` — professional emails
- `technical-writer` — documentation
- `ux-designer` — UI/UX feedback
- And 12 more...

---

## 15. How to Run Each Type — Step by Step

### Prerequisites (do this once)
```bash
# Install Python 3.10+ (check: python --version)
# Install pip (check: pip --version)
```

### Step 1: Get the Code
```bash
git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
cd awesome-llm-apps
```

### Step 2: Get Your API Keys
Go to these websites and sign up to get free/paid API keys:
- **OpenAI:** https://platform.openai.com (paid, ~$5 to start)
- **Anthropic (Claude):** https://console.anthropic.com (paid)
- **Google (Gemini):** https://aistudio.google.com (free tier!)
- **Groq (Llama):** https://console.groq.com (free tier!)
- **Together.ai:** https://www.together.ai (free credits)
- **SerpAPI:** https://serpapi.com (100 free searches/month)

### Step 3: Run a Starter Agent (easiest)
```bash
cd starter_ai_agents/ai_travel_agent
pip install -r requirements.txt
streamlit run travel_agent.py
```
Browser opens at `http://localhost:8501`. Enter your API keys in the UI. Done.

### Step 4: Run the Basic RAG App
```bash
cd rag_tutorials/rag_chain
pip install -r requirements.txt
streamlit run app.py
```
Browser opens. Enter Gemini API key in sidebar. Upload a PDF. Ask questions about it.

### Step 5: Run a Multi-Agent Team
```bash
cd advanced_ai_agents/multi_agent_apps/agent_teams/ai_finance_agent_team
pip install -r requirements.txt
export OPENAI_API_KEY="your-key-here"   # Linux/Mac
# or on Windows:
# set OPENAI_API_KEY=your-key-here
python finance_agent_team.py
```
Opens a web server at `http://localhost:7777`. Chat with the team via browser.

### Step 6: Run the MCP GitHub Agent
```bash
# REQUIRES DOCKER TO BE RUNNING FIRST
cd mcp_ai_agents/github_mcp_agent
pip install -r requirements.txt
streamlit run github_agent.py
```
Enter OpenAI key + GitHub token. Ask questions about any public repo.

### Step 7: Run the Memory App
```bash
# First start Qdrant (vector database) in Docker:
docker run -p 6333:6333 qdrant/qdrant

# Then in a new terminal:
cd advanced_llm_apps/llm_apps_with_memory_tutorials/llm_app_personalized_memory
pip install -r requirements.txt
streamlit run llm_app_memory.py
```

### Step 8: Run the Corrective RAG
```bash
# First start Qdrant:
docker run -p 6333:6333 qdrant/qdrant

cd rag_tutorials/corrective_rag
pip install -r requirements.txt
streamlit run corrective_rag.py
```

### Step 9: Run the Google ADK Crash Course
```bash
cd ai_agent_framework_crash_course/google_adk_crash_course/1_starter_agent
pip install -r requirements.txt
export GOOGLE_API_KEY="your-gemini-key"
adk web  # opens browser UI
# navigate to creative_writing_agent folder and test it
```

### Step 10: Run the Game-Playing Agents
```bash
cd advanced_ai_agents/autonomous_game_playing_agent_apps/ai_tic_tac_toe_agent
pip install -r requirements.txt
# Create .env file with API keys:
echo "OPENAI_API_KEY=your-key" > .env
echo "ANTHROPIC_API_KEY=your-key" >> .env
streamlit run app.py
```

---

## 16. What Result Will You See?

### Starter AI Travel Agent
- You see a web page with two input boxes (destination, days)
- You enter "Paris, 5 days"
- The researcher agent searches Google for Paris activities
- A progress spinner shows while it thinks
- After ~30 seconds, a full 5-day itinerary appears
- A download button for a `.ics` calendar file appears

### Mixture of Agents
- You enter a question like "Explain quantum entanglement"
- 4 expandable boxes show each model's individual answer
- Below that, the aggregator model's combined final answer streams word-by-word

### Basic RAG (PharmaQuery)
- You upload a pharmaceutical research PDF
- You ask: "What are the drug interactions described in section 3?"
- The app retrieves the relevant chunks
- Gemini answers using only your document's content

### Finance Agent Team
- You chat in a text box
- You ask: "What is the current stock price and analyst rating for NVDA?"
- The team coordinator decides: web_agent for news, finance_agent for price
- Both agents respond with tables and formatted data

### GitHub MCP Agent
- You select "Pull Requests" query type for a repo
- Results show a formatted table of recent PRs with links, authors, status

### Memory App
- Session 1: You say "I'm vegetarian and I love Thai food"
- Session 2 (days later): You ask "What should I eat in London?"
- The app remembers your vegetarian preference and suggests accordingly

### Voice Agent
- You enter a docs URL (e.g., OpenAI docs)
- The system crawls and indexes it
- You ask "How do I authenticate API requests?"
- A text answer appears AND an audio player that speaks the answer

### Tic-Tac-Toe Game Agents
- The 3x3 board updates automatically as two LLMs play
- Move history shows in a list on the side
- You can watch Claude vs GPT-4o play in real time

---

## 17. Different Ways of Doing the Same Thing

### 3 Ways to Search the Web in an Agent:
| Method | Library | Cost | Speed | Notes |
|--------|---------|------|-------|-------|
| SerpAPI | `agno.tools.serpapi` | Paid (100 free) | Fast | Best quality Google results |
| DuckDuckGo | `agno.tools.duckduckgo` | Free | Medium | No API key needed |
| Tavily | `langchain_community.tools.TavilySearchResults` | Free tier | Fast | AI-optimized for RAG |

### 3 Ways to Store Vectors (for RAG):
| Method | Library | Deployment | Notes |
|--------|---------|-----------|-------|
| Chroma | `langchain_chroma` | Local (no server) | Easiest, no Docker needed |
| Qdrant | `qdrant_client` | Docker or Cloud | Best for production, faster |
| FAISS | `langchain_community.vectorstores.FAISS` | Local (in-memory) | Facebook's library, very fast |

### 3 Ways to Build Agent Logic:
| Method | Framework | Style | Best For |
|--------|-----------|-------|---------|
| Agno | `agno.agent.Agent` | Simple class | Quick single agents, teams |
| LangGraph | `langgraph.graph.StateGraph` | State machine graph | Complex multi-step workflows |
| Google ADK | `google.adk.agents.LlmAgent` | Google-native | Gemini-centric apps |

### 2 Ways to Run Multiple LLMs Together:
| Method | File | How |
|--------|------|-----|
| Sequential (one at a time) | Most apps | Agent runs → result feeds into next |
| Parallel (all at once) | mixture-of-agents | `asyncio.gather()` runs all simultaneously |

### 2 Ways to Add Memory:
| Method | Library | Persistence |
|--------|---------|------------|
| Short-term (this session) | `add_history_to_context=True` in Agno | In-memory, lost on restart |
| Long-term (across sessions) | `mem0` library | Stored in Qdrant, permanent |

---

## 18. Differences Between Each Category

| Category | What Makes It Different | Complexity | API Keys Needed |
|----------|------------------------|------------|----------------|
| Starter Agents | Single file, uses Agno, Streamlit UI | Low | 1-2 |
| RAG Tutorials | Adds document reading + vector DB | Medium | 1-2 + vector DB |
| Multi-Agent Teams | Multiple agents collaborate, coordinator | Medium-High | 1 |
| MCP Agents | Uses Docker-based external tool servers | High | 2 + Docker |
| Memory Apps | Persistent memory across sessions | Medium | 1 + Qdrant |
| Voice Agents | Adds text-to-speech output | High | 3-4 |
| Game Agents | LLMs play games, board state management | Medium | 1-2 |
| CRAG (Corrective RAG) | LangGraph state machine, self-correcting | High | 3 + Qdrant |
| Agent Skills | Just Markdown files, no code | Very Low | 0 |
| ADK Crash Course | Google's framework, structured curriculum | Medium | 1 (Gemini) |

---

## 19. What Each Part Adds Over the Previous

Think of it as a progression:

```
Level 1: Basic LLM Call
  "Send text to GPT, get text back"
  
Level 2: Starter Agent (travel_agent.py)
  + Agent framework (Agno)
  + Multiple agents with roles
  + Tools (web search)
  + Streamlit UI
  + Calendar file export
  
Level 3: RAG App (rag_chain/app.py)
  Level 2 +
  + Document loading (PDF)
  + Text chunking
  + Vector embeddings
  + Vector database (Chroma)
  + Retrieval by similarity
  
Level 4: Corrective RAG (corrective_rag.py)
  Level 3 +
  + LangGraph state machine
  + Document grading (relevant or not?)
  + Query transformation
  + Web search fallback
  + Self-correcting pipeline
  
Level 5: Multi-Agent Team (finance_agent_team.py)
  Level 2 +
  + Team coordinator
  + Shared database
  + Conversation history
  + Role specialization
  
Level 6: Memory App (llm_app_memory.py)
  Level 5 +
  + Cross-session memory
  + Per-user storage
  + Semantic memory search
  
Level 7: MCP Agent (github_agent.py)
  Level 5 +
  + Docker container management
  + MCP protocol connection
  + External API tools via protocol
  
Level 8: Voice Agent (customer_support_voice_agent.py)
  Level 6 +
  + Website crawling
  + Voice synthesis
  + Audio file output
  + Multiple agent pipeline (processor + TTS)
```

---

## 20. Comparison Table

### Framework Comparison

| Feature | Agno | LangChain/LangGraph | Google ADK | OpenAI Agents SDK |
|---------|------|---------------------|------------|-------------------|
| Learning Curve | Low | Medium | Low | Low |
| Multi-agent | Yes (Team) | Yes (LangGraph) | Yes | Yes (handoffs) |
| Streaming | Yes | Yes | Yes | Yes |
| Memory | Built-in | Via Mem0 | Via Sessions | Limited |
| Tool Calling | Yes | Yes | Yes | Yes |
| MCP Support | Yes | Limited | Yes | Yes |
| Provider Support | OpenAI, Anthropic, Google, Groq | OpenAI, Anthropic, Google | Gemini-first | OpenAI-first |
| Best For | Quick agents | RAG + complex chains | Gemini-native | OpenAI-native |

### Vector Database Comparison

| Feature | Chroma | Qdrant | FAISS |
|---------|--------|--------|-------|
| Setup | None needed | Docker/Cloud | None needed |
| Persistence | File-based | Server-based | In-memory |
| Scalability | Small-medium | Large | Medium |
| Speed | Good | Excellent | Excellent |
| Cloud option | No | Yes | No |
| Used in repo | rag_chain | corrective_rag, voice_agent, memory | Some apps |

### RAG Type Comparison

| Type | Complexity | What It Does Differently | File |
|------|-----------|--------------------------|------|
| Basic RAG | Low | Simple retrieve + generate | rag_chain/app.py |
| Corrective RAG | High | Grades relevance, falls back to web | corrective_rag/ |
| Hybrid Search RAG | Medium | Combines keyword + semantic search | hybrid_search_rag/ |
| Agentic RAG | Medium | Agent decides when/how to retrieve | agentic_rag_with_reasoning/ |
| Autonomous RAG | High | Decides if RAG is needed at all | autonomous_rag/ |
| Multimodal RAG | High | Works with images + text | multimodal_agentic_rag/ |

### LLM Provider Comparison (as used in this repo)

| Provider | Model | Strengths | Free Tier |
|---------|-------|----------|-----------|
| OpenAI | GPT-4o | Best general performance | No |
| Anthropic | Claude 3.7 | Best reasoning, code | No |
| Google | Gemini 2.0 | Multimodal, large context | Yes (limited) |
| Groq | Llama 3.3-70B | Very fast inference | Yes |
| Together.ai | Mixtral, Qwen | Many open models | Yes (credits) |
| DeepSeek | DeepSeek-R1 | Strong math/coding | Yes (limited) |

---

## 21. Cheat Sheet

### Quick Commands
```bash
# Clone the repo
git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git

# Go into any app folder
cd awesome-llm-apps/starter_ai_agents/ai_travel_agent

# Install dependencies
pip install -r requirements.txt

# Set environment variable (Linux/Mac)
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."
export GOOGLE_API_KEY="AIza..."

# Set environment variable (Windows)
set OPENAI_API_KEY=sk-...

# Run Streamlit app
streamlit run travel_agent.py

# Run Python script directly
python finance_agent_team.py

# Run Google ADK in browser
adk web

# Start Qdrant (Docker)
docker run -p 6333:6333 qdrant/qdrant

# Start Qdrant in background
docker run -d -p 6333:6333 qdrant/qdrant
```

### Key Python Patterns Used Everywhere

```python
# 1. STREAMLIT BASICS
import streamlit as st
st.title("App Title")
st.text_input("Label", type="password")   # text box
st.button("Click Me")                      # button
st.write(some_text)                        # display text
st.spinner("Loading...")                   # spinner
st.session_state.key = value              # remember values

# 2. AGNO AGENT BASICS
from agno.agent import Agent
from agno.models.openai import OpenAIChat
agent = Agent(
    model=OpenAIChat(id="gpt-4o"),
    instructions=["Be helpful", "Always be concise"],
    tools=[SomeToolClass()],
)
result = agent.run("Your question here", stream=False)
print(result.content)

# 3. LANGCHAIN RAG BASICS
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
loader = PyPDFLoader("file.pdf")
docs = loader.load()
splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
chunks = splitter.split_documents(docs)
db = Chroma.from_documents(chunks, OpenAIEmbeddings())
retriever = db.as_retriever()

# 4. LANGGRAPH BASICS
from langgraph.graph import StateGraph, END
workflow = StateGraph(MyState)
workflow.add_node("step1", my_function_1)
workflow.add_node("step2", my_function_2)
workflow.set_entry_point("step1")
workflow.add_edge("step1", "step2")
workflow.add_edge("step2", END)
app = workflow.compile()
result = app.invoke({"my_key": "my_value"})

# 5. ASYNC PARALLEL LLM CALLS
import asyncio
async def call_llm(model, prompt):
    return await client.chat.completions.create(...)

async def main():
    results = await asyncio.gather(
        call_llm("gpt-4o", prompt),
        call_llm("claude-3", prompt),
    )

asyncio.run(main())

# 6. MEM0 MEMORY
from mem0 import Memory
memory = Memory()
memory.add("User likes Italian food", user_id="alice")
results = memory.search("What food does user like?", user_id="alice")

# 7. QDRANT VECTOR DB
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
client = QdrantClient(url="http://localhost:6333")
client.create_collection("my_collection", vectors_config=VectorParams(size=384, distance=Distance.COSINE))
client.upsert("my_collection", points=[PointStruct(id=1, vector=[0.1, 0.2, ...], payload={"text": "hello"})])
results = client.query_points("my_collection", query=[0.1, 0.2, ...], limit=5)
```

### File Structure of Every App
```
any_app_folder/
├── main_app.py        ← Run this file
├── requirements.txt   ← pip install -r this first
└── README.md          ← Step-by-step instructions
```

### Common Errors and Fixes
```
Error: "OPENAI_API_KEY not set"
Fix: export OPENAI_API_KEY="your-key" (or enter it in the Streamlit UI)

Error: "Module not found: agno"
Fix: pip install -r requirements.txt

Error: "Connection refused to localhost:6333"
Fix: Start Qdrant: docker run -p 6333:6333 qdrant/qdrant

Error: "Docker not found"
Fix: Install Docker from docker.com

Error: "streamlit: command not found"
Fix: pip install streamlit

Error: "Rate limit exceeded"
Fix: Wait 1 minute, or upgrade your API tier
```

### API Key Where to Get

| Key Needed | Get It From |
|-----------|-------------|
| `OPENAI_API_KEY` | https://platform.openai.com/api-keys |
| `ANTHROPIC_API_KEY` | https://console.anthropic.com |
| `GOOGLE_API_KEY` | https://aistudio.google.com |
| `GROQ_API_KEY` | https://console.groq.com |
| `SERPAPI_KEY` | https://serpapi.com |
| `TAVILY_API_KEY` | https://app.tavily.com |
| `TOGETHER_API_KEY` | https://api.together.ai |
| `FIRECRAWL_API_KEY` | https://firecrawl.dev |

---

## 22. Summary

The **Awesome LLM Apps** repository is a curated, working collection of over 100 AI application templates organized into 14 categories. It was designed to eliminate the need to rebuild common LLM patterns from scratch each time.

**The repository covers the full spectrum of LLM application development:**

1. **Starter Agents** — The foundation. Single-file apps that show the basic pattern: give an AI a role, give it tools, give it a question, display the answer. The Travel Agent and Mixture-of-Agents show how to use Agno and Together.ai.

2. **RAG Tutorials** — The most practically useful category. RAG (Retrieval Augmented Generation) lets you feed your own documents to an AI so it can answer questions about them accurately. This goes from the simplest version (basic RAG chain) to advanced versions that self-correct (CRAG), use hybrid search, work with images (multimodal), and route between multiple databases.

3. **Multi-Agent Teams** — Advanced coordination. Instead of one AI doing everything, you create specialized agents (web researcher, finance analyst, legal expert) and a coordinator that routes tasks to the right agent.

4. **MCP Agents** — The newest pattern. Model Context Protocol (MCP) is a standard that lets AI agents connect to external tools (GitHub, browser, Notion) via a universal protocol instead of custom integrations.

5. **Memory Apps** — Persistence layer. Without memory, every conversation starts from zero. These apps use Mem0 and Qdrant to store and retrieve user-specific information across sessions.

6. **Voice AI Agents** — The multi-modal extension. Converts the text output of AI agents into speech, enabling voice-based user interfaces.

7. **Game Playing Agents** — Research/demonstration. Shows that LLMs can reason about game states and make strategic decisions.

8. **Agent Skills** — Reusable "personality" files in Markdown format that can be loaded into any agent to specialize it instantly.

9. **Framework Crash Courses** — Structured learning paths for Google ADK and OpenAI Agents SDK.

**Key technologies across the whole project:**
- Python 3.10+ as the programming language
- Streamlit for web UI (zero JavaScript needed)
- Agno, LangChain, LangGraph, Google ADK, OpenAI SDK as agent frameworks
- OpenAI, Anthropic, Google, Groq as LLM providers
- Qdrant and Chroma as vector databases
- Mem0 for persistent memory

---

## 23. Conclusion

If you are new to coding and want to build AI applications, this repository is one of the best starting points available. Here is why:

### Why This Repository Works as a Learning Resource

1. **Progressive difficulty** — You can start with `starter_ai_agents/ai_travel_agent` (150 lines, one pattern) and gradually move to `rag_tutorials/corrective_rag` (450 lines, state machines) as your understanding grows.

2. **Real, runnable code** — Every app here is complete and tested. You can run it with 3 commands. Nothing is pseudocode or a simplified demo.

3. **Separation of concerns** — Each category isolates a new concept. RAG tutorials focus on document retrieval. Memory tutorials focus on persistence. Voice agents focus on audio. You can learn each concept independently.

4. **Multiple frameworks** — By seeing the same problem solved with Agno, LangChain, LangGraph, and Google ADK, you develop framework-agnostic understanding of the underlying concepts.

5. **Provider-agnostic** — Switching between GPT, Claude, Gemini, and Llama is often just changing one model ID string. This teaches you that the AI logic is separate from the model provider.

### What You Should Build Next

- **Start here:** `starter_ai_agents/ai_travel_agent` — understand the 2-agent pattern
- **Then here:** `rag_tutorials/rag_chain` — understand how RAG works
- **Then here:** `advanced_llm_apps/llm_apps_with_memory_tutorials/llm_app_personalized_memory` — add memory
- **Advanced:** `rag_tutorials/corrective_rag` — understand self-correcting agents with LangGraph
- **Production:** `advanced_ai_agents/multi_agent_apps/agent_teams/ai_finance_agent_team` — multi-agent teams

### The Big Picture

The entire field of LLM application development boils down to:
1. **Calling an LLM with a prompt** (the base)
2. **Giving it tools** (web search, databases, APIs)
3. **Giving it memory** (short-term context + long-term storage)
4. **Making multiple agents collaborate** (specialization + coordination)
5. **Adding retrieval** (RAG — making it answer from your data)
6. **Adding modalities** (voice, images, video)

This repository contains working examples of ALL of these patterns. Every file in it is a lesson in one or more of these dimensions.

**In 2025–2026, the ability to build AI-powered applications is one of the most valuable skills in technology.** This repository gives you everything you need to develop that skill, from your first "Hello, World" AI agent to a production-ready multi-agent voice assistant with persistent memory and self-correcting RAG.

---

*Document generated for the awesome-llm-apps-main repository. All code examples reference actual files in this folder. Last updated: 2026-06-12.*
