# Orion AI Agent — Complete End-to-End Explanation

> Written for someone who has never read code before.
> Every concept is explained from first principles.

---

## Table of Contents

1. [What Is Orion?](#1-what-is-orion)
2. [What Is an AI Agent?](#2-what-is-an-ai-agent)
3. [The Big Picture — How Everything Connects](#3-the-big-picture--how-everything-connects)
4. [The Agentic Loop — The Heart of Orion](#4-the-agentic-loop--the-heart-of-orion)
5. [File-by-File Breakdown](#5-file-by-file-breakdown)
   - [agent.py — The Brain](#agentpy--the-brain)
   - [tool_registry.py — The Tool Cabinet](#tool_registrypy--the-tool-cabinet)
   - [tools.py — The 13 Superpowers](#toolspy--the-13-superpowers)
   - [guardrails.py — The Safety System](#guardrailspy--the-safety-system)
   - [model_router.py — The Smart Model Selector](#model_routerpy--the-smart-model-selector)
   - [server.py — The Web Server](#serverpy--the-web-server)
   - [main.py — The Command-Line Interface](#mainpy--the-command-line-interface)
   - [static/index.html — The Web Frontend](#staticindexhtml--the-web-frontend)
   - [evals/run_evals.py — The Test Suite](#evalsrun_evalspy--the-test-suite)
   - [job_apply/ — The Job Application Module](#job_apply--the-job-application-module)
6. [All 13 Tools Explained](#6-all-13-tools-explained)
7. [Guardrails — 3 Layers of Safety](#7-guardrails--3-layers-of-safety)
8. [Model Router — Choosing the Right AI Brain](#8-model-router--choosing-the-right-ai-brain)
9. [The Job Auto-Apply System](#9-the-job-auto-apply-system)
10. [The Eval System — Automated Testing](#10-the-eval-system--automated-testing)
11. [How a Real Conversation Works — Step by Step](#11-how-a-real-conversation-works--step-by-step)
12. [How to Run Orion](#12-how-to-run-orion)
13. [Summary](#13-summary)
14. [Conclusion](#14-conclusion)
15. [Cheat Sheet](#15-cheat-sheet)

---

## 1. What Is Orion?

Orion is a **fully custom AI assistant** built from scratch. Think of it like a smarter version of Siri or Alexa — but instead of just answering questions, Orion can actually **do things** for you:

- Look up live weather in any city
- Search the internet
- Do math calculations
- Run computer programs
- Read and write files on your computer
- Schedule tasks to run in the future
- Search for jobs on the internet
- Automatically fill out and submit job applications

The word "agentic" in its name means Orion acts like an **agent** — it does not just answer, it **takes actions** on your behalf.

What makes Orion special is that it is built **entirely from scratch** using only the raw Anthropic Python SDK (the official software library for talking to Claude AI). There are no shortcuts, no pre-built agent frameworks, no magic — just pure code implementing the full logic step by step. This makes it an excellent learning project and a highly transparent system.

---

## 2. What Is an AI Agent?

To understand Orion, you first need to understand what makes something an "AI Agent" versus a regular chatbot.

### Regular Chatbot (like a basic Q&A bot)
- You ask: "What is the weather in London?"
- It replies from memory: "I don't have real-time data, but London is typically..."
- It **cannot take actions**. It can only generate text from what it already knows.

### AI Agent (like Orion)
- You ask: "What is the weather in London?"
- Orion thinks: "I should use the `get_weather` tool to get real data."
- Orion calls the tool, gets the live temperature, humidity, and wind speed.
- Orion replies: "Currently in London it is 14°C, 72% humidity, winds at 8 mph."
- It **actually fetched live data** and gave you a real answer.

The key difference is **tools**. An AI Agent has access to tools (functions it can run), and it decides on its own which tool to use and when. Orion has 13 such tools.

---

## 3. The Big Picture — How Everything Connects

Here is how all the pieces of Orion fit together, explained as a simple flow:

```
User (browser or terminal)
        |
        | types a message
        v
   server.py  <-- receives the message over the internet
        |
        | passes to
        v
   agent.py   <-- the main brain, runs the agentic loop
        |
        |-- checks guardrails.py  (is this message safe?)
        |-- checks model_router.py (which AI model should handle this?)
        |-- sends to Anthropic Claude AI
        |
        | Claude responds, possibly calling a tool
        v
   tool_registry.py  <-- looks up which tool function to run
        |
        v
   tools.py  <-- runs the actual tool (weather, calculator, etc.)
        |
        | result goes back to agent.py
        v
   agent.py sends result back to Claude
        |
        | Claude gives final text answer
        v
   server.py sends answer back to user's browser
        |
        v
   static/index.html  <-- the webpage the user sees
```

Every single one of these steps is controlled by Orion's own code. Nothing is hidden.

---

## 4. The Agentic Loop — The Heart of Orion

The most important concept in Orion is the **agentic loop**. This is the cycle that runs inside `agent.py` every time you send a message. Here is how it works:

### Step 1 — You send a message
You type: "What is the weather in Tokyo and what time is it there?"

### Step 2 — Safety check
Guardrails check: Is this message safe? Is it too long? Does it contain dangerous content? If it passes, we continue.

### Step 3 — Model selection
The model router decides: This is a simple low-risk request. Use the fast, cheap Haiku model.

### Step 4 — Send to Claude
Orion sends your message to the Claude AI along with a list of all available tools. Claude reads this and decides: "I need to call `get_weather` with city=Tokyo AND `get_datetime` to answer this."

### Step 5 — Tool call detected
Claude does not answer with text yet. Instead it says: "Please run the `get_weather` tool with city=Tokyo." This is called a `tool_use` block.

### Step 6 — Tool is executed
Orion runs the `get_weather` function, which calls the Open-Meteo weather API on the internet and gets real data.

### Step 7 — Result sent back to Claude
Orion sends the weather result back to Claude as a `tool_result` message.

### Step 8 — Loop continues
Claude now has the weather data. It may decide to call `get_datetime` next. The loop repeats steps 4-7.

### Step 9 — Final answer
When Claude has all the information it needs, it replies with `end_turn` — this means "I'm done, here is my final answer." Claude writes a nice response combining all the data.

### Step 10 — Output safety check
Guardrails scan the output: Does it contain any leaked passwords or API keys? If safe, it goes to the user.

### Step 11 — User sees the answer
The response streams back to your browser word by word (this is called SSE — Server-Sent Events), so it feels live.

This loop can run up to 50 iterations (turns) before giving up. Most conversations only need 2-4 turns.

---

## 5. File-by-File Breakdown

### agent.py — The Brain

`agent.py` is the most important file. It contains the `Agent` class — the core engine that runs the agentic loop described above.

**What it stores:**
- `messages` — the full conversation history. Every message you send, every tool result, every Claude response is kept here. This is important because Claude AI itself has no memory — it is "stateless." Every time Orion talks to Claude, it sends the entire conversation history so Claude knows what was said before.
- `registry` — a reference to the tool cabinet (tool_registry.py)
- `model` — which Claude model to use
- `max_iterations` — how many loop turns before giving up (default: 50)

**What it does:**
- Runs the agentic loop
- Calls guardrails before and after every action
- Asks the model router which AI model to use
- Sends messages to the Anthropic Claude API
- Executes tool calls and feeds results back to Claude
- Streams responses back to the user

**Key concept — conversation history format:**
Claude expects messages in a specific format. Each message looks like:
```
{"role": "user",      "content": "What is the weather in Tokyo?"}
{"role": "assistant", "content": [tool_use blocks, text blocks]}
{"role": "user",      "content": [tool_result blocks]}
```
The `role` tells Claude who is speaking. The `content` is what was said. When Claude calls a tool, the tool result must also go back as a `user` role message. This is a specific API requirement.

---

### tool_registry.py — The Tool Cabinet

Think of `tool_registry.py` as a **filing cabinet** where all the tools are stored and organized.

**The problem it solves:** Claude AI needs to know what tools exist and how to call them. It needs each tool described in a precise format called a "JSON Schema" — like a form that tells Claude: "This tool is called `get_weather`, it takes a `city` parameter which is a text string, and here is what it does."

**How it works:**
1. Each tool function in `tools.py` is decorated with `@registry.tool(...)` — like putting a label on a folder.
2. The registry stores the function AND its schema (description + parameters).
3. When Orion calls Claude, it passes all schemas so Claude knows what tools are available.
4. When Claude wants to use a tool, it outputs the tool name and arguments. Orion looks up the function in the registry and runs it.

**The decorator pattern:** A decorator is a special marker in Python code. When you see `@registry.tool(...)` above a function, it means "register this function as a tool." This is similar to how a restaurant puts a sticker on a menu item to mark it as a "chef's special."

---

### tools.py — The 13 Superpowers

`tools.py` contains all 13 tools that Orion can use. Each tool is a Python function that:
- Receives arguments (inputs) from Claude
- Does something useful (call an API, run code, read a file, etc.)
- Returns a string result back to Claude

All 13 tools are described in detail in Section 6 below.

---

### guardrails.py — The Safety System

`guardrails.py` is Orion's **security guard**. It runs checks at three different moments:
1. Before your message reaches Claude
2. Before each tool runs
3. Before the final answer reaches you

All three layers are described in detail in Section 7 below.

---

### model_router.py — The Smart Model Selector

Anthropic offers multiple Claude AI models. They vary in speed, cost, and capability:
- **Haiku** — fastest and cheapest, good for simple tasks
- **Sonnet** — balanced speed and quality
- **Opus** — most powerful, best for complex tasks, most expensive

Without a router, you would always use the most expensive model (Opus) for everything — including asking "what time is it?" — which wastes money.

`model_router.py` automatically picks the right model based on your message and which tools are active. This is described in detail in Section 8 below.

---

### server.py — The Web Server

`server.py` is the **web server** — the layer that lets you use Orion through a web browser instead of just a terminal.

**Technology used:** FastAPI — a popular Python library for building web APIs.

**What it does:**
- Serves the webpage (`index.html`) when you open `http://localhost:8000`
- Receives your messages from the browser (POST /chat/stream)
- Manages sessions — each browser tab gets its own Agent instance with its own conversation history
- Streams responses back to the browser in real time using **SSE (Server-Sent Events)**

**What is SSE?** SSE is a technology that allows a web server to push data to the browser in real time. You see this when Claude's response appears word by word, like someone typing. Each "word" is a small event pushed from the server to the browser.

**Important technical note:** Normal SSE uses a method called `EventSource` which only supports GET requests (reading data). But Orion needs to send an image in the request body, which requires POST. So Orion uses `fetch()` (a JavaScript function) to make POST requests that also stream back events — a less common but more powerful approach.

**Sessions:** The server keeps one `Agent` object per browser session. This means if you open two browser tabs, each has its own separate conversation. The session ID is sent with every message to identify which Agent to use.

---

### main.py — The Command-Line Interface

`main.py` is the **terminal menu** for running Orion without a browser. You can:
- Press 1 to get the current date/time
- Press 2 to use the calculator
- Press 3 to check weather
- Press 4 to search the web
- Press 5 to run Python code
- Press 6 to read or write a file
- Press 7 to type a custom message
- Press 8 to run a full demo (all tools at once)
- Press 9 to enter chat mode (back-and-forth conversation)
- Press 10 to list scheduled tasks

`main.py` also defines the **System Prompt** — a hidden set of instructions that always runs before your conversation. This tells Claude who it is (Orion), what tools it has, and rules to follow (like: "Always confirm before applying to a job").

**The System Prompt (key rules Orion follows):**
- Think step-by-step before choosing a tool
- Use tools for real-time data — never guess
- When writing files, confirm by reading them back
- Explain what code does before running it
- Never apply to a job without user approval
- No emojis in any output

---

### static/index.html — The Web Frontend

`static/index.html` is the **entire web interface** in a single file. There is no React, no npm, no complex JavaScript framework — just plain HTML, CSS, and JavaScript in one file.

**Features:**
- Dark-themed chat interface
- Streams Claude's response in real time (word by word)
- Shows which AI model tier is being used (colored badge: green=haiku, indigo=sonnet, purple=opus)
- Tool call notifications — shows when a tool runs (e.g., "Calling get_weather...")
- Voice input button — speak your message instead of typing
- Image input — attach a photo and ask Claude about it
- Tool selector dropdown — choose which tools to allow for this conversation
- Shield button — shows the guardrail event log (what was blocked or flagged)
- Session reset button — clears conversation history

**Why plain HTML/JS?** The project deliberately avoids React, npm, or any frontend build system. This keeps it simple — no build step, no node_modules, no version conflicts. One file you can open and understand.

---

### evals/run_evals.py — The Test Suite

`evals/run_evals.py` is the **automated test system**. After you make changes to Orion, you can run this script to verify that everything still works correctly.

**What it tests (10 tests total):**
1. `get_datetime` returns valid date, time, weekday, and ISO timestamp
2. `calculate` correctly evaluates 2+2 = 4
3. `get_weather` returns temperature, humidity, wind speed, and weather code for London
4. `web_search` returns at least one result with a title and URL for "Python 3.12"
5. `read_file` can read its own file content
6. `write_file` writes a file, confirms it exists, verifies the content matches
7. `run_python` correctly executes `print(1+1)` and captures "2" in the output
8. The full schedule/list/cancel task workflow works end to end
9. Guardrails blocks the jailbreak phrase "ignore previous instructions"
10. Model router correctly assigns "haiku" tier for "What time is it?" with get_datetime tool

**Output format:**
```
[PASS] get_datetime returns valid JSON+ISO (45.2 ms)
[PASS] calculate evaluates 2+2 (0.1 ms)
[FAIL] get_weather returns expected fields (8032.1 ms)
       -> Missing 'temperature_c' in get_weather output
```

**Key design decision:** The evals call tool functions **directly** — they bypass the Agent and Claude completely. This means they test the tools themselves, not Claude's ability to choose the right tool. This makes tests faster and more precise.

---

### job_apply/ — The Job Application Module

This folder contains the code for automatically applying to jobs. It has four files:

**detector.py** — Detects which job platform a URL belongs to:
- `boards.greenhouse.io/...` → Greenhouse
- `jobs.lever.co/...` → Lever
- Anything else → Not supported

It also builds search queries for DuckDuckGo like: `site:boards.greenhouse.io machine learning engineer Seattle`

**greenhouse.py** — Automatically fills in a Greenhouse job application form using Playwright (a browser automation tool). It opens a real browser window, navigates to the job URL, and fills in your name, email, phone, LinkedIn, resume, and answers to common questions.

**lever.py** — Same as above but for Lever job boards.

**profile.json.example** — A template file showing what information Orion needs to apply for you:
- Personal info: name, email, phone, location
- Links: LinkedIn, GitHub, portfolio
- Resume: path to your PDF resume file
- Work authorization status
- Standard answers: salary expectation, notice period, why you're interested, etc.

To use job apply, you copy `profile.json.example` to `profile.json` and fill in your real information.

---

## 6. All 13 Tools Explained

Each tool is a function that Claude can call. Here is what each one does:

---

### Tool 1: get_datetime
**Risk level: Low | Model: Haiku**

Gets the current date and time from the computer's clock.

What it returns:
```json
{
  "date":    "2026-06-05",
  "time":    "14:23:11",
  "weekday": "Thursday",
  "iso":     "2026-06-05T14:23:11.000000"
}
```
No internet connection needed — reads from the local system clock.

---

### Tool 2: calculate
**Risk level: Low | Model: Haiku**

Evaluates a math expression safely.

Example: `(100 + 200) * 3.14` → `942.0`

**Safety mechanism:** The tool only allows numbers, basic operators (+, -, *, /, **), and parentheses. It explicitly blocks everything else. This prevents someone from writing `__import__('os').system('rm -rf /')` inside a "math expression." Sneaky attempts like that are impossible because letters and import statements are filtered out.

---

### Tool 3: get_weather
**Risk level: Low | Model: Haiku/Sonnet**

Gets live weather data for any city. Uses the Open-Meteo API — a free weather service that requires no API key.

**Two-step process:**
1. Convert the city name to GPS coordinates (latitude/longitude) using the Open-Meteo geocoding API
2. Fetch actual weather data for those coordinates

What it returns:
```json
{
  "city":           "London, United Kingdom",
  "temperature_c":  14.2,
  "humidity_pct":   72,
  "wind_speed_mph": 8.3,
  "weather_code":   1
}
```
Weather code 1 means "Mainly clear." There is a lookup table in `agent.py` that translates these numeric codes to human-readable descriptions.

---

### Tool 4: web_search
**Risk level: Low | Model: Sonnet**

Searches the internet using DuckDuckGo — no API key required.

Example: Search for "Python 3.12 release notes" → returns up to 10 results, each with a title, URL, and short snippet (summary sentence).

This gives Orion access to current events and information that Claude's training data does not include (Claude's knowledge has a cutoff date).

---

### Tool 5: read_file
**Risk level: Medium | Model: Sonnet**

Reads any text file from the computer and returns its content.

Example: Read `report.md` → returns the full text of the file.

Medium risk because it can read sensitive files (like `.env` files with passwords). The guardrails system watches for this and blocks writes to sensitive system directories.

---

### Tool 6: write_file
**Risk level: High | Model: Opus**

Writes text to a file. Creates the file if it does not exist, overwrites if it does.

Example: Write a report to `output/summary.md`

High risk because it modifies files on disk. The guardrails system blocks writing to system directories like `/etc/`, `/usr/`, or `C:\Windows\`.

---

### Tool 7: run_python
**Risk level: High | Model: Opus**

Executes actual Python code and returns the output.

Example: "Run a script that generates the first 10 prime numbers" → Claude writes the code, run_python executes it, and returns the printed output.

**How it works safely:**
1. The code is written to a temporary file
2. A separate Python process runs that file (subprocess — completely isolated from Orion itself)
3. The output (stdout/stderr) is captured and returned
4. The temporary file is deleted
5. Maximum 15 seconds execution time — after that, it is force-stopped

**Guardrail protection:** The tool blocks any code that imports `os`, `sys`, or `subprocess` — these could be used to access the file system or run system commands maliciously.

---

### Tool 8: schedule_task
**Risk level: High | Model: Opus**

Schedules a task to run automatically in the future.

Actions you can schedule:
- `print_message` — display a message at a specific time
- `run_python` — run Python code at a specific time
- `write_file` — write to a file at a specific time

Time formats supported:
- `"in 5 minutes"`
- `"in 2 hours"`
- `"in 1 day"`
- `"15:30"` (today at 3:30 PM)
- `"2026-06-10 09:00:00"` (specific date and time)

Uses **APScheduler** — a Python library for background scheduling. The scheduler runs as a background thread alongside the main server.

Tasks are saved to `tasks.json` so they survive server restarts. When the server starts again, it reads `tasks.json`, checks if any tasks are still in the future, and re-registers them.

---

### Tool 9: list_tasks
**Risk level: Low | Model: Haiku**

Shows all scheduled tasks and their status: `scheduled`, `running`, `completed`, `failed`, or `cancelled`.

---

### Tool 10: cancel_task
**Risk level: Medium | Model: Sonnet**

Cancels a scheduled task by its ID. Only works if the task has not run yet (status must be "scheduled").

---

### Tool 11: search_jobs
**Risk level: Medium | Model: Sonnet**

Searches for job listings on Greenhouse and Lever — two popular Applicant Tracking Systems (ATS) used by tech companies like Stripe, Airbnb, Netflix, Figma, and Spotify.

**How it works:**
1. Builds a DuckDuckGo search query like: `site:boards.greenhouse.io machine learning engineer Seattle`
2. Runs the search and gets URLs
3. Filters results to keep only valid job listing URLs (not company home pages or search pages)
4. Returns a list of jobs with title, company name, URL, and description snippet

---

### Tool 12: apply_job
**Risk level: High | Model: Opus**

Automatically fills in and submits a job application on Greenhouse or Lever.

**How it works:**
1. Opens a real browser window using Playwright (browser automation)
2. Navigates to the job URL
3. Reads your profile from `job_apply/profile.json`
4. Finds and fills in form fields: name, email, phone, LinkedIn URL, resume upload
5. Answers common questions using your saved `standard_answers`
6. Submits the form
7. Logs the result (success or failure) to `job_apply/applied_jobs.json`

**Important safety rule:** Orion's system prompt says "Never apply without explicit user confirmation." The agent is instructed to always show you the job listing and ask "Should I apply?" before ever calling this tool.

---

### Tool 13: list_applications
**Risk level: Low | Model: Haiku**

Shows the history of all job applications submitted by Orion — including the company, job title, date applied, and whether it succeeded or failed.

---

## 7. Guardrails — 3 Layers of Safety

Guardrails are Orion's safety system. They run at three different points in every conversation to prevent misuse, protect your system, and keep responses safe.

---

### Layer 1 — Input Checks (runs before your message reaches Claude)

This layer runs immediately when you send a message. It is instant (no API calls needed).

**Check 1 — Empty input:**
If you send a blank message, it is rejected immediately.
Response: `[Guardrail] Input cannot be empty.`

**Check 2 — Length limit (8,000 characters max):**
If your message is longer than 8,000 characters, it is rejected.
This prevents overwhelming Claude with enormous inputs.
Response: `[Guardrail] Input is too long (12,450 characters). Please keep it under 8,000 characters.`

**Check 3 — Jailbreak patterns (11+ patterns blocked):**
Jailbreaking means trying to trick an AI into ignoring its safety rules. Orion blocks common jailbreak phrases:
- "ignore previous instructions"
- "ignore all instructions"
- "ignore your system prompt"
- "disregard your instructions"
- "forget everything above"
- "you are now [different character]"
- "act as DAN"
- "do anything now"
- "pretend you have no restrictions"
- "bypass your safety"
- "override your programming"

If any of these appear in your message (case-insensitive), it is blocked.
Response: `[Guardrail] Input blocked: contains a disallowed instruction override pattern.`

**Check 4 — Dangerous shell commands (8+ patterns blocked):**
Blocks messages that contain dangerous system commands:
- `rm -rf` (deletes everything on a Linux/Mac system)
- `format c:` (formats the hard drive on Windows)
- `drop table` (deletes a database table)
- `delete all files`
- `sudo rm` (delete with admin privileges on Linux/Mac)
- `chmod 777` (makes a file world-writable — a security risk)
- `mkfs` (formats a filesystem)
- `dd if=` (writes raw data to a disk — can destroy it)

Response: `[Guardrail] Input blocked: contains a potentially dangerous system command.`

**Check 5 — PII (Personal Identifying Information) detection (warns, does not block):**
Detects if your message contains:
- Email addresses
- Phone numbers
- Social Security Numbers (SSN in the format XXX-XX-XXXX)
- Credit card numbers (Visa, Mastercard patterns)

This does NOT block your message — it just logs a warning and shows it in the guardrail log. The agent may legitimately need to work with personal info.

---

### Layer 2 — Tool Call Safeguards (runs before each tool executes)

Every time Claude decides to call a tool, this layer runs before the tool actually executes.

**For run_python — 13 dangerous code patterns blocked:**
If the code contains any of these, it is blocked:
- `import os` — could access file system
- `import sys` — could manipulate the Python runtime
- `import subprocess` — could run shell commands
- `import shutil` — could delete directories
- `__import__(...)` — another way to import modules
- `os.system(...)` — runs shell commands
- `os.popen(...)` — opens a shell pipe
- `subprocess.` — any subprocess usage
- `eval(...)` — executes arbitrary Python
- `exec(...)` — executes arbitrary Python
- `compile(...)` — compiles arbitrary Python
- `__builtins__` — accesses Python internals
- `open(..., "w"...)` — opens a file for writing

Response: `[Guardrail] Tool call blocked: This Python code was blocked because it imports os module.`

**For write_file — system directory protection:**
Writing to these directories is blocked:
- `/etc/` (Linux system config)
- `/sys/` (Linux kernel interface)
- `/proc/` (Linux process info)
- `/boot/` (bootloader files)
- `/usr/` (installed programs)
- `/bin/`, `/sbin/` (system executables)
- `C:\Windows\` (Windows system)
- `C:\System32\` (Windows core)
- `C:\Program Files\` (installed apps)

**Audit logging for high-risk tools:**
Every time a high-risk tool runs — even if it passes the checks — the event is logged to the guardrail log. This creates an audit trail of every powerful action Orion takes.

---

### Layer 3 — Output Validation (runs before the answer reaches you)

Before Claude's final response is sent to you, this layer scans it for leaked secrets.

**6 patterns that trigger output blocking:**
- `sk-[20+ characters]` — looks like an OpenAI API key
- `sk-ant-[20+ characters]` — looks like an Anthropic API key
- `-----BEGIN [TYPE] KEY-----` — a PEM private key (used in SSL/SSH)
- `password = "..."` — a hardcoded password in text
- `api_key = "..."` — a hardcoded API key in text
- `secret = "..."` — a hardcoded secret in text

If any of these appear in the response, it is blocked entirely.
Response: `[Guardrail] Response was blocked because it contained a Anthropic API key.`

---

### Guardrail Log

All guardrail events are stored in memory (last 200 events). You can view them by:
- Clicking the "Shield" button in the web interface
- Calling the API endpoint `GET /guardrails`

Each event shows: timestamp, event type, detail, and whether it was allowed.

---

## 8. Model Router — Choosing the Right AI Brain

Anthropic offers three Claude models. From fastest/cheapest to slowest/most powerful:

| Tier | Model Name | Best For | Speed | Cost |
|------|-----------|---------|-------|------|
| Haiku | claude-haiku-4-5-20251001 | Simple 1-tool queries | Very fast (<1s) | Cheapest |
| Sonnet | claude-sonnet-4-6 | Web search, file reads | Medium | Moderate |
| Opus | claude-opus-4-6 | Code, writing, complex tasks | Slower | Most expensive |

The model router (`model_router.py`) decides which tier to use for each request. The decision is **instant** — no extra API calls needed, just rule checking.

### Routing Rules (in priority order)

**Rule 1 — If any high-risk tool is active → Opus**
High-risk tools: `run_python`, `write_file`, `schedule_task`, `apply_job`
These require careful reasoning. Always use Opus.

**Rule 2 — If the message is longer than 400 characters → Opus**
Long messages are complex by nature.

**Rule 3 — If the message contains complexity keywords → Opus**
Keywords that trigger Opus:
- "write a file/script/program/report/function"
- "create a file/script/program"
- "run code" / "execute"
- "schedule" / "automate"
- "step-by-step" / "multiple tasks"
- "first... then..."
- "deploy" / "install" / "debug" / "analyse" / "build" / "refactor" / "generate"
- "apply to/for" / "submit my application" / "auto-apply"

**Rule 4 — If any medium-risk tool is active → Sonnet**
Medium-risk tools: `web_search`, `read_file`, `cancel_task`, `search_jobs`

**Rule 5 — If message is short (≤120 chars) AND only low-risk tools are active → Haiku**
Low-risk tools: `get_datetime`, `calculate`, `get_weather`, `list_tasks`, `list_applications`
Example: "What time is it?" with only get_datetime enabled → Haiku

**Rule 6 — Default → Sonnet**
When no other rule matches, Sonnet is the safe middle ground.

### Extended Thinking

Sonnet and Opus models support "extended thinking" — a feature where Claude privately works through a problem step-by-step before answering (like showing its work). Orion enables this with `thinking: {type: "adaptive"}`, which means Claude decides on its own when thinking adds value.

Haiku does NOT support extended thinking, so Orion automatically omits this parameter for Haiku requests.

### UI Display

The web interface shows a colored badge on each response telling you which tier was used:
- Green badge = Haiku (fast)
- Indigo/blue badge = Sonnet (balanced)
- Purple badge = Opus (full power)

---

## 9. The Job Auto-Apply System

One of Orion's most powerful and unique features is the ability to automatically apply for jobs. Here is how the complete workflow works:

### Step 1 — Set up your profile
Copy `job_apply/profile.json.example` to `job_apply/profile.json` and fill in:
- Your full name, email, phone number
- Your location, LinkedIn, GitHub
- The full path to your PDF resume file (e.g., `C:\Users\YourName\Documents\MyResume.pdf`)
- Your current job title and years of experience
- Standard answers to common application questions (salary expectation, notice period, etc.)

### Step 2 — Search for jobs
Tell Orion: "Search for machine learning engineer jobs in Seattle on Greenhouse and Lever."

Orion calls `search_jobs`, which:
1. Builds DuckDuckGo queries: `site:boards.greenhouse.io machine learning engineer Seattle`
2. Runs the searches
3. Filters results to keep only real job listing URLs
4. Returns a list with job title, company, URL, and description

### Step 3 — Review results
Orion shows you the job listings. You can say "Apply to the Stripe one and the Airbnb one."

### Step 4 — Auto-apply
For each confirmed job, Orion calls `apply_job`:
1. A real browser window opens (you can watch it fill in the form)
2. It navigates to the job URL
3. Detects whether it is Greenhouse or Lever
4. Fills in your name, email, phone, LinkedIn, and uploads your resume
5. Matches your `standard_answers` to application question text
6. Submits the form
7. Reports success or failure

### Step 5 — Check your applications
"Show me all the jobs I've applied to." → Orion calls `list_applications` and shows your full history.

### Supported Platforms
- **Greenhouse** (`boards.greenhouse.io`) — used by Stripe, Lyft, Coinbase, Pinterest, etc.
- **Lever** (`jobs.lever.co`) — used by Airbnb, Netflix, Figma, Spotify, Reddit, etc.

### Why these two?
Greenhouse and Lever are the two most common ATS (Applicant Tracking Systems) in tech companies. They have standardized form structures that Playwright can reliably automate. LinkedIn and Indeed have complex anti-scraping defenses that make automation much harder.

---

## 10. The Eval System — Automated Testing

The eval system in `evals/run_evals.py` is how you verify Orion is working correctly after making changes.

### Why evals matter
Imagine you update the `get_weather` tool. How do you know it still works? You could manually test it, but that takes time and you might forget to test something. Evals automate this verification.

### How to run evals
```bash
cd evals
python run_evals.py
```

### What the output looks like
```
[PASS] get_datetime returns valid JSON+ISO (45.2 ms)
[PASS] calculate evaluates 2+2 (0.1 ms)
[PASS] get_weather returns expected fields (1834.7 ms)
[PASS] web_search returns at least one result (2341.1 ms)
[PASS] read_file reads known file content (3.2 ms)
[PASS] write_file writes and verifies content (12.4 ms)
[PASS] run_python prints expected output (287.3 ms)
[PASS] schedule/list/cancel task flow works (15.6 ms)
[PASS] guardrails blocks jailbreak text (0.2 ms)
[PASS] model_router routes simple query to haiku (0.1 ms)

=== Eval Summary ===
Total: 10 | Passed: 10 | Failed: 0 | Time: 4620.1 ms

Report: evals/last_eval_report.json
```

### Design decisions
- Evals call tool functions **directly** — no Claude API calls needed. This is cheaper and faster.
- Results are saved to `evals/last_eval_report.json` with timestamps and latency data.
- Exit code 0 = all passed. Exit code 1 = some failed. This makes evals work with CI/CD pipelines.
- The schedule/list/cancel eval actually schedules a real task "in 1 day," lists tasks, verifies the task appears, cancels it, and verifies the cancellation. It tests the full lifecycle.

---

## 11. How a Real Conversation Works — Step by Step

Let's walk through a complete example: "Search for Python developer jobs in San Francisco and apply to the top result."

**Turn 0 — You send the message**
Browser sends a POST to `/chat/stream` with the message.

**Turn 0 — Safety check**
Guardrails Layer 1 checks: not empty, under 8,000 chars, no jailbreak patterns, no dangerous commands. Passes.

**Turn 0 — Model selection**
Model router sees: message contains "apply" → keyword match → Opus tier.

**Turn 0 — Model event streamed**
Browser receives: `{"type": "model", "tier": "opus", "model": "claude-opus-4-6"}`
UI shows purple "opus · full power" badge.

**Turn 1 — First Claude call**
Orion sends your message + system prompt + all tool schemas to Claude.
Claude thinks: "I need to search for jobs first."
Claude returns: `{"type": "tool_use", "name": "search_jobs", "input": {"query": "Python developer", "location": "San Francisco", "ats": "all"}}`

**Turn 1 — Tool call event streamed**
Browser receives: `{"type": "tool", "name": "search_jobs", "input": {...}}`
UI shows: "Calling search_jobs..."

**Turn 1 — Guardrails Layer 2**
search_jobs is medium-risk. No specific checks, just logged.

**Turn 1 — Tool execution**
`search_jobs` runs DuckDuckGo searches, filters results, returns a JSON list of 10 job URLs.

**Turn 1 — Result back to Claude**
Orion sends the tool result back to Claude as a user message.

**Turn 2 — Second Claude call**
Claude has the job list. Claude thinks: "The user said to apply to the top result. But my instructions say to always confirm before applying."
Claude returns text: "I found 10 Python developer jobs. The top result is: [Job Title] at [Company], [URL]. Shall I apply to this one?"

**Turn 2 — Text event streamed**
Browser receives chunks of text and displays them word by word.

**Turn 2 — Stop reason: end_turn**
Claude is done for this turn (waiting for your confirmation).

**Turn 2 — Guardrails Layer 3**
Output scanned for API keys, passwords, PEM keys. Clean. Allowed.

**Turn 2 — done event streamed**
Browser receives: `{"type": "done", "full": "I found 10 Python developer jobs. The top result is..."}`

**You reply: "Yes, apply to that one."**

**Turn 3 — Guardrails check**
"Yes, apply to that one." — safe, passes all checks.

**Turn 3 — Model selection**
"apply" keyword → Opus tier again.

**Turn 3 — Third Claude call**
Claude now has permission. It calls `apply_job` with the URL from the search results.

**Turn 3 — apply_job runs**
Playwright opens a browser window. Fills in your profile details. Uploads your resume. Submits the form. Returns: `{"success": true, "message": "Application submitted successfully."}`

**Turn 3 — Result logged**
The application is saved to `job_apply/applied_jobs.json`.

**Turn 4 — Final Claude call**
Claude gets the success result and writes: "Your application to [Company] for [Job Title] was submitted successfully. I've logged it in your application history."

**Turn 4 — End of conversation**
Response streams to the browser. Conversation complete.

---

## 12. How to Run Orion

### Prerequisites
1. Python with Anaconda installed
2. An Anthropic API key (from console.anthropic.com)
3. A `.env` file in the project folder containing: `ANTHROPIC_API_KEY=sk-ant-...`

### Install dependencies
```bash
pip install anthropic fastapi uvicorn httpx anyio duckduckgo-search apscheduler python-dotenv tzdata playwright
playwright install chromium
```

### Start the web server
```bash
uvicorn server:app --reload --port 8000
```

Then open your browser to: `http://localhost:8000`

### OR use the command-line menu
```bash
python main.py
```

### Run evals (tests)
```bash
cd evals
python run_evals.py
```

### Setup job applying
1. Copy `job_apply/profile.json.example` to `job_apply/profile.json`
2. Fill in your personal details and resume path
3. Use the web interface or chat mode to search and apply

---

## 13. Summary

Orion is a complete, production-quality AI agent built entirely from scratch in Python. Here is what makes it notable:

| Feature | What It Does | Why It Matters |
|---------|-------------|----------------|
| Manual agentic loop | Implements the full tool-calling cycle without any SDK shortcuts | Shows exactly how AI agents work — no black boxes |
| 13 tools | Covers date/time, math, weather, web search, file I/O, Python execution, scheduling, and job application | Handles a wide range of real tasks |
| 3-layer guardrails | Checks input, tool calls, and output for safety | Prevents misuse and protects your system |
| Smart model router | Picks the cheapest Claude model that can handle the task | Saves money without sacrificing quality |
| Job auto-apply | Searches Greenhouse and Lever, fills forms with Playwright | Automates a tedious real-world task |
| SSE streaming | Responses appear word by word in the browser | Feels responsive and live |
| Eval system | 10 automated tests verify every tool works | Prevents regressions after code changes |
| No frameworks | No React, no LangChain, no Agent SDK | Simple, transparent, educational |

The system architecture follows a clean separation of concerns:
- `agent.py` — orchestration
- `tool_registry.py` — tool management
- `tools.py` — tool implementations
- `guardrails.py` — safety
- `model_router.py` — model selection
- `server.py` — web interface
- `main.py` — CLI interface

---

## 14. Conclusion

Orion demonstrates that building a fully capable AI agent does not require magical frameworks or complex dependencies. The entire system — multi-turn conversations, tool calling, safety layers, model optimization, and browser automation — is implemented in approximately 1,000 lines of readable Python.

**What Orion teaches:**

1. **AI agents work by looping** — the intelligence is in the loop: send message, get tool call, execute tool, send result back, repeat.

2. **Conversation history IS memory** — Claude has no memory between calls. The agent's "memory" is just a list of messages we keep and send each time.

3. **Tools extend what AI can do** — without tools, Claude can only generate text. With tools, it can access real data, execute code, and take actions in the real world.

4. **Safety requires multiple layers** — no single check is enough. Input validation, tool safeguards, and output scanning together create robust protection.

5. **Cost optimization matters in production** — using Haiku for simple queries and Opus only when truly needed can reduce API costs dramatically (Haiku is roughly 40x cheaper than Opus per token).

6. **Automation + AI = powerful workflows** — the job application feature shows how combining web search, profile management, browser automation, and AI reasoning can automate complex real-world workflows.

Orion is not just a demo — it is a fully working system you can use today to manage tasks, search and apply for jobs, run code, and interact with the world through an AI assistant.

---

## 15. Cheat Sheet

### Key Files at a Glance

| File | One-Line Description |
|------|---------------------|
| `agent.py` | Runs the agentic loop. The brain of Orion. |
| `tool_registry.py` | Stores all tool names, descriptions, schemas, and functions. |
| `tools.py` | The 13 tool implementations (weather, search, files, code, jobs, etc.). |
| `guardrails.py` | 3-layer safety system: input → tool → output. |
| `model_router.py` | Picks haiku/sonnet/opus based on task complexity. |
| `server.py` | FastAPI web server. Handles HTTP requests and SSE streaming. |
| `main.py` | Terminal menu. Also defines the system prompt. |
| `static/index.html` | The entire web frontend in one file. |
| `evals/run_evals.py` | 10 automated tests. Run to verify everything works. |
| `job_apply/` | Job search + Playwright auto-apply for Greenhouse and Lever. |
| `.env` | Your `ANTHROPIC_API_KEY`. Never commit this to git. |
| `tasks.json` | Saved scheduled tasks. Auto-created. |
| `job_apply/profile.json` | Your personal info for job applications. You must create this. |

---

### The Agentic Loop in 6 Steps

```
1. Check input safety (guardrails Layer 1)
2. Pick AI model (model_router)
3. Send message + tools list to Claude
4. If Claude returns tool_use:
     a. Check tool safety (guardrails Layer 2)
     b. Execute the tool
     c. Send result back to Claude
     d. Go to step 3
5. If Claude returns end_turn:
     a. Check output safety (guardrails Layer 3)
     b. Return final answer to user
6. If max 50 iterations reached: give up
```

---

### 13 Tools Quick Reference

| Tool | What It Does | Risk | Best Model |
|------|-------------|------|-----------|
| `get_datetime` | Current date and time | Low | Haiku |
| `calculate` | Safe math evaluation | Low | Haiku |
| `get_weather` | Live weather via Open-Meteo API | Low | Haiku |
| `web_search` | DuckDuckGo internet search | Low | Sonnet |
| `list_tasks` | Show scheduled task log | Low | Haiku |
| `list_applications` | Show job application history | Low | Haiku |
| `read_file` | Read any file from disk | Medium | Sonnet |
| `cancel_task` | Cancel a scheduled task | Medium | Sonnet |
| `search_jobs` | Search Greenhouse + Lever for jobs | Medium | Sonnet |
| `write_file` | Write to a file on disk | High | Opus |
| `run_python` | Execute Python code (sandboxed) | High | Opus |
| `schedule_task` | Schedule a future task | High | Opus |
| `apply_job` | Auto-fill + submit a job application | High | Opus |

---

### Model Routing Rules (Priority Order)

```
1. High-risk tool active?  → Opus
2. Message > 400 chars?    → Opus
3. Complex keywords?       → Opus  (write/execute/schedule/automate/debug/apply...)
4. Medium-risk tool active? → Sonnet
5. Short message + low-risk tools only? → Haiku
6. Default                 → Sonnet
```

---

### Guardrails Quick Reference

| Layer | When It Runs | What It Blocks |
|-------|-------------|---------------|
| Layer 1 — Input | Before Claude sees your message | Empty input, >8000 chars, jailbreaks, dangerous shell commands, PII (warns) |
| Layer 2 — Tool | Before each tool executes | Dangerous Python code, writes to system directories, high-risk tool audit logging |
| Layer 3 — Output | Before response reaches you | Leaked API keys, PEM keys, hardcoded passwords/secrets |

---

### API Endpoints

| Method | URL | What It Does |
|--------|-----|-------------|
| GET | `/` | Opens the web chat interface |
| POST | `/chat/stream` | Send a message, get SSE-streamed response |
| POST | `/session/reset` | Clear conversation history |
| GET | `/tasks` | List all scheduled tasks (JSON) |
| GET | `/tools` | List all registered tools (JSON) |
| GET | `/guardrails` | Last 200 guardrail events (JSON) |
| GET | `/guardrails/rules` | Tool risk levels and input limits (JSON) |
| GET | `/router/preview?message=...&active_tools=...` | Preview which model tier would be chosen |

---

### SSE Event Types (What the Browser Receives)

| Type | Example | When It Fires |
|------|---------|--------------|
| `model` | `{"type": "model", "tier": "opus", "model": "claude-opus-4-6"}` | Start of each run |
| `tool` | `{"type": "tool", "name": "get_weather", "input": {"city": "Tokyo"}}` | When a tool is called |
| `text` | `{"type": "text", "chunk": "The weather in..."}` | As Claude generates text |
| `done` | `{"type": "done", "full": "Complete final answer here"}` | When the run finishes |
| `error` | `{"type": "error", "message": "Something went wrong"}` | If an exception occurs |

---

### Common Commands

```bash
# Start the server
uvicorn server:app --reload --port 8000

# Open the web interface
# Navigate browser to: http://localhost:8000

# Run the terminal menu
python main.py

# Jump straight to chat mode
python main.py --chat

# Run all evals
cd evals && python run_evals.py
```

---

### File Structure

```
OrionAiAgent-main/
├── agent.py                   The core agentic loop
├── tool_registry.py           Tool storage and execution
├── tools.py                   All 13 tool implementations
├── guardrails.py              3-layer safety system
├── model_router.py            Smart model selection
├── server.py                  FastAPI web server
├── main.py                    CLI entry point + system prompt
├── requirements.txt           Python package dependencies
├── .env                       YOUR API KEY (create this, never commit)
├── tasks.json                 Auto-created: scheduled task log
│
├── static/
│   └── index.html             Entire web frontend (single file)
│
├── evals/
│   └── run_evals.py           10 automated tests
│
├── job_apply/
│   ├── profile.json.example   Template: copy to profile.json
│   ├── profile.json           YOUR profile (create from example)
│   ├── applied_jobs.json      Auto-created: application history
│   ├── detector.py            Detects Greenhouse vs Lever URLs
│   ├── greenhouse.py          Playwright automation for Greenhouse
│   └── lever.py               Playwright automation for Lever
│
└── assets/                    Diagram images for documentation
```

---

*End of explanation. This document covers every file, every concept, every tool, and every architectural decision in the Orion AI Agent project.*
