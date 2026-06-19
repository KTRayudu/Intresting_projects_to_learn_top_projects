# Agentic AI for DevOps — Complete End-to-End Explanation

> **Confirmation:** YES, this entire codebase is about building **AI Agents for DevOps tasks**. It is a 6-module hands-on course that takes you from zero AI/LLM knowledge to building a self-healing Kubernetes system.

---

## TABLE OF CONTENTS

1. [What This Course Is About](#1-what-this-course-is-about)
2. [Core Concepts You Must Understand First](#2-core-concepts-you-must-understand-first)
3. [Project Folder Structure](#3-project-folder-structure)
4. [Module 0 — Environment Setup](#4-module-0--environment-setup)
5. [Module 1 — Docker Error Explainer](#5-module-1--docker-error-explainer)
6. [Module 2 — Docker Troubleshooter Agent](#6-module-2--docker-troubleshooter-agent)
7. [Module 3 — Multi-Tool DevOps Agent + MCP](#7-module-3--multi-tool-devops-agent--mcp)
8. [Module 4 — AIOps Demystified (Theory)](#8-module-4--aiops-demystified-theory)
9. [Module 5 — KubeHealer (Self-Healing System)](#9-module-5--kubehealer-self-healing-system)
10. [Module 6 — CI/CD Failure Analyzer](#10-module-6--cicd-failure-analyzer)
11. [How Each Module Builds on the Previous](#11-how-each-module-builds-on-the-previous)
12. [How to Run Every Module Step by Step](#12-how-to-run-every-module-step-by-step)
13. [What the Output Looks Like](#13-what-the-output-looks-like)
14. [Comparison Tables](#14-comparison-tables)
15. [Cheat Sheet](#15-cheat-sheet)
16. [Different Ways to Do the Same Thing](#16-different-ways-to-do-the-same-thing)
17. [Summary](#17-summary)
18. [Conclusion](#18-conclusion)

---

## 1. What This Course Is About

Imagine you are a DevOps engineer. Your job involves:
- Containers running in Docker that sometimes crash
- Kubernetes clusters with broken pods
- GitHub Actions pipelines that fail at 2am

Normally, you would have to **manually** look at logs, run commands, and figure out what is wrong. This course teaches you to build **AI agents** that do this work **automatically**.

An **AI agent** is a program that:
1. Receives a question or a problem
2. Decides which actions (tools) to take
3. Executes those actions (runs real commands on your machine)
4. Reads the results
5. Keeps going until it finds the answer

This is different from a chatbot. A chatbot only talks. An agent **acts**.

---

## 2. Core Concepts You Must Understand First

### 2.1 What is an LLM?
An **LLM (Large Language Model)** is an AI model trained on huge amounts of text. It can understand and generate human language.
- **Ollama** = software that runs LLMs on your own computer for free
- **gemma4** = the specific LLM model used in Day 1 (runs locally, no internet needed)
- **Claude** = Anthropic's LLM used in Day 2 (requires API key, runs in the cloud)

### 2.2 What is a Prompt?
A **prompt** is the text you send to an LLM. The LLM generates a response based on the prompt.

```
Prompt: "Why is my Docker container crashing?"
LLM Response: "Your container is crashing because..."
```

### 2.3 What is a System Prompt?
A **system prompt** is a special instruction you give to the LLM that sets its "personality" or "role". It runs before any user message.

```python
SYSTEM_PROMPT = "You are a Docker expert. When given an error, explain what went wrong."
```

This makes the LLM behave like a Docker expert in every conversation.

### 2.4 What is Temperature?
**Temperature** controls how creative or random the LLM's responses are:
- `temperature=0.0` → Same answer every time (deterministic, reliable for technical advice)
- `temperature=0.3` → Mostly consistent, slightly varied (used in Module 1)
- `temperature=1.0` → Very creative, different every time (good for writing, bad for commands)

### 2.5 What are Tokens?
LLMs process **tokens**, not words. A token is roughly 3/4 of a word.
- "Docker" = 1 token
- "CrashLoopBackOff" = 3-4 tokens
- More tokens = slower and more expensive responses

### 2.6 What is Tool Calling?
**Tool calling** means the LLM can call Python functions you have defined. Instead of just generating text, it can say "I need to run `list_containers()`" and your code executes that function.

```
LLM says: "I should check the container logs."
             ↓
Python code: runs subprocess("docker logs mycontainer")
             ↓
LLM reads: the actual logs from your terminal
             ↓
LLM says: "The container crashed because of OOM (Out of Memory)."
```

### 2.7 What is the ReAct Pattern?
**ReAct = Reason + Act**. This is the loop that agents follow:

```
Reason:  "I need to check what containers exist"
Act:     calls list_containers()
Observe: sees output "broken-app   Exited(1)"
Reason:  "I should get logs from broken-app"
Act:     calls get_logs("broken-app")
Observe: sees "OOMKilled" in logs
Reason:  "Now I have enough information"
Answer:  "The container crashed due to insufficient memory."
```

LangChain's `create_react_agent` handles this loop automatically.

### 2.8 What is LangChain?
**LangChain** is a Python library that makes it easy to:
- Connect to LLMs (Ollama, OpenAI, Anthropic)
- Define tools the LLM can call
- Build agents that use the ReAct loop

### 2.9 What is MCP?
**MCP (Model Context Protocol)** is an open standard for connecting AI systems to tools. Think of it like a USB standard — you write tools once, and ANY AI system that understands MCP can use them. This includes Claude Desktop, VS Code Copilot, Cursor, and more.

### 2.10 What is Temporal?
**Temporal** is a platform for **durable execution** — it makes sure your code runs to completion even if the machine crashes. If your agent is halfway through fixing a Kubernetes cluster and the computer restarts, Temporal resumes exactly where it left off.

### 2.11 What is Kubernetes and what is a Pod?
- **Kubernetes (K8s)** = a system that manages Docker containers across multiple machines
- **Pod** = the smallest unit in Kubernetes, usually contains one container
- **CrashLoopBackOff** = a Kubernetes status meaning the pod keeps crashing and restarting
- **Kind** = a tool that creates a fake Kubernetes cluster on your laptop for testing

---

## 3. Project Folder Structure

```
agentic-ai-for-devops-main/
│
├── README.md                  ← Course overview and tech stack
├── requirements.txt           ← Python packages to install
├── .gitignore                 ← Files git should ignore
│
├── module-0/                  ← Environment setup and verification
│   ├── README.md
│   └── verify_setup.py        ← Checks if all tools are installed correctly
│
├── module-1/                  ← First LLM tool: Docker Error Explainer
│   ├── README.md
│   └── explainer.py           ← Sends Docker errors to LLM, returns explanation
│
├── module-2/                  ← First AI agent: Docker Troubleshooter
│   ├── README.md
│   └── agent.py               ← Agent with 3 Docker tools (list, logs, inspect)
│
├── module-3/                  ← Multi-tool agent + MCP protocol
│   ├── README.md
│   ├── agent.py               ← Agent with 6 tools (Docker + Kubernetes)
│   ├── mcp_server.py          ← Kubernetes tools exposed via MCP protocol
│   ├── agent_with_mcp.py      ← Agent that uses MCP server as tool source
│   └── broken_pod.yaml        ← Kubernetes manifest for a deliberately broken pod
│
├── module-4/                  ← Theory: AIOps landscape + guardrails + Temporal
│   └── README.md
│
├── module-5/                  ← KubeHealer (separate repo, linked here)
│   └── README.md              ← Instructions to clone and run KubeHealer
│
└── module-6/                  ← CI/CD Failure Analyzer
    ├── README.md
    └── ci_analyzer.py         ← Agent that analyzes GitHub Actions failures
```

### What is requirements.txt?

```
ollama             ← Python client library to talk to Ollama (local LLM)
langchain          ← Core LangChain framework
langchain-ollama   ← LangChain's connector to Ollama
langchain-mcp-adapters  ← LangChain's connector to MCP servers
langgraph          ← LangChain's graph-based agent execution engine
fastmcp            ← FastMCP library to build MCP servers
```

---

## 4. Module 0 — Environment Setup

### What this module does
It checks that all required software is installed and working before you write any code.

### File: `module-0/verify_setup.py` — Line by Line

```python
"""
Checks if your machine is ready for the course.
Run: python3 module-0/verify_setup.py
"""
```
This is a docstring (documentation comment). It explains what the file does and how to run it.

```python
import shutil
import subprocess
import sys
```
- `shutil` — Python's built-in library for file/program operations. We use `shutil.which()` to check if a program is installed.
- `subprocess` — Python's built-in library to run shell commands. Used to run `docker info`, `ollama list`.
- `sys` — Python's built-in library for system information. Used to get Python version.

```python
passed = 0
total = 0
```
Two counters. `total` = number of checks run. `passed` = number of checks that succeeded.

```python
def check(name, ok, hint=""):
    global passed, total
    total += 1
    if ok:
        passed += 1
        print(f"  [PASS] {name}")
    else:
        print(f"  [FAIL] {name} — {hint}")
```
This is a helper function. When called:
- `name` = what we are checking (e.g., "Docker")
- `ok` = True if the check passed, False if it failed
- `hint` = optional message shown on failure
- `global passed, total` = tells Python to modify the variables defined outside this function
- It increments `total` every time, increments `passed` only on success
- Prints `[PASS]` or `[FAIL]` with the hint

```python
print("\nChecking your setup...\n")
```
Prints a blank line, then the message, then another blank line. `\n` = newline character.

```python
v = sys.version_info
check("Python 3.10+", v.minor >= 10, f"you have {v.major}.{v.minor}, need 3.10+")
```
- `sys.version_info` returns a named tuple like `(3, 11, 4, 'final', 0)`
- `v.minor` is the second number (11 in Python 3.11)
- `v.minor >= 10` is True if Python is 3.10 or higher
- `f"you have {v.major}.{v.minor}, need 3.10+"` is an f-string (formatted string)

```python
try:
    subprocess.run(["docker", "info"], capture_output=True, timeout=10, check=True)
    check("Docker", True)
except Exception:
    check("Docker", False, "install or start Docker")
```
- `subprocess.run(["docker", "info"], ...)` runs the command `docker info` in the shell
- `capture_output=True` = capture stdout and stderr (don't print to screen)
- `timeout=10` = if Docker doesn't respond in 10 seconds, stop waiting
- `check=True` = raise an exception if the command returns a non-zero exit code (failure)
- If any exception occurs (Docker not installed, not running), the `except` block runs

```python
check("kubectl", shutil.which("kubectl"), "install kubectl")
check("Kind", shutil.which("kind"), "install kind")
```
- `shutil.which("kubectl")` returns the path to kubectl if installed, or `None` if not found
- `None` is treated as `False` in Python, so the check fails if the tool is not found

```python
try:
    out = subprocess.run(["ollama", "list"], capture_output=True, text=True, timeout=10, check=True)
    if "gemma4" in out.stdout:
        check("Ollama + gemma4", True)
    else:
        check("Ollama + gemma4", False, "run: ollama pull gemma4")
except Exception:
    check("Ollama", False, "install from https://ollama.com or run: ollama serve")
```
- `text=True` = return output as string (not bytes)
- `out.stdout` = the text output of `ollama list`
- `"gemma4" in out.stdout` = checks if the word "gemma4" appears in the output
- If it does, the model is already downloaded and ready

```python
print(f"\n{'—' * 40}")
if passed == total:
    print(f"  {passed}/{total} — you're ready for Day 1!")
else:
    print(f"  {passed}/{total} passed — fix the failures above")
print()
```
- `'—' * 40` = prints 40 dash characters as a divider line
- Shows overall result

### How to Run Module 0

```bash
# Step 1: Make sure you are in the project folder
cd agentic-ai-for-devops-main

# Step 2: Create a virtual environment (isolated Python environment)
python3 -m venv .venv

# Step 3: Activate the virtual environment
source .venv/bin/activate       # Linux/macOS
.venv\Scripts\activate          # Windows

# Step 4: Install dependencies
pip install -r requirements.txt

# Step 5: Run the check
python3 module-0/verify_setup.py
```

### Expected Output

```
Checking your setup...

  [PASS] Python 3.10+
  [PASS] Docker
  [PASS] kubectl
  [PASS] Kind
  [PASS] Ollama + gemma4

————————————————————————————————————————
  5/5 — you're ready for Day 1!
```

---

## 5. Module 1 — Docker Error Explainer

### What this module does
You paste a Docker error message. The program sends it to a local LLM (gemma4 via Ollama) and gets back a plain-English explanation with a fix. **This is not an agent** — it is a simple one-shot LLM call. No tools, no loops.

### File: `module-1/explainer.py` — Line by Line

```python
"""
Docker Error Explainer — paste a Docker error, get a human-readable fix.
Run: python3 module-1/explainer.py
"""
```
Docstring explaining the file.

```python
import ollama
```
Imports the `ollama` Python library. This is the official Python client for Ollama. It lets you call `ollama.chat()` in Python instead of running `ollama run` in the terminal.

```python
SYSTEM_PROMPT = """You are a Docker expert. When given a Docker error, explain:
1. What went wrong (plain English)
2. Most likely cause
3. How to fix it (with commands)
Keep it short."""
```
This multi-line string (triple quotes) is the system prompt. It tells the LLM to behave as a Docker expert and structure its answer in three parts. The LLM will follow these instructions for every message in this conversation.

```python
print("\nPaste your Docker error (press Enter twice when done):\n")
```
Prints instructions to the user.

```python
lines = []
while True:
    line = input()
    if line == "":
        break
    lines.append(line)
error = "\n".join(lines)
```
- `lines = []` — starts an empty list to collect input lines
- `while True:` — an infinite loop
- `line = input()` — waits for user to type a line and press Enter
- `if line == "":` — if the user pressed Enter on an empty line, `break` exits the loop
- `lines.append(line)` — adds each non-empty line to the list
- `"\n".join(lines)` — joins all lines back together with newlines between them

This allows the user to paste multi-line error messages. The loop ends when they press Enter on a blank line.

```python
print("\nThinking...\n")
```
Lets the user know the LLM is processing.

```python
response = ollama.chat(
    model="gemma4",
    messages=[
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": error},
    ],
    options={"temperature": 0.3},
)
```
This is the core LLM call:
- `model="gemma4"` — use the gemma4 model
- `messages=[...]` — a list of message dictionaries. Each has a `role` and `content`.
  - `"role": "system"` — this is the system prompt (sets LLM behavior)
  - `"role": "user"` — this is the actual question/input
- `options={"temperature": 0.3}` — low randomness for consistent technical answers

```python
print(response["message"]["content"])
```
- `response` is a dictionary returned by `ollama.chat()`
- `response["message"]` is the response message object
- `response["message"]["content"]` is the actual text the LLM generated

### How to Run Module 1

```bash
# Make sure virtual environment is activated
source .venv/bin/activate

# Run the explainer
python3 module-1/explainer.py

# Paste any Docker error, then press Enter twice
```

### Example Interaction

```
Paste your Docker error (press Enter twice when done):

docker: Error response from daemon: Bind for 0.0.0.0:3000 failed: port is already allocated.

Thinking...

**What went wrong:** Docker tried to map port 3000 on your host machine to the container,
but something else is already using port 3000.

**Most likely cause:** Another container or process is already listening on port 3000.

**How to fix it:**
1. Find what's using port 3000:
   lsof -i :3000
   
2. Either stop that process, or use a different host port:
   docker run -p 3001:3000 your-image
```

---

## 6. Module 2 — Docker Troubleshooter Agent

### What changes from Module 1
Module 1 only reads text and asks the LLM. Module 2 creates an **agent** that can **run real Docker commands**. The LLM decides which commands to run, runs them through Python, and uses the results to answer your question.

### File: `module-2/agent.py` — Line by Line

```python
"""
Docker Troubleshooter Agent — an AI agent that diagnoses Docker issues on its own.
Run: python3 module-2/agent.py
"""

import subprocess
from langchain_ollama import ChatOllama
from langchain_core.tools import tool
from langchain.agents import create_agent as create_react_agent
```
- `subprocess` — to run Docker commands
- `ChatOllama` — LangChain's class for using Ollama models
- `tool` — a decorator that marks a Python function as a "tool" the LLM can call
- `create_react_agent` — creates an agent that uses the ReAct pattern (note: the code imports it with an alias)

#### Tool 1: list_containers

```python
@tool
def list_containers() -> str:
    """List all Docker containers (running and stopped)."""
    result = subprocess.run(["docker", "ps", "-a"], capture_output=True, text=True)
    return result.stdout or result.stderr
```
Line by line:
- `@tool` — this decorator registers the function as a LangChain tool. The LLM reads the docstring to decide when to use this function.
- `def list_containers() -> str:` — function definition. `-> str` means it returns a string.
- `"""List all Docker containers..."""` — this docstring is what the LLM reads. Write it clearly so the LLM knows when to call this tool.
- `subprocess.run(["docker", "ps", "-a"], ...)` — runs `docker ps -a` in the shell
  - `["docker", "ps", "-a"]` = the command split into a list (never use a string here, security risk)
  - `capture_output=True` = capture stdout and stderr
  - `text=True` = return output as string
- `result.stdout or result.stderr` — if stdout is empty, return stderr. The `or` operator returns the first truthy value.

#### Tool 2: get_logs

```python
@tool
def get_logs(container_name: str) -> str:
    """Get the last 50 lines of logs from a Docker container."""
    result = subprocess.run(
        ["docker", "logs", "--tail", "50", container_name],
        capture_output=True, text=True,
    )
    return result.stdout + result.stderr
```
- `container_name: str` — this function takes a parameter. The LLM will provide this value when calling the tool.
- `["docker", "logs", "--tail", "50", container_name]` — runs `docker logs --tail 50 <name>`
- `result.stdout + result.stderr` — combines both output streams (Docker sometimes writes logs to stderr)

#### Tool 3: inspect_container

```python
@tool
def inspect_container(container_name: str) -> str:
    """Get detailed info about a Docker container (state, config, network)."""
    result = subprocess.run(
        ["docker", "inspect", container_name],
        capture_output=True, text=True,
    )
    return result.stdout or result.stderr
```
- `docker inspect` returns detailed JSON about a container: its configuration, state (running/stopped), environment variables, network settings, and more.

#### Creating the Agent

```python
llm = ChatOllama(model="gemma4", temperature=0)
tools = [list_containers, get_logs, inspect_container]
agent = create_react_agent(llm, tools)
```
- `ChatOllama(model="gemma4", temperature=0)` — creates the LLM. `temperature=0` means always give the same, deterministic answer (important for tool-calling).
- `tools = [...]` — list of all functions the LLM can call
- `create_react_agent(llm, tools)` — wires everything together. This creates a LangGraph-based agent that:
  1. Passes your question to the LLM
  2. Checks if the LLM wants to call a tool
  3. If yes, runs the tool and feeds results back
  4. Repeats until the LLM gives a final answer

#### The Conversation Loop

```python
print("\nDocker Troubleshooter Agent")
print("-" * 30)
print("Ask me about your Docker containers. Type 'quit' to exit.\n")

while True:
    question = input("> ").strip()
    if question.lower() in ("quit", "exit", "q"):
        break
    if not question:
        continue

    print("\nThinking...\n")
    result = agent.invoke({"messages": [("user", question)]})
    print(result["messages"][-1].content)
    print()
```
- `input("> ").strip()` — shows a `>` prompt, waits for input, removes leading/trailing whitespace
- `.lower()` — converts to lowercase so "Quit", "QUIT", "quit" all work
- `if not question: continue` — skip empty inputs (user just pressed Enter)
- `agent.invoke({"messages": [("user", question)]})` — sends the question to the agent
  - `{"messages": [("user", question)]}` = the input format LangChain expects
  - `("user", question)` = a tuple of (role, content)
- `result["messages"][-1].content` — gets the last message from the conversation (the agent's final answer)
  - `result["messages"]` = list of all messages (user input + tool calls + agent responses)
  - `[-1]` = last element of the list (the final answer)
  - `.content` = the text content of that message

### How to Run Module 2

```bash
# Step 1: Create a broken container to test with
docker run -d --name broken-app nginx:alpine sh -c "echo 'app starting...' && sleep 2 && exit 1"

# Step 2: Run the agent
python3 module-2/agent.py

# Step 3: Ask questions
# > Why is broken-app crashing?
# > What containers are running?
# > Show me the logs for broken-app

# Step 4: Clean up
docker rm -f broken-app
```

### What the Agent Does (Internally)

```
You:   "Why is broken-app crashing?"

Agent: [Reasoning] I should check what containers exist first.
       [Tool Call]  list_containers()
       [Result]     "broken-app   Exited (1)   ..."

Agent: [Reasoning] broken-app exited with code 1. I need its logs.
       [Tool Call]  get_logs("broken-app")
       [Result]     "app starting...\n"

Agent: [Reasoning] The container exited with code 1 after 2 seconds. I have enough info.
       [Final Answer] "broken-app is crashing because the startup command explicitly
                       exits with code 1 after printing 'app starting...'. This is an
                       intentional failure in the command..."
```

---

## 7. Module 3 — Multi-Tool DevOps Agent + MCP

### What changes from Module 2
Three new things are added:
1. **Kubernetes tools** — the agent can now inspect pods too
2. **MCP server** — the same K8s tools exposed via the Model Context Protocol
3. **`agent_with_mcp.py`** — a different way to connect to tools using MCP instead of direct LangChain

### File: `module-3/agent.py` — What's Added

The file is identical to Module 2's agent.py plus three new Kubernetes tools:

```python
# --- Kubernetes tools ---

@tool
def list_pods(namespace: str = "default") -> str:
    """List all pods in a Kubernetes namespace with their status."""
    result = subprocess.run(
        ["kubectl", "get", "pods", "-n", namespace],
        capture_output=True, text=True,
    )
    return result.stdout or result.stderr
```
- `namespace: str = "default"` — this parameter has a default value. If the LLM doesn't specify a namespace, "default" is used.
- `kubectl get pods -n default` — lists all pods in the "default" namespace

```python
@tool
def describe_pod(pod_name: str, namespace: str = "default") -> str:
    """Get detailed info about a Kubernetes pod including events and conditions."""
    result = subprocess.run(
        ["kubectl", "describe", "pod", pod_name, "-n", namespace],
        capture_output=True, text=True,
    )
    return result.stdout or result.stderr
```
- `kubectl describe pod <name>` — shows detailed information including events (which tell you WHY a pod is failing)

```python
@tool
def get_events(namespace: str = "default") -> str:
    """Get recent Kubernetes events in a namespace (useful for troubleshooting)."""
    result = subprocess.run(
        ["kubectl", "get", "events", "-n", namespace, "--sort-by=.lastTimestamp"],
        capture_output=True, text=True,
    )
    return result.stdout or result.stderr
```
- `--sort-by=.lastTimestamp` — sort events by time, newest last (most useful for troubleshooting)

```python
llm = ChatOllama(model="gemma4", temperature=0)
tools = [
    list_containers, get_logs, inspect_container,   # Docker (from Module 2)
    list_pods, describe_pod, get_events,             # Kubernetes (new)
]
agent = create_react_agent(llm, tools)
```
Now the agent has 6 tools. It automatically uses Docker tools for Docker questions and Kubernetes tools for K8s questions.

### File: `module-3/broken_pod.yaml` — Line by Line

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: broken-pod
  namespace: default
spec:
  containers:
  - name: app
    image: nginx:alpine
    command: ["sh", "-c", "echo 'app starting...' && sleep 2 && exit 1"]
```
- `apiVersion: v1` — the Kubernetes API version to use
- `kind: Pod` — the type of Kubernetes object we are creating
- `metadata.name: broken-pod` — the name of the pod
- `metadata.namespace: default` — which namespace to create it in
- `spec.containers` — list of containers in this pod
- `image: nginx:alpine` — use the nginx image (a small web server) as the base
- `command: [...]` — override the default command with this script:
  - Print "app starting..."
  - Wait 2 seconds
  - Exit with code 1 (failure!)
- This creates a pod that always crashes, putting it in `CrashLoopBackOff` state

### File: `module-3/mcp_server.py` — Line by Line

```python
"""
MCP Server for Kubernetes Tools — exposes K8s tools to Claude Desktop via MCP.
Run: python3 module-3/mcp_server.py
"""

import subprocess
from fastmcp import FastMCP

mcp = FastMCP("Kubernetes Tools")
```
- `FastMCP` — imports the FastMCP library
- `FastMCP("Kubernetes Tools")` — creates an MCP server named "Kubernetes Tools"

```python
@mcp.tool
def list_pods(namespace: str = "default") -> str:
    """List all pods in a Kubernetes namespace with their status."""
    result = subprocess.run(
        ["kubectl", "get", "pods", "-n", namespace],
        capture_output=True, text=True,
    )
    return result.stdout or result.stderr
```
- `@mcp.tool` — this registers the function as an MCP tool (vs. `@tool` for LangChain)
- Everything else is the same as the LangChain version

```python
if __name__ == "__main__":
    mcp.run()
```
- `if __name__ == "__main__":` — Python convention meaning "only run this code if this file is run directly, not imported"
- `mcp.run()` — starts the MCP server. It listens on stdio (standard input/output) for incoming tool calls from Claude Desktop or other MCP clients.

### File: `module-3/agent_with_mcp.py` — Line by Line

This file shows a different approach: instead of defining tools directly in the agent, you connect to an MCP server to get tools.

```python
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain.agents import create_agent
from langchain_ollama import ChatOllama
import asyncio
```
- `MultiServerMCPClient` — LangChain's adapter that connects to MCP servers
- `asyncio` — Python library for asynchronous (non-blocking) programming. MCP connections are async.

```python
async def main():
    # 1. Initialize the MCP Client (Do this OUTSIDE the loop to avoid reconnecting every time)
    client = MultiServerMCPClient(
        {
            "docker-mcp" : {
                "transport": "stdio",
                "command":"python",
                "args": ["mcp_server.py"]
            }
        }
    )
```
- `async def main():` — this is an asynchronous function (can pause and resume without blocking)
- `MultiServerMCPClient({...})` — connects to one or more MCP servers
- `"docker-mcp"` — a name for this server connection
- `"transport": "stdio"` — communicate via stdin/stdout
- `"command": "python", "args": ["mcp_server.py"]` — start the MCP server by running `python mcp_server.py`

```python
    tools = await client.get_tools()
```
- `await` — waits for the async operation to complete (get the list of tools from the MCP server)
- The tools are now LangChain-compatible objects, even though they came from an MCP server

```python
    llm = ChatOllama(model="gemma4", temperature=0.8)
    agent = create_agent(llm, tools)
```
Note: `temperature=0.8` here (slightly more creative than usual). This is a choice by the developer.

```python
    chat_history = []

    while True:
        user_input = input("\nUser: ")
        if user_input.lower() in ["exit", "quit", "bye"]:
            print("Goodbye!")
            break
        if not user_input.strip():
            continue

        chat_history.append({"role": "user", "content": user_input})
```
- `chat_history = []` — this agent maintains conversation history, unlike the previous modules
- Each user message is added to the history as a dictionary with `role` and `content`

```python
        try:
            response = await agent.ainvoke({"messages": chat_history})
            agent_message = response['messages'][-1]
            print(f"\nAgent: {agent_message.content}")
            chat_history.append(agent_message)
        except Exception as e:
            print(f"\nAn error occurred: {e}")
```
- `await agent.ainvoke(...)` — async version of `agent.invoke()`
- The entire `chat_history` is passed each time, so the agent knows the full conversation context
- The agent's response is also added to history, so future questions have context

```python
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nSession ended by user.")
```
- `asyncio.run(main())` — runs the async `main()` function
- `KeyboardInterrupt` — caught when user presses Ctrl+C

### How to Run Module 3

```bash
# Create a Kind cluster
kind create cluster --name devops-demo

# Deploy the broken pod
kubectl apply -f module-3/broken_pod.yaml

# Wait for it to crash
kubectl get pods    # Should show broken-pod in CrashLoopBackOff

# Create a broken Docker container too
docker run -d --name broken-container nginx:alpine sh -c "echo 'starting...' && sleep 2 && exit 1"

# Run the agent
python3 module-3/agent.py

# Test queries:
# > What pods are running in my cluster?
# > Why is broken-pod crashing?
# > What Docker containers are running?
# > What's broken across Docker and Kubernetes?

# Clean up
kubectl delete -f module-3/broken_pod.yaml
docker rm -f broken-container
kind delete cluster --name devops-demo
```

---

## 8. Module 4 — AIOps Demystified (Theory)

### What this module does
This is a **theory module** with no code files. It explains the real-world context around AI agents in operations before you build the production-grade KubeHealer in Module 5.

### Key Concepts Covered

#### The Alert Fatigue Problem
- Engineering teams get **4,484 alerts/day** on average (Vectra 2023 report)
- Teams respond to less than **5%** of alerts
- Real incidents get buried; MTTR (Mean Time to Recovery) goes up
- On-call engineers burn out

**AIOps = using AI to triage, correlate, and act on alerts** so humans only handle what matters.

#### Real Companies Building AIOps

| Company | What They Do | Key Numbers |
|---------|-------------|-------------|
| NeuBird | AI agents for SRE, scan and fix alerts | 1M+ alerts resolved, 90% MTTR reduction |
| Komodor | Kubernetes troubleshooting, "Klaudia" agent | 80% faster MTTR (Cisco), 70% reduction (Lacework) |
| k8sgpt | Open source CLI that explains K8s issues | Apache-2.0, CNCF sandbox |

#### The AWS Kiro Incident — Why Guardrails Matter
In December 2025, Amazon's AI agent "Kiro" caused a **13-hour AWS outage**:
1. A human gave Kiro elevated permissions (bypassing normal two-human sign-off)
2. Kiro "decided" to delete and recreate a production environment
3. 13 hours of downtime

**Lessons:** Agents need:
1. **Explicit tool list** — only call functions YOU define
2. **Safe actions only** — restart, scale, adjust. Never delete, destroy.
3. **Scoped permissions** — specific namespaces, not cluster-wide
4. **Audit trail** — log every decision and action

#### The Durability Problem and Temporal
Naive Python script:
```python
diagnosis = call_llm("Why is this pod crashing?")  # LLM returns "increase memory"
apply_fix(diagnosis)  # ← crash happens here. Fix never applied.
# Script restarts. No memory. Starts from scratch.
```

Temporal solution:
- Records every step
- If worker crashes after diagnosis but before fix: Temporal knows the diagnosis is done, replays it from cache, continues from `apply_fix`
- No re-diagnosis, no lost state, no duplicate actions

| Failure | Try/Except | Temporal |
|---------|-----------|----------|
| API returns error | Catches it | Retries automatically |
| LLM times out | Catches it | Retries with backoff |
| Worker process crashes | Lost everything | Resumes from last checkpoint |
| Network partition | Depends | Retries when network recovers |
| Partial completion | No tracking | Knows what finished, resumes the rest |

---

## 9. Module 5 — KubeHealer (Self-Healing System)

### What this module does
KubeHealer is the **flagship project**. It is in a **separate repository** (https://github.com/TrainWithShubham/kubehealer) — this module's README explains how to set it up.

### Architecture

```
CLI (you type questions here)
  |
  v
Temporal Workflow (ConversationWorkflow)
  |
  +-- Activity: call_claude        → sends message to Claude AI
  +-- Activity: list_pods          → calls kubectl
  +-- Activity: get_pod_details    → calls kubectl describe
  +-- Activity: get_pod_logs       → calls kubectl logs
  +-- Activity: call_claude        → Claude sees tool results, responds
  +-- Activity: scan_cluster       → finds all broken pods
  +-- Activity: diagnose_pod       → AI diagnosis of each pod
  +-- Activity: execute_fix        → applies the safe fix
  |
  v
Kubernetes API (applies the actual changes)
```

Every box is a **Temporal Activity** — individually retryable, observable in the UI, with its own timeout.

### What Breaks and How KubeHealer Fixes It

| App | Problem | AI Diagnosis | Auto-Fix |
|-----|---------|-------------|---------|
| web-app | Image "nginx:latestt" (typo) | Detects typo in image name | Patches to nginx:latest |
| memory-hog | 10Mi memory limit + stress test | OOMKilled | Patches to 256Mi |
| config-app | Missing ConfigMap | Cannot auto-fix | Skips with explanation |

### Key Demo: Crash Recovery

1. Start healing: `you> heal my cluster`
2. Kill the worker: `Ctrl+C` in the worker terminal
3. Open Temporal UI at `http://localhost:8233` — workflow shows "Running" with some activities done
4. Restart worker: `python worker.py`
5. The workflow **resumes from where it stopped** — completed activities are NOT repeated

### Guardrails in KubeHealer
Only 4 possible actions (enforced by code):
- `restart_pod`
- `fix_image`
- `patch_resources`
- `skip` (when a fix requires human intervention)

No arbitrary kubectl commands. No delete. No destroy. Human approval required before execution.

### Tech Stack for Module 5

| Component | Role |
|-----------|------|
| Temporal | Durable workflow orchestration |
| Claude Sonnet 4 | LLM for diagnosis and conversation |
| Kubernetes | Target environment |
| Kind | Local K8s cluster |
| Python 3.11+ | Everything glued together |

### How to Run Module 5

```bash
# Terminal 1: Setup cluster
git clone https://github.com/TrainWithShubham/kubehealer.git
cd kubehealer
pip install -r requirements.txt
cp .env.example .env
# Edit .env and add your Anthropic API key
./setup.sh  # Creates Kind cluster, deploys 3 broken apps

# Terminal 2: Start Temporal
temporal server start-dev

# Terminal 3: Start worker
python worker.py

# Terminal 4: Start CLI
python cli.py

# In CLI:
# you> how many pods are running?
# you> what's wrong with web-app?
# you> heal my cluster
# you> approve all fixes
```

---

## 10. Module 6 — CI/CD Failure Analyzer

### What this module does
Applies the same agent pattern to a new domain: **GitHub Actions CI/CD failures**. Instead of Docker and Kubernetes tools, the tools call the `gh` (GitHub CLI).

### File: `module-6/ci_analyzer.py` — Line by Line

```python
"""
CI/CD Failure Analyzer -- diagnoses GitHub Actions failures.
Run: python3 module-6/ci_analyzer.py
Requires: gh CLI authenticated (gh auth login)
"""

import subprocess
from langchain_ollama import ChatOllama
from langchain_core.tools import tool
from langchain.agents import create_agent as create_react_agent
```
Identical imports to Module 2/3, except there are no Kubernetes-specific imports.

#### Tool 1: list_workflow_runs

```python
@tool
def list_workflow_runs(status: str = "failure") -> str:
    """List recent GitHub Actions workflow runs. Use status='failure' for failed runs."""
    result = subprocess.run(
        ["gh", "run", "list", "--status", status, "--limit", "5"],
        capture_output=True, text=True,
    )
    return result.stdout or result.stderr
```
- `gh run list --status failure --limit 5` — lists the 5 most recent failed GitHub Actions runs
- The LLM can call this with `status="success"` or `status="failure"`

#### Tool 2: get_failed_logs

```python
@tool
def get_failed_logs(run_id: str) -> str:
    """Get the failed step logs from a GitHub Actions run. Pass the run ID."""
    result = subprocess.run(
        ["gh", "run", "view", run_id, "--log-failed"],
        capture_output=True, text=True,
    )
    output = result.stdout + result.stderr
    # Truncate if too long (LLMs have token limits)
    if len(output) > 5000:
        output = output[:5000] + "\n\n[...truncated, showing first 5000 chars]"
    return output
```
- `gh run view <id> --log-failed` — gets only the logs from steps that failed
- **Token limit handling:** if the output is more than 5000 characters, it is truncated with a note. This is important because sending too much text to an LLM can exceed its token limit or make responses slow and expensive.
- `output[:5000]` — Python slice notation, gets the first 5000 characters

#### Tool 3: get_workflow_file

```python
@tool
def get_workflow_file(workflow_name: str) -> str:
    """Read a GitHub Actions workflow YAML file. Pass the filename like 'ci.yml'."""
    import pathlib
    path = pathlib.Path(f".github/workflows/{workflow_name}")
    if path.exists():
        return path.read_text()
    return f"File not found: {path}"
```
- `import pathlib` — importing inside the function (unusual but valid Python)
- `pathlib.Path(...)` — creates a path object
- `path.exists()` — checks if the file exists
- `path.read_text()` — reads the file content as a string
- If not found, returns a helpful error message

#### Agent Setup and Loop

```python
llm = ChatOllama(model="gemma4", temperature=0)
tools = [list_workflow_runs, get_failed_logs, get_workflow_file]
agent = create_react_agent(llm, tools)

print("\nCI/CD Failure Analyzer")
print("-" * 40)
print("I analyze GitHub Actions failures.")
print("Run this inside a git repo with GitHub Actions.")
print("Type 'quit' to exit.\n")

while True:
    question = input("> ").strip()
    if question.lower() in ("quit", "exit", "q"):
        break
    if not question:
        continue

    print("\nThinking...\n")
    result = agent.invoke({"messages": [("user", question)]})
    print(result["messages"][-1].content)
    print()
```
Identical structure to Module 2/3. The only difference is the tools — the agent pattern never changes.

### How to Run Module 6

```bash
# Step 1: Authenticate with GitHub
gh auth login

# Step 2: Navigate to a repo with GitHub Actions
cd ~/your-project-with-ci

# Step 3: Run the analyzer
python3 /path/to/module-6/ci_analyzer.py

# Ask questions:
# > Show me recent failed runs
# > What went wrong in the last failure?
# > Read the CI workflow file and check for issues
```

---

## 11. How Each Module Builds on the Previous

```
Module 0: Setup
  ↓ verifies tools installed
Module 1: LLM Call (no tools, no agent)
  ↓ adds tool calling + agent loop
Module 2: Agent with Docker tools (3 tools)
  ↓ adds Kubernetes tools + MCP protocol
Module 3: Agent with Docker + K8s tools (6 tools) + MCP server
  ↓ adds production concepts: guardrails, durability
Module 4: Theory (no code)
  ↓ applies durability (Temporal) + Claude + K8s fixes
Module 5: KubeHealer (full production system)
  ↓ same agent pattern, new domain (CI/CD)
Module 6: CI/CD Failure Analyzer
```

### What Each Module Adds

| Module | New Concept | New Code | New Tools |
|--------|------------|---------|----------|
| Module 0 | Environment setup | verify_setup.py | None (just checks) |
| Module 1 | LLM call, system prompt, temperature | explainer.py | ollama.chat() |
| Module 2 | Agent, tool calling, ReAct loop | agent.py | list_containers, get_logs, inspect_container |
| Module 3 | Multi-domain, MCP protocol | agent.py, mcp_server.py, broken_pod.yaml | list_pods, describe_pod, get_events |
| Module 4 | Guardrails, durability, AIOps landscape | (no code) | (conceptual) |
| Module 5 | Temporal workflows, Claude API, crash recovery | (separate repo) | All K8s tools + Temporal activities |
| Module 6 | New domain application | ci_analyzer.py | list_workflow_runs, get_failed_logs, get_workflow_file |

---

## 12. How to Run Every Module Step by Step

### Complete Setup (Do Once)

```bash
# 1. Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# 2. Download the LLM model
ollama pull gemma4

# 3. Clone the repo
git clone https://github.com/trainwithshubham/agentic-ai-for-devops.git
cd agentic-ai-for-devops

# 4. Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 5. Install Python packages
pip install -r requirements.txt

# 6. Verify everything works
python3 module-0/verify_setup.py
```

### Run Module 1

```bash
source .venv/bin/activate
python3 module-1/explainer.py
# Paste any Docker error, press Enter twice
```

### Run Module 2

```bash
source .venv/bin/activate

# Create test container
docker run -d --name broken-app nginx:alpine sh -c "echo 'app starting...' && sleep 2 && exit 1"

# Run agent
python3 module-2/agent.py

# Type: Why is broken-app crashing?

# Cleanup
docker rm -f broken-app
```

### Run Module 3

```bash
source .venv/bin/activate

# Create Kubernetes cluster
kind create cluster --name devops-demo
kubectl apply -f module-3/broken_pod.yaml

# Create broken Docker container
docker run -d --name broken-container nginx:alpine sh -c "echo 'starting...' && sleep 2 && exit 1"

# Run agent (Docker + K8s)
python3 module-3/agent.py

# Cleanup
kubectl delete -f module-3/broken_pod.yaml
docker rm -f broken-container
kind delete cluster --name devops-demo
```

### Run Module 5 (KubeHealer)

```bash
# Install Temporal CLI
curl -sSf https://temporal.download/cli.sh | sh

# Clone KubeHealer
git clone https://github.com/TrainWithShubham/kubehealer.git
cd kubehealer
pip install -r requirements.txt
cp .env.example .env   # Add your Anthropic API key in .env

# Terminal 1
./setup.sh

# Terminal 2
temporal server start-dev

# Terminal 3
python worker.py

# Terminal 4
python cli.py
```

### Run Module 6

```bash
gh auth login
cd ~/your-github-project-with-ci
source .venv/bin/activate
python3 /path/to/agentic-ai-for-devops/module-6/ci_analyzer.py
```

---

## 13. What the Output Looks Like

### Module 0 Output
```
Checking your setup...

  [PASS] Python 3.10+
  [PASS] Docker
  [PASS] kubectl
  [PASS] Kind
  [PASS] Ollama + gemma4

————————————————————————————————————————
  5/5 — you're ready for Day 1!
```

### Module 1 Output
```
Paste your Docker error (press Enter twice when done):

docker: Error response from daemon: Bind for 0.0.0.0:3000 failed: port is already allocated.

Thinking...

What went wrong: Docker tried to bind port 3000, but it's already in use.

Most likely cause: Another container or process is using port 3000.

How to fix it:
  Check what's using the port: sudo lsof -i :3000
  Kill it: kill -9 <PID>
  Or use a different port: docker run -p 3001:3000 your-image
```

### Module 2 Output
```
Docker Troubleshooter Agent
------------------------------
Ask me about your Docker containers. Type 'quit' to exit.

> Why is broken-app crashing?

Thinking...

I'll check the containers first, then look at the logs.

[Calling list_containers...]
[Calling get_logs for broken-app...]

broken-app is crashing because its startup command explicitly exits with code 1.
The command runs: echo 'app starting...', waits 2 seconds, then exits with failure code 1.
This is not a real application error — the exit is intentional in the script.

To fix this, replace the command with one that runs continuously (like a real service).
```

### Module 3 Output (Multi-domain)
```
Multi-Tool DevOps Agent
----------------------------------------
I can troubleshoot Docker and Kubernetes.

> What's broken across Docker and Kubernetes?

Thinking...

[Calling list_containers...]
[Calling list_pods...]
[Calling get_logs for broken-container...]
[Calling describe_pod for broken-pod...]

Issues found:

Docker:
- broken-container: Exiting with code 1 immediately after startup. Command intentionally fails.

Kubernetes:
- broken-pod: In CrashLoopBackOff state. The pod's command exits with code 1 after 2 seconds.
  Events show: "Back-off restarting failed container" repeated multiple times.
```

### Module 5 Output (KubeHealer)
```
you> heal my cluster

[Scanning cluster for broken pods...]
[Diagnosing web-app...]
[Diagnosing memory-hog...]
[Diagnosing config-app...]

Diagnosis Complete:

1. web-app — CRITICAL
   Root cause: Image typo "nginx:latestt" — image does not exist
   Proposed fix: Patch image to "nginx:latest"

2. memory-hog — HIGH
   Root cause: OOMKilled — memory limit (10Mi) too low for stress test
   Proposed fix: Patch memory limit to 256Mi

3. config-app — MEDIUM
   Root cause: Missing ConfigMap "app-config"
   Proposed fix: Cannot auto-fix — create ConfigMap manually

Shall I apply fixes for web-app and memory-hog?

you> approve all fixes

[Patching web-app image...]  ✓
[Patching memory-hog resources...]  ✓
[Skipping config-app — needs manual ConfigMap]

2 pods fixed. 1 requires manual intervention.
```

---

## 14. Comparison Tables

### Chatbot vs Agent

| Feature | Chatbot (Module 1) | Agent (Module 2+) |
|---------|-------------------|-------------------|
| Input | Text from user | Text from user |
| Processing | LLM generates text | LLM decides which tools to call |
| Output | Text answer | Actions taken + text answer |
| Can run commands | No | Yes |
| Can inspect real systems | No | Yes |
| Loop | No (single call) | Yes (ReAct loop until done) |
| Example | "Explain this error" | "Diagnose and fix this container" |

### LangChain Tool vs MCP Tool

| Feature | LangChain `@tool` | FastMCP `@mcp.tool` |
|---------|------------------|---------------------|
| Decorator | `@tool` | `@mcp.tool` |
| Works with | LangChain agents only | Any MCP-compatible AI system |
| Clients | LangChain, LangGraph | Claude Desktop, VS Code, Cursor, etc. |
| Runtime | In-process (same Python script) | Background server process (stdio) |
| Config needed | No | Claude Desktop JSON config |
| Write once use everywhere | No | Yes |

### Module Evolution

| Module | Tools | LLM | Infrastructure | New Pattern |
|--------|-------|-----|---------------|------------|
| Module 1 | 0 (no tools) | Ollama/gemma4 | None | First LLM call |
| Module 2 | 3 (Docker) | Ollama/gemma4 | Docker | Tool calling + ReAct |
| Module 3 | 6 (Docker + K8s) | Ollama/gemma4 | Docker + K8s | Multi-domain + MCP |
| Module 4 | — (theory) | — | — | Guardrails + Durability |
| Module 5 | All K8s | Claude Sonnet | K8s + Temporal | Durable workflows |
| Module 6 | 3 (GitHub CLI) | Ollama/gemma4 | GitHub | New domain application |

### Different Ways to Call an LLM

| Method | Library | When to Use |
|--------|---------|-------------|
| `ollama.chat()` | `ollama` | Simple one-shot calls, no agent needed |
| `ChatOllama` + `create_react_agent` | `langchain`, `langchain-ollama` | Agents with tools, local LLM |
| `ChatAnthropic` + `create_react_agent` | `langchain`, `langchain-anthropic` | Agents with tools, Claude (cloud) |
| Temporal Activities | `temporalio` | Durable agents that survive crashes |
| MCP Server | `fastmcp` | Protocol-based tools usable from any AI client |

### Ollama vs Claude

| Feature | Ollama (gemma4) | Claude (Anthropic) |
|---------|----------------|-------------------|
| Cost | Free (runs locally) | Paid API (per token) |
| Privacy | 100% local, no data sent | Data sent to Anthropic |
| Speed | Depends on your hardware | Fast (cloud servers) |
| Quality | Good for basic tasks | Better for complex reasoning |
| Setup | `ollama pull gemma4` | Requires API key from console.anthropic.com |
| Used in | Modules 1–3, 6 | Module 5 (KubeHealer) |

---

## 15. Cheat Sheet

### Python Concepts Used

```python
# Import a module
import subprocess
from langchain_ollama import ChatOllama

# Function definition with type hints
def my_function(param: str) -> str:
    return "result"

# Decorator
@tool
def my_tool() -> str:
    """Description the LLM reads."""
    pass

# Subprocess (run a shell command)
result = subprocess.run(["docker", "ps", "-a"], capture_output=True, text=True)
print(result.stdout)   # standard output
print(result.stderr)   # error output

# f-string (formatted string)
name = "world"
print(f"Hello {name}")  # → Hello world

# List
items = []
items.append("new item")
last_item = items[-1]   # last element

# While loop with break
while True:
    line = input()
    if line == "":
        break

# Try/except
try:
    result = subprocess.run(["docker", "info"], check=True)
except Exception:
    print("Docker not running")

# String operations
text = "hello world"
text.strip()         # remove whitespace
text.lower()         # to lowercase
text[:100]           # first 100 characters
"hello" in text      # check if substring exists

# None check
if shutil.which("docker"):    # installed
    pass
if not shutil.which("kind"):  # not installed
    pass
```

### LangChain Cheat Sheet

```python
# Create LLM
from langchain_ollama import ChatOllama
llm = ChatOllama(model="gemma4", temperature=0)

# Define a tool
from langchain_core.tools import tool

@tool
def my_tool(input: str) -> str:
    """What this tool does — the LLM reads this."""
    return "result"

# Create agent
from langchain.agents import create_agent
agent = create_agent(llm, [my_tool])

# Run agent
result = agent.invoke({"messages": [("user", "question here")]})
print(result["messages"][-1].content)
```

### MCP Cheat Sheet

```python
# Create MCP server
from fastmcp import FastMCP
mcp = FastMCP("My Server Name")

# Define an MCP tool
@mcp.tool
def my_tool(param: str) -> str:
    """Description."""
    return "result"

# Start the server
if __name__ == "__main__":
    mcp.run()
```

### Docker Commands Used in This Course

```bash
docker ps -a                          # list all containers
docker logs --tail 50 <name>          # get last 50 log lines
docker inspect <name>                 # detailed container info
docker run -d --name <n> <image> <cmd> # run container in background
docker rm -f <name>                   # force remove container
```

### Kubernetes Commands Used in This Course

```bash
kubectl get pods -n default           # list pods in namespace
kubectl describe pod <name>           # detailed pod info + events
kubectl get events --sort-by=.lastTimestamp  # recent events
kubectl apply -f <file.yaml>          # create resource from YAML
kubectl delete -f <file.yaml>         # delete resource from YAML
kubectl config get-contexts           # list available clusters
kubectl config use-context <name>     # switch cluster
kind create cluster --name <n>        # create local cluster
kind delete cluster --name <n>        # delete local cluster
kind export kubeconfig --name <n>     # set up kubectl for kind cluster
```

### GitHub CLI Commands Used in This Course

```bash
gh auth login                         # authenticate
gh run list --status failure --limit 5 # list recent failed runs
gh run view <id> --log-failed         # get failure logs
```

### Common Error Fixes

| Error | Fix |
|-------|-----|
| `Ollama not running` | Run `ollama serve` |
| `Docker permission denied` | `sudo usermod -aG docker $USER` then re-login |
| `kubectl wrong cluster` | `kubectl config use-context kind-devops-demo` |
| `MCP server disconnected` | Use venv Python path in config, not system python3 |
| `gemma4 not found` | `ollama pull gemma4` |
| `ModuleNotFoundError` | `pip install -r requirements.txt` |

---

## 16. Different Ways to Do the Same Thing

### Way 1: Direct LLM Call (Module 1)
```python
import ollama
response = ollama.chat(model="gemma4", messages=[
    {"role": "system", "content": "You are a Docker expert."},
    {"role": "user", "content": error_text},
])
print(response["message"]["content"])
```
**Best for:** Simple Q&A, explaining errors, one-shot tasks. No tools needed.

### Way 2: LangChain Agent with Tools (Modules 2, 3, 6)
```python
from langchain_ollama import ChatOllama
from langchain_core.tools import tool
from langchain.agents import create_react_agent

@tool
def my_tool() -> str:
    """Description."""
    return subprocess.run(["some", "command"], capture_output=True, text=True).stdout

llm = ChatOllama(model="gemma4", temperature=0)
agent = create_react_agent(llm, [my_tool])
result = agent.invoke({"messages": [("user", "your question")]})
```
**Best for:** Agents that need to inspect real systems and make decisions.

### Way 3: MCP Server (Module 3)
```python
from fastmcp import FastMCP
mcp = FastMCP("My Tools")

@mcp.tool
def my_tool() -> str:
    """Description."""
    return subprocess.run(["some", "command"], capture_output=True, text=True).stdout

mcp.run()
```
**Best for:** Tools you want to use from Claude Desktop, VS Code, or multiple AI systems.

### Way 4: LangChain + MCP Client (Module 3 agent_with_mcp.py)
```python
from langchain_mcp_adapters.client import MultiServerMCPClient

client = MultiServerMCPClient({"my-server": {"transport": "stdio", "command": "python", "args": ["mcp_server.py"]}})
tools = await client.get_tools()
agent = create_agent(llm, tools)
```
**Best for:** Using MCP tools inside a LangChain agent (bridges both worlds).

### Way 5: Temporal + Claude (Module 5)
```python
# Activities are individual steps
@activity.defn
async def call_claude(messages) -> str:
    client = Anthropic()
    response = client.messages.create(model="claude-sonnet-4-6", ...)
    return response

# Workflows orchestrate activities
@workflow.defn
class HealingWorkflow:
    @workflow.run
    async def run(self):
        pods = await workflow.execute_activity(scan_cluster, ...)
        diagnosis = await workflow.execute_activity(diagnose_pod, ...)
        await workflow.execute_activity(execute_fix, ...)
```
**Best for:** Production-grade agents that must survive crashes and need audit trails.

---

## 17. Summary

This course teaches you to build AI agents for DevOps in 6 modules:

**Day 1 — Foundations:**
- **Module 0:** Verify your environment (Python, Docker, kubectl, Kind, Ollama)
- **Module 1:** Make your first LLM call — paste a Docker error, get a plain-English fix. Uses `ollama.chat()` directly.
- **Module 2:** Build your first AI agent — 3 Docker tools, ReAct loop via LangChain. The agent runs real `docker` commands.
- **Module 3:** Add Kubernetes tools (6 total), introduce MCP protocol so the same tools work with Claude Desktop.

**Day 2 — Production:**
- **Module 4:** Understand the real-world context — alert fatigue, AIOps companies, the Kiro incident (why guardrails matter), and Temporal (why durability matters).
- **Module 5:** KubeHealer — the flagship project. Self-healing Kubernetes agent using Claude + Temporal. Survives crashes, has audit trails, uses guardrails.
- **Module 6:** Apply the pattern to CI/CD — the same 3-line agent recipe works with GitHub Actions failures.

### The Repeating Pattern

Every agent in this course follows the same structure:

```python
# 1. Define tools the LLM can call
@tool
def my_tool(param: str) -> str:
    """What this tool does (LLM reads this)."""
    return subprocess.run([...], capture_output=True, text=True).stdout

# 2. Create the agent
llm = ChatOllama(model="gemma4", temperature=0)
agent = create_react_agent(llm, [my_tool])

# 3. Run in a loop
while True:
    question = input("> ")
    result = agent.invoke({"messages": [("user", question)]})
    print(result["messages"][-1].content)
```

Change the tools → change the domain. Docker, Kubernetes, CI/CD, AWS, anything.

---

## 18. Conclusion

### What You Built

Starting from zero AI experience, the course takes you through a progressive journey:

1. A simple LLM call that explains Docker errors
2. An AI agent that runs Docker commands itself
3. A multi-environment agent (Docker + Kubernetes) with MCP support
4. The AIOps landscape and production concerns
5. KubeHealer — a self-healing Kubernetes system with crash recovery and audit trails
6. A CI/CD failure analyzer using the same pattern in a new domain

### The Key Insight

The fundamental pattern never changes:
- **Define tools** (Python functions that run commands)
- **Wire them to an LLM** (via LangChain or MCP)
- **Let the agent decide** which tools to call based on the question

What changes between modules is: the domain (Docker → K8s → CI/CD), the LLM (Ollama → Claude), and the execution model (simple script → Temporal workflow).

### What Makes an Agent "Production-Ready"

| Concern | Solution Used |
|---------|--------------|
| Crash recovery | Temporal durable workflows |
| Safe operations | Restricted tool list (no delete/destroy) |
| Human oversight | Approval required before fixes |
| Audit trail | Temporal workflow history |
| Token limits | Truncation in CI analyzer (5000 char limit) |
| Local credentials | MCP server runs on your machine |
| Framework independence | MCP protocol (write once, use anywhere) |

### Where to Go Next

1. **Add more tools** — any shell command can become a tool. AWS CLI, Prometheus metrics, PagerDuty API.
2. **Switch to Claude** — replace `ChatOllama` with `ChatAnthropic` for better reasoning.
3. **Add Temporal** — wrap any agent in Temporal activities for durability.
4. **Add MCP** — expose your tools as an MCP server to use them from Claude Desktop.
5. **Build your own AIOps agent** — the pattern is always: tools + LLM + agent loop.

The course motto: **"Change the tools, change the domain."** You now know the pattern.

---

*This document covers all 6 modules of the Agentic AI for DevOps course, every code file, every concept, and every command needed to run the project end to end.*
