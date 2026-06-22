# Amazon Bedrock AgentCore — Complete End-to-End Explanation

> **Who this is for:** Complete beginners who want to understand Amazon Bedrock AgentCore — what it is, why it exists, what every component does, and how to build and deploy production AI agents using it, end to end.

---

## Table of Contents

1. [What is Amazon Bedrock AgentCore?](#1-what-is-amazon-bedrock-agentcore)
2. [Why AgentCore Exists — The Problem It Solves](#2-why-agentcore-exists)
3. [The Full Architecture Map](#3-the-full-architecture-map)
4. [Component 1 — Runtime (Harness)](#4-component-1-runtime-harness)
5. [Component 2 — Gateway](#5-component-2-gateway)
6. [Component 3 — Memory](#6-component-3-memory)
7. [Component 4 — Identity and Auth](#7-component-4-identity-and-auth)
8. [Component 5 — Code Interpreter](#8-component-5-code-interpreter)
9. [Component 6 — Browser Tool](#9-component-6-browser-tool)
10. [Component 7 — Observability](#10-component-7-observability)
11. [Component 8 — Evaluation](#11-component-8-evaluation)
12. [Component 9 — Policy (Cedar)](#12-component-9-policy)
13. [Component 10 — Agent Registry](#13-component-10-agent-registry)
14. [Framework Support — Strands, LangGraph, CrewAI, OpenAI](#14-framework-support)
15. [The AgentCore CLI — Developer Workflow](#15-the-agentcore-cli)
16. [Repository Structure Walkthrough](#16-repository-structure)
17. [End-to-End Example 1 — Customer Support Agent](#17-e2e-example-1)
18. [End-to-End Example 2 — Harness (Low-Level API)](#18-e2e-example-2)
19. [Blueprints — Production Reference Applications](#19-blueprints)
20. [Infrastructure as Code (CDK / CloudFormation / Terraform)](#20-infrastructure-as-code)
21. [Workshops — Learning Paths](#21-workshops)
22. [Request Lifecycle — A to Z](#22-request-lifecycle)
23. [Common Patterns and Anti-Patterns](#23-patterns)
24. [Cheatsheet](#24-cheatsheet)
25. [Summary and Conclusion](#25-summary)

---

## 1. What is Amazon Bedrock AgentCore?

### The One-Line Definition

**Amazon Bedrock AgentCore is AWS's managed platform for deploying and operating AI agents at scale — supporting any framework (LangGraph, CrewAI, Strands, OpenAI) and any model (Claude, Gemini, GPT, Llama).**

### The Analogy

Think of it like AWS EC2 but for AI agents:

```
BEFORE EC2:
  You manage your own servers
  You handle networking, security, scaling, monitoring
  Every team builds the same infrastructure from scratch

AFTER EC2:
  AWS manages the servers
  You just upload your code and it runs
  Pay for what you use, scales automatically

BEFORE AgentCore:
  You build your own agent runtime
  You manage tool connections, auth tokens, memory stores, traces
  Every agent team builds the same infrastructure independently

AFTER AgentCore:
  AWS manages the agent infrastructure
  You just write your agent logic
  Memory, auth, observability, policy — all managed for you
```

### What AgentCore Is NOT

- It is **not** an agent framework (you bring your own: LangGraph, CrewAI, Strands, etc.)
- It is **not** a model provider (you bring your own: Claude via Bedrock, OpenAI, Gemini, etc.)
- It is **not** just a hosting service — it's a full agent operations platform

### What AgentCore IS

It is the **infrastructure layer** that sits between your agent code and the cloud:

```
┌──────────────────────────────────────────────────────────┐
│                YOUR AGENT CODE                           │
│  (Strands / LangGraph / CrewAI / OpenAI Agents SDK)      │
└──────────────────────────┬───────────────────────────────┘
                           │ wraps with
┌──────────────────────────▼───────────────────────────────┐
│               AGENTCORE PLATFORM                         │
│                                                          │
│  Runtime    Gateway    Memory    Identity    Policy       │
│  (hosting)  (tools)    (memory)  (auth)     (guardrails) │
│                                                          │
│  Code Interpreter   Browser    Observability   Evaluations│
│  (safe code exec)  (web)       (traces/metrics) (quality)│
└──────────────────────────┬───────────────────────────────┘
                           │ runs on
┌──────────────────────────▼───────────────────────────────┐
│                    AWS CLOUD                             │
│  Lambda / ECS / Fargate / CloudWatch / S3 / IAM / VPC   │
└──────────────────────────────────────────────────────────┘
```

---

## 2. Why AgentCore Exists — The Problem It Solves

### The Problem Without AgentCore

When companies try to deploy AI agents, they hit the same 7 problems every time:

```
PROBLEM 1: HOW DO I RUN THIS?
  → Build a FastAPI server
  → Dockerize it
  → Set up ECS or Lambda
  → Configure networking
  → Handle scaling
  → 2-4 weeks of work per agent

PROBLEM 2: HOW DO MY AGENTS USE TOOLS?
  → Each team builds their own tool integration
  → No standard protocol
  → Auth tokens stored in every agent
  → Security team can't audit centrally
  → Same bug fixed in 10 places

PROBLEM 3: HOW DO AGENTS REMEMBER THINGS?
  → Build your own vector database
  → Build your own session management
  → Handle conversation history
  → Different solution per team

PROBLEM 4: HOW DO I AUTHENTICATE USERS?
  → Every agent has its own auth logic
  → API keys scattered everywhere
  → No single view of who called what

PROBLEM 5: HOW DO I KNOW IF IT'S WORKING?
  → Build custom logging
  → Set up metrics
  → Configure tracing
  → No standard evaluation

PROBLEM 6: HOW DO I CONTROL WHAT AGENTS CAN DO?
  → Hard-code limits in agent logic
  → Can't update rules without redeploying
  → No centralized governance

PROBLEM 7: HOW DO I SAFELY RUN CODE THE AGENT GENERATES?
  → Run code in your production environment (dangerous!)
  → Build your own sandboxing system
  → Handle timeouts, isolation, security
```

### How AgentCore Solves Each Problem

```
PROBLEM 1 → AgentCore Runtime
  Deploy in minutes with `agentcore deploy`
  Serverless, scales to zero, auto-scales under load

PROBLEM 2 → AgentCore Gateway
  One MCP endpoint, centralized tool catalog
  All agents use one URL, auth managed centrally

PROBLEM 3 → AgentCore Memory
  Managed short-term + long-term memory
  SEMANTIC, SUMMARIZATION, USER_PREFERENCE, EPISODIC strategies
  `agentcore add memory` command

PROBLEM 4 → AgentCore Identity
  JWT-based inbound auth
  OAuth 2.0 outbound auth (2LO and 3LO)
  Supports Cognito, Okta, Entra ID, Auth0, PingFederate

PROBLEM 5 → AgentCore Observability + Evaluation
  Auto-instrumented OpenTelemetry traces
  Built-in LLM-as-judge evaluators
  CloudWatch integration, online evaluation

PROBLEM 6 → AgentCore Policy
  Cedar-based deterministic policy enforcement
  Update policies without redeploying code
  Centralized governance across all agents

PROBLEM 7 → AgentCore Code Interpreter
  Fully isolated Python sandbox (microVM per session)
  Safe, secure, ephemeral execution environment
```

---

## 3. The Full Architecture Map

```
┌─────────────────────────────────────────────────────────────────────────┐
│                   AMAZON BEDROCK AGENTCORE                               │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  DEVELOPER EXPERIENCE                                            │    │
│  │  AgentCore CLI (`agentcore create/dev/deploy/invoke`)           │    │
│  │  AgentCore Python SDK  │  TypeScript SDK  │  boto3 API          │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                  │                                       │
│  ┌───────────────────────────────▼─────────────────────────────────┐    │
│  │  RUNTIME (Harness)                                               │    │
│  │  Serverless container hosting for agent code                     │    │
│  │  Supports: HTTP protocol (streaming SSE/WebSocket)               │    │
│  │  Frameworks: Strands │ LangGraph │ CrewAI │ OpenAI SDK │ Any     │    │
│  │  Models: Claude (Bedrock) │ GPT-4 │ Gemini │ Llama │ Any         │    │
│  └───────────────────────────────┬─────────────────────────────────┘    │
│                                  │                                       │
│  ┌───────────────────────────────▼─────────────────────────────────┐    │
│  │  CORE SERVICES (all managed by AWS)                              │    │
│  │                                                                  │    │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐    │    │
│  │  │ GATEWAY  │  │  MEMORY  │  │ IDENTITY │  │   POLICY     │    │    │
│  │  │ MCP hub  │  │ Short +  │  │ Inbound  │  │ Cedar rules  │    │    │
│  │  │ HTTP fwd │  │ Long term│  │ Outbound │  │ Real-time    │    │    │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────────┘    │    │
│  │                                                                  │    │
│  │  ┌──────────────────┐  ┌───────────────────────────────────┐    │    │
│  │  │   BUILT-IN TOOLS │  │   OBSERVABILITY + EVALUATION      │    │    │
│  │  │  Code Interpreter│  │   OpenTelemetry traces            │    │    │
│  │  │  Browser Tool    │  │   LLM-as-judge evaluators         │    │    │
│  │  └──────────────────┘  │   A/B testing optimization        │    │    │
│  │                         └───────────────────────────────────┘    │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                  │                                       │
│  ┌───────────────────────────────▼─────────────────────────────────┐    │
│  │  AWS INFRASTRUCTURE                                              │    │
│  │  CloudWatch │ IAM │ S3 │ Lambda │ VPC │ Secrets Manager │ ECR   │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Component 1 — Runtime (Harness)

### What It Is

The Runtime is where your agent **code lives and runs in production**. It is a serverless, containerized execution environment managed by AWS.

There are two interfaces:
- **AgentCore Runtime** — deploy full agent apps (the recommended path via CLI)
- **AgentCore Harness** — a lower-level API for ephemeral AI sessions with isolated microVMs

### The Harness Concept

The Harness is a unique innovation in AgentCore. Think of it as a "compute session for an AI agent":

```
Harness = An isolated microVM (tiny virtual machine) allocated per session

When you create a Harness:
  ✓ AWS allocates a fresh, isolated Linux microVM
  ✓ The VM has Python, a shell, a filesystem
  ✓ The VM has the AI model available (Claude, Gemini, etc.)
  ✓ You can run shell commands on it (ExecuteCommand)
  ✓ The AI can write files, read files, run code
  ✓ When done, the VM is destroyed (ephemeral)

Why this is powerful:
  ✓ Completely isolated per session (no cross-contamination)
  ✓ AI can actually DO things (write files, run programs)
  ✓ You can switch models in the SAME session (Haiku → Sonnet)
  ✓ Full shell access means the AI can truly work like a developer
```

### Harness Code Walkthrough (getting_started.py)

```python
import boto3
from utils.iam import create_harness_role, delete_harness_role
from utils.client import get_agentcore_control_client, get_agentcore_client

# Two clients:
# control = management plane (create/delete harnesses, IAM setup)
# client  = data plane (send messages, run commands)
control = get_agentcore_control_client()
client  = get_agentcore_client()

# STEP 1: Create an IAM execution role
# The Harness needs AWS permissions to call Bedrock, etc.
role_arn = create_harness_role()

# STEP 2: Create the Harness (provisions a microVM pool)
resp = control.create_harness(
    harnessName="MyHarness",
    executionRoleArn=role_arn,
)
harness_id  = resp["harness"]["harnessId"]
harness_arn = resp["harness"]["arn"]

# Wait for READY status (~30-60 seconds)
while True:
    status = control.get_harness(harnessId=harness_id)["harness"]["status"]
    if status == "READY":
        break
    time.sleep(5)

# STEP 3: Invoke the agent (streaming response)
session_id = str(uuid.uuid4())   # One session = one isolated VM

response = client.invoke_harness(
    harnessArn=harness_arn,
    runtimeSessionId=session_id,          # Same session = same VM state
    messages=[{
        "role": "user",
        "content": [{"text": "List 3 fun things to do in Seattle. Save to a Markdown file."}]
    }],
    model={"bedrockModelConfig": {"modelId": "global.anthropic.claude-haiku-4-5-20251001-v1:0"}},
)

# Stream the response event by event
for event in response["stream"]:
    if "contentBlockDelta" in event:
        delta = event["contentBlockDelta"].get("delta", {})
        if "text" in delta:
            print(delta["text"], end="", flush=True)

# STEP 4: Switch to a DIFFERENT model in the SAME session
# The session state (files written, history) persists!
response2 = client.invoke_harness(
    harnessArn=harness_arn,
    runtimeSessionId=session_id,           # ← SAME session
    messages=[{"role": "user", "content": [{"text": "Add a Sonnet prefix to the file."}]}],
    model={"bedrockModelConfig": {"modelId": "global.anthropic.claude-sonnet-4-6"}},  # ← different model
)

# STEP 5: Run shell commands DIRECTLY on the microVM
# This is unique to the Harness — you get real shell access!
def run_command(cmd: str):
    resp = client.invoke_agent_runtime_command(
        agentRuntimeArn=harness_arn,
        runtimeSessionId=session_id,
        body={"command": cmd},
    )
    for event in resp["stream"]:
        if "chunk" in event:
            chunk = event["chunk"]
            if "contentDelta" in chunk:
                if "stdout" in chunk["contentDelta"]:
                    print(chunk["contentDelta"]["stdout"], end="")

run_command("ls -la")                        # List files the agent created
run_command("cat seattle_activities.md")     # Read a file the agent wrote

# STEP 6: Cleanup
control.delete_harness(harnessId=harness_id)
```

### Runtime vs Harness — When to Use Which

| Use Case | Use Runtime (via CLI) | Use Harness (via API) |
|----------|----------------------|----------------------|
| Production agent API | ✓ | |
| Standard chatbot | ✓ | |
| Custom sandboxed AI session | | ✓ |
| Switch models mid-session | | ✓ |
| Shell access to agent VM | | ✓ |
| Multi-framework support | ✓ | ✓ |
| Fastest deployment | ✓ (CLI) | |

### Deploying with Runtime (the Standard Path)

```python
# agent.py — your agent code
from strands import Agent, tool
from bedrock_agentcore.runtime import BedrockAgentCoreApp

app = BedrockAgentCoreApp()

@tool
def weather(city: str) -> str:
    """Get the weather for a city."""
    return "sunny" if city == "Seattle" else "cloudy"

agent = Agent(
    model=BedrockModel(model_id="global.anthropic.claude-haiku-4-5-20251001-v1:0"),
    tools=[weather],
    system_prompt="You are a helpful assistant that knows about weather.",
)

# @app.entrypoint marks the function AgentCore will call when invoked
@app.entrypoint
async def invoke(payload, context):
    stream = agent.stream_async(payload.get("prompt"))
    async for event in stream:
        if "data" in event and isinstance(event["data"], str):
            yield event["data"]   # Streams back to caller

if __name__ == "__main__":
    app.run()   # Starts local dev server on :8080
```

```bash
# Deploy this to AWS:
agentcore deploy
agentcore invoke "What's the weather in Seattle?" --stream
```

---

## 5. Component 2 — Gateway

### What It Is

The Gateway is a **centralized MCP (Model Context Protocol) hub** that all your agents connect to for tools. Instead of every agent managing its own tool connections, the Gateway is one URL that gives access to every tool.

### The Problem Without Gateway

```
WITHOUT GATEWAY:
  Agent A (Legal) → has its own Salesforce connector → stores Salesforce creds
  Agent B (Finance) → has its own Salesforce connector → stores Salesforce creds
  Agent C (HR) → has its own Salesforce connector → stores Salesforce creds

  Problems:
  - Credentials stored in 3 places (security risk)
  - Bug in Salesforce connector must be fixed 3 times
  - Security team can't audit centrally
  - Each agent author must know Salesforce API

WITH GATEWAY:
  Agent A ──┐
  Agent B ──┼──► AgentCore Gateway ──► Salesforce Tool (one implementation)
  Agent C ──┘

  Benefits:
  - Credentials in one place
  - Fix bugs once
  - Central audit log
  - Agent authors just call the tool by name
```

### Two Types of Gateway Targets

```
TYPE 1: MCP TARGET (most common)
  Gateway acts as a unified MCP server
  Agents connect to ONE endpoint and get ALL tools
  Example: GitHub MCP, Salesforce MCP, your own MCP server

  AgentCore Gateway URL ──► exposes multiple MCP tools
                             (search_github, create_issue, list_prs...)

TYPE 2: HTTP TARGET
  Gateway forwards HTTP requests to your backend
  No protocol translation — direct passthrough
  Example: your internal REST API exposed as an agent tool
```

### Popular Enterprise Patterns

**Pattern 1: Unified MCP Access for Developer IDEs**
```
All developer tools (VS Code, Cursor, Claude Code, Kiro)
    ↓ connect to
ONE AgentCore Gateway URL
    ↓ which routes to
GitHub MCP + Salesforce MCP + AWS MCP + Databricks MCP + Internal APIs

Result: Developers configure ONE endpoint in their IDE, get ALL tools
```

**Pattern 2: Internal Tool Catalog**
```
Platform team builds internal "Tools-as-a-Service":
  Legal:    contract_search(), clause_extractor()
  Finance:  get_transaction(), run_query()
  HR:       lookup_employee(), get_policy()
  Ops:      restart_service(), get_metrics()

All exposed via ONE Gateway URL
All protected by AgentCore Policy (Cedar rules)
All audited via AgentCore Observability
All authenticated via AgentCore Identity
```

### Gateway Setup Code

```python
import boto3

control = boto3.client("bedrock-agentcore-control", region_name="us-east-1")

# STEP 1: Create a Gateway
gateway = control.create_gateway(
    gatewayName="EnterpriseToolGateway",
    # Auth: who can call this gateway?
    authorizerType="CUSTOM_JWT",
    authorizerConfiguration={
        "customJwtConfiguration": {
            "discoveryUrl": "https://cognito-idp.us-east-1.amazonaws.com/us-east-1_XXXXXX/.well-known/openid-configuration",
            "allowedAudience": ["your-app-client-id"],
        }
    },
    # Execution role: what AWS permissions does the gateway have?
    executionRoleArn="arn:aws:iam::123456789:role/AgentCoreGatewayRole",
)
gateway_id = gateway["gatewayId"]

# STEP 2: Attach an MCP server as a target
target = control.create_gateway_target(
    gatewayIdentifier=gateway_id,
    name="GitHubMCPServer",
    targetType="MCP",
    targetConfiguration={
        "mcp": {
            "endpoint": {
                "url": "https://my-github-mcp-server.example.com/mcp",
                "httpEndpointConfiguration": {
                    "authorizationConfiguration": {
                        "type": "CREDENTIAL_PROVIDER",
                        "credentialProviderConfiguration": {
                            # Credentials stored in AgentCore Identity, not in agent code
                            "credentialProviderType": "GATEWAY_IAM_ROLE",
                        }
                    }
                }
            }
        }
    }
)

# STEP 3: Use from an agent
# The agent just calls the MCP endpoint — no auth headers needed
# The Gateway handles authentication automatically

from strands import Agent
from strands.tools.mcp import MCPClient

mcp_client = MCPClient(lambda: gateway_endpoint_url)

agent = Agent(
    model=my_model,
    tools=[*mcp_client.list_tools()],   # Automatically discovers all tools
    system_prompt="You have access to GitHub and other enterprise tools.",
)
```

---

## 6. Component 3 — Memory

### What It Is

AgentCore Memory is a **fully managed memory service** that lets agents remember past interactions across multiple sessions. AWS manages the database, indexing, retrieval, and strategies.

### Why Memory Matters

```
WITHOUT MEMORY:
  Session 1: "Hi, I'm Rayudu. I prefer Python. I'm working on ML models."
  Session 2: "Can you help me write some code?" → Agent has no context
  Agent: "Sure! What language do you prefer?"  ← Already told it!

WITH MEMORY:
  Session 1: "Hi, I'm Rayudu. I prefer Python. I'm working on ML models."
             [Memory stores: name=Rayudu, language_pref=Python, project=ML]
  Session 2: "Can you help me write some code?"
             [Memory retrieves: Python preference, ML context]
  Agent: "I'll write this in Python for your ML project! Here's the code..."
```

### 4 Memory Strategies

```
STRATEGY 1: SEMANTIC
  What it stores: Important facts about the user
  Example: "User works in healthcare", "User prefers concise answers"
  How retrieved: By semantic similarity to current query
  Best for: User preferences, facts, knowledge

STRATEGY 2: SUMMARIZATION
  What it stores: Compressed summaries of past conversations
  Example: "In Jan session, discussed database performance. Resolved by adding index."
  How retrieved: By topic similarity
  Best for: Long-running projects, task history

STRATEGY 3: USER_PREFERENCE
  What it stores: Explicit preferences and settings
  Example: "Always use metric units", "Respond in bullet points"
  How retrieved: Applied to every new session automatically
  Best for: UX personalization, consistency

STRATEGY 4: EPISODIC
  What it stores: Timestamped records of specific events
  Example: "2024-01-15: User submitted support ticket #1234"
  How retrieved: By time range or semantic search
  Best for: Support systems, audit trails, task tracking
```

### Two Types of Memory: Short-Term vs Long-Term

```
SHORT-TERM MEMORY (within a session)
  Scope: One conversation session
  Storage: Ephemeral (lost when session ends by default)
  Purpose: Keep context during the current interaction
  Access: Fast, in-memory
  Use: Multi-turn conversations where you need history

LONG-TERM MEMORY (across sessions)
  Scope: Persists across all sessions, indefinitely (or configurable TTL)
  Storage: Managed database (AWS handles this)
  Purpose: Remember users, preferences, past work across days/weeks
  Access: Semantic search or direct lookup
  Use: Personalization, learning user preferences, episodic records
```

### Memory Code Example

```python
from bedrock_agentcore.memory import MemoryClient

# Connect to AgentCore Memory
memory = MemoryClient(
    memory_id="mem-abc123",    # Created via: agentcore add memory
    region="us-east-1",
)

user_id = "user-rayudu"

# ── STORE MEMORIES ─────────────────────────────────────────────────────

# Store a semantic fact about the user
memory.create_event(
    actor_id=user_id,
    session_id="session-001",
    messages=[
        {"role": "user", "content": "I prefer Python and I work on NLP models"},
        {"role": "assistant", "content": "I'll remember that you prefer Python for NLP work!"}
    ]
)
# AgentCore automatically extracts:
# - Semantic: "User prefers Python"
# - Semantic: "User works on NLP models"
# - Summarization: "User mentioned language preference and work domain"

# ── RETRIEVE MEMORIES ──────────────────────────────────────────────────

# On the NEXT session, retrieve relevant memories
memories = memory.retrieve(
    actor_id=user_id,
    namespace="default",
    query="What does the user prefer for coding?",
    top_k=5,
)

for m in memories:
    print(f"[{m['strategy']}] {m['content']}")
# → [SEMANTIC] User prefers Python
# → [USER_PREFERENCE] Use Python for all code examples
# → [EPISODIC] 2024-01-10: Helped with NLP tokenizer implementation

# ── INJECT INTO AGENT CONTEXT ──────────────────────────────────────────

memory_context = "\n".join([f"- {m['content']}" for m in memories])

agent = Agent(
    model=model,
    system_prompt=f"""You are a helpful assistant.
    
What you know about this user:
{memory_context}

Use this context to personalize your responses.""",
    tools=tools,
)
```

### Adding Memory via CLI

```bash
# Add semantic + preference memory (30-day retention)
agentcore add memory \
  --name UserMemory \
  --strategies SEMANTIC,USER_PREFERENCE \
  --expiry 30

# Or interactively:
agentcore add memory

# Then deploy to provision:
agentcore deploy
```

---

## 7. Component 4 — Identity and Auth

### What It Is

AgentCore Identity is a **security layer** that handles both:
- **Inbound auth**: Who is allowed to CALL your agent?
- **Outbound auth**: What APIs can your agent CALL on behalf of users?

### The Core Security Concept: Delegation

```
WITHOUT DELEGATION (bad):
  User tells agent: "My Gmail password is abc123"
  Agent stores password → HUGE security risk
  Agent logs in as the user → no audit trail

WITH DELEGATION (good):
  User authenticates with Google (not the agent)
  Google issues a limited-scope token to the agent
  Agent uses token to access ONLY what was permitted
  All actions logged as "Agent acted on behalf of User X"
  Token expires after set time → automatic revocation
```

### Inbound Auth — Who Can Call Your Agent?

```
OPTION 1: AWS IAM (default)
  Callers need AWS credentials
  Fine for AWS-native workflows, internal services

OPTION 2: Custom JWT (for external users)
  Users authenticate with YOUR identity provider (Cognito, Okta, etc.)
  They get a JWT token
  They send the JWT when calling your agent
  AgentCore validates the JWT before letting the request through

  Flow:
  User → Cognito → gets JWT → calls Agent API with JWT
                                     ↓
                              AgentCore validates JWT
                                     ↓
                              If valid: agent runs
                              If invalid: 401 error
```

**Setting up JWT Inbound Auth:**

```python
import boto3

control = boto3.client("bedrock-agentcore-control")

# Configure your runtime to require JWT tokens
control.create_agent_runtime(
    agentRuntimeName="SecureCustomerAgent",
    agentRuntimeArtifact={
        "containerConfiguration": {"containerUri": "123456789.dkr.ecr.us-east-1.amazonaws.com/my-agent:latest"}
    },
    # This enforces JWT auth on ALL incoming requests:
    networkConfiguration={"authorizationType": "CUSTOM_JWT"},
    authorizerConfiguration={
        "customJwtAuthorizer": {
            "discoveryUrl": "https://cognito-idp.us-east-1.amazonaws.com/us-east-1_POOL_ID/.well-known/openid-configuration",
            "allowedAudience": ["your-app-client-id"],
        }
    },
    executionRoleArn="arn:aws:iam::123456789:role/AgentRuntimeRole",
)

# Now callers MUST include Authorization: Bearer <jwt_token>
# Any request without a valid JWT is rejected before reaching agent code
```

### Outbound Auth — OAuth Flows

**2-Legged OAuth (M2M — Machine to Machine):**
```
When to use: Agent calls APIs without user involvement
Example: Agent calls your internal analytics API with a service account

Flow:
Agent → requests token from OAuth server → gets token → calls API
(No user involved, uses client_id + client_secret)
```

**3-Legged OAuth (Authorization Code — On Behalf Of User):**
```
When to use: Agent accesses user's data (Google Calendar, GitHub, etc.)
Example: Agent reads user's Google Calendar to schedule meetings

Flow:
1. User opens app → app redirects to Google OAuth page
2. User clicks "Allow this app to read my Calendar"
3. Google redirects back with authorization code
4. App exchanges code for access token
5. App passes access token to AgentCore Identity
6. Agent uses token to call Google Calendar API
7. Google's audit log shows "Agent X accessed Calendar on behalf of User Y"
```

**On-Behalf-Of (OBO) — for Multi-Agent Systems:**
```
When to use: Coordinator agent delegates to sub-agents WITH user context
Example: Orchestrator → Research Agent, both need to access user's data

Flow:
User Token
    ↓
Coordinator Agent mints ATTENUATED token (limited scope)
    ↓
Research Agent uses attenuated token to access APIs
    ↓
The sub-agent only has the permissions the coordinator chose to delegate
```

---

## 8. Component 5 — Code Interpreter

### What It Is

The Code Interpreter is a **fully isolated Python sandbox** that your agent can use to write and execute code safely. Each session gets its own clean microVM — files, variables, and processes are completely isolated.

### Why It's Needed

```
WITHOUT CODE INTERPRETER:
  Agent generates Python code
  ??? Where does it run? On your server = DANGEROUS!
  Bad code could: delete files, access secrets, crash the server, spin up processes

WITH CODE INTERPRETER:
  Agent generates Python code
  Code runs in AWS-managed isolated microVM
  MicroVM has: Python 3.12, writable filesystem, shell, AWS CLI
  If code is malicious: it only affects the isolated VM
  VM is destroyed after session ends
  Your servers are never touched
```

### Available Operations

```
OPERATION 1: executeCode
  Run Python code and capture stdout/stderr
  State persists within session (variables, imports)
  
OPERATION 2: writeFiles
  Upload files into the session's filesystem
  Agent can then read/process these files

OPERATION 3: executeCommand
  Run arbitrary shell commands in the isolated VM
  Full shell access: bash, curl, aws cli, etc.

OPERATION 4: readFiles
  Read files the agent or code has created
  Download outputs after execution
```

### Code Example

```python
from bedrock_agentcore.tools.code_interpreter_client import code_session

with code_session("us-east-1") as client:
    # ── Execute Python code ──────────────────────────────────────────
    response = client.invoke("executeCode", {
        "code": """
import numpy as np
import json

data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
result = {
    "mean": np.mean(data),
    "std": np.std(data),
    "max": max(data),
    "min": min(data),
}
print(json.dumps(result, indent=2))
""",
        "language": "python",
        "clearContext": False,  # Keep state from previous calls
    })
    
    for event in response["stream"]:
        result = event.get("result", {})
        stdout = result.get("structuredContent", {}).get("stdout", "")
        if stdout:
            print(stdout)
    # Output:
    # {
    #   "mean": 5.5,
    #   "std": 2.87,
    #   "max": 10,
    #   "min": 1
    # }
    
    # ── Write a file into the session ────────────────────────────────
    import base64
    csv_content = "name,score\nAlice,95\nBob,87\nCarol,92"
    
    client.invoke("writeFiles", {
        "files": [{
            "name": "scores.csv",
            "content": {"text": csv_content}
        }]
    })
    
    # ── Now the agent's code can read the file ───────────────────────
    response2 = client.invoke("executeCode", {
        "code": """
import pandas as pd
df = pd.read_csv('scores.csv')
print(f"Average score: {df['score'].mean():.1f}")
print(f"Highest scorer: {df.loc[df['score'].idxmax(), 'name']}")
""",
        "language": "python",
        "clearContext": False,  # file still exists from previous call
    })
    
    # ── Run a shell command ───────────────────────────────────────────
    response3 = client.invoke("executeCommand", {
        "command": "ls -la && python --version"
    })
# Context manager automatically stops the session when done
```

### Using Code Interpreter Inside an Agent

```python
from strands import Agent
from bedrock_agentcore.tools import CodeInterpreterTool

# Give the agent access to the code interpreter as a tool
code_interpreter = CodeInterpreterTool(region="us-east-1")

agent = Agent(
    model=my_model,
    tools=[code_interpreter],
    system_prompt="""You are a data analysis assistant.
When asked to analyze data, write and execute Python code using the code interpreter.
Always show the code you're running and explain the results.""",
)

# Now the agent can CHOOSE to run code when it decides to:
result = agent("Analyze this sales data and find the top 3 products: [...]")
# Agent thinks: "I should write Python code to analyze this"
# Agent calls: code_interpreter(code="import pandas as pd...")
# Agent gets back: results from the sandboxed execution
# Agent formats: "The top 3 products are..."
```

---

## 9. Component 6 — Browser Tool

### What It Is

The Browser Tool gives your agent the ability to **navigate and interact with real websites** — taking screenshots, clicking buttons, filling forms, and extracting content.

### What It Can Do

```
CAPABILITIES:
  ✓ Navigate to any URL
  ✓ Take screenshots (see what the page looks like)
  ✓ Click on buttons, links, form elements
  ✓ Type text into input fields
  ✓ Scroll up/down on pages
  ✓ Extract text content from pages
  ✓ Wait for page elements to load
  ✓ Handle JavaScript-rendered content

COMMON USE CASES:
  ✓ Web research (read actual page content, not just search results)
  ✓ Data extraction from websites
  ✓ Form automation (fill out forms on behalf of users)
  ✓ Visual testing of web applications
  ✓ Monitoring websites for changes
  ✓ Booking systems, e-commerce automation
```

### Browser Tool in Action

```python
from strands import Agent
from bedrock_agentcore.tools import BrowserTool

browser = BrowserTool(region="us-east-1")

agent = Agent(
    model=my_model,
    tools=[browser],
    system_prompt="""You are a web research assistant.
Use the browser to navigate to websites and extract information.
Always take a screenshot first to confirm what you're looking at.""",
)

# Agent can now browse the web:
result = agent("Go to news.ycombinator.com and tell me the top 3 stories right now")

# Agent will:
# 1. browser.navigate("https://news.ycombinator.com")
# 2. browser.screenshot() → sees the actual page
# 3. browser.extract_text() → gets the headlines
# 4. Formats and returns the results
```

### Webapp Visual Testing Use Case

```python
# Use case from: 01-features/01-harness/02-use-cases/02-webapp-visual-testing/

agent = Agent(
    model=my_model,
    tools=[browser],
    system_prompt="""You are a QA engineer testing web applications.
For each test:
1. Navigate to the page
2. Take a screenshot
3. Check if expected elements are present
4. Report pass/fail with evidence""",
)

# Automated visual regression testing:
test_result = agent("""
Test the login page at http://localhost:3000/login:
1. Check that the email field exists
2. Check that the password field exists
3. Check that the login button is visible
4. Try entering test@example.com and clicking login
5. Report what happened
""")
```

---

## 10. Component 7 — Observability

### What It Is

AgentCore Observability gives you **full visibility into what your agents are doing** — using OpenTelemetry (the industry standard for distributed tracing) to capture every step automatically.

### What Gets Captured Automatically

```
When your agent runs, AgentCore automatically captures:

SPANS:
  ├── invoke_agent (top-level)
  │   ├── model_call (LLM API call)
  │   │   ├── input_tokens: 1240
  │   │   ├── output_tokens: 89
  │   │   └── model: claude-haiku-4-5
  │   ├── tool_call: web_search
  │   │   ├── input: {"query": "AI trends 2024"}
  │   │   └── duration_ms: 823
  │   └── tool_call: write_file
  │       ├── input: {"path": "report.md"}
  │       └── duration_ms: 12

METRICS:
  └── agent.invocations (counter)
  └── agent.latency (histogram, p50/p95/p99)
  └── agent.token_usage (gauge)
  └── agent.errors (counter)
  └── agent.cost (counter in USD)
```

### Viewing Traces

All traces go to **AWS CloudWatch** automatically:

```
CloudWatch Console → X-Ray → Traces
→ See every agent invocation as a waterfall diagram
→ Click any span to see inputs/outputs
→ Filter by user_id, session_id, agent_name
→ Set alerts on error rates or latency thresholds
```

### Custom Spans — Adding Your Own Instrumentation

```python
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode

tracer = trace.get_tracer(__name__)

@tool
def web_search(query: str) -> str:
    """Search the web for information."""
    
    # Add a custom span with rich attributes
    with tracer.start_as_current_span("web_search") as span:
        span.set_attribute("search.query", query)
        span.set_attribute("search.engine", "duckduckgo")
        
        try:
            results = duckduckgo_search(query)
            span.set_attribute("search.results_count", len(results))
            span.set_status(Status(StatusCode.OK))
            return results
        
        except Exception as e:
            span.set_status(Status(StatusCode.ERROR, str(e)))
            span.record_exception(e)
            raise

# Your CloudWatch trace now shows:
# invoke_agent
#   └── model_call (auto)
#   └── web_search (YOUR CUSTOM SPAN)
#       ├── search.query: "AI trends 2024"
#       ├── search.engine: duckduckgo
#       └── search.results_count: 5
```

### Data Protection in Observability

```python
# Two-layer PII protection:

# LAYER 1: Bedrock Guardrails (before model sees the data)
# Detects and anonymizes PII in prompts and responses
# "My SSN is 123-45-6789" → "My SSN is [SSN]"

# LAYER 2: CloudWatch Data Protection (after logging)
# Masks PII in log events with ****
# "user@email.com" → "****"

# Setup:
control.create_agent_runtime(
    agentRuntimeName="PrivacyCompliantAgent",
    guardrailConfiguration={
        "guardrailId": "my-guardrail-id",     # Blocks PII at model level
        "guardrailVersion": "DRAFT",
    },
    ...
)
```

---

## 11. Component 8 — Evaluation

### What It Is

AgentCore Evaluation lets you **automatically measure the quality of your agent's responses** using three approaches:

```
APPROACH 1: GROUND TRUTH EVALUATION
  You have the "right" answers → compare agent output vs right answer
  Best for: Well-defined tasks where you know the correct output

APPROACH 2: LLM-AS-JUDGE EVALUATION
  Another LLM scores your agent's responses
  Best for: Open-ended responses where ground truth is subjective

APPROACH 3: CUSTOM CODE EVALUATION
  Your own Lambda function with domain-specific business logic
  Best for: Business rules that can't be expressed as LLM prompts
```

### Built-in Evaluators

| Evaluator | What It Measures | Score Range |
|-----------|-----------------|-------------|
| `GoalSuccessRate` | Did the agent complete the user's goal? | 0.0 – 1.0 |
| `Helpfulness` | Was the response useful and actionable? | 0.0 – 1.0 |
| `Correctness` | Did the agent give accurate information? | 0.0 – 1.0 |
| `TrajectoryToolSelectionAccuracy` | Did the agent choose the right tools? | 0.0 – 1.0 |
| `Faithfulness` | Is the response grounded in retrieved context? | 0.0 – 1.0 |

### Running Evaluation via CLI

```bash
# Evaluate a specific session
agentcore run eval \
  --runtime HRAssistant \
  --evaluator Builtin.GoalSuccessRate \
  --session-id sess-abc123

# Batch evaluation across many sessions
agentcore run batch-evaluation \
  --runtime HRAssistant \
  --evaluator Builtin.GoalSuccessRate Builtin.Helpfulness Builtin.Correctness

# Get AI-generated recommendations to improve your agent
agentcore run recommendation \
  --runtime HRAssistant \
  --type system-prompt \
  --evaluator Builtin.GoalSuccessRate

# Enable continuous monitoring (evaluates every session automatically)
agentcore add online-eval \
  --name HROnlineEval \
  --runtime HRAssistant \
  --evaluator Builtin.GoalSuccessRate Builtin.Helpfulness \
  --sampling-rate 100 \
  --enable-on-create
```

### A/B Testing with Configuration Bundles

AgentCore has a unique capability: you can change your agent's system prompt or tool descriptions WITHOUT redeploying code, and run A/B tests:

```bash
# Current: HRAssistant v1 (old system prompt)

# Step 1: Get AI recommendation for a better system prompt
agentcore run recommendation \
  --runtime HRAssistant \
  --type system-prompt \
  --evaluator Builtin.GoalSuccessRate

# Step 2: Create a "config bundle" with the new system prompt
agentcore add config-bundle \
  --name HRAssistV2 \
  --system-prompt "You are an expert HR assistant with deep knowledge of employment law..."

# Step 3: Run A/B test (50% v1, 50% v2)
agentcore add ab-test \
  --name HRAssistABTest \
  --variant-a HRAssistV1 \
  --variant-b HRAssistV2 \
  --split 50/50

# Or run canary test (10% v2, 90% v1)
agentcore add ab-test \
  --name HRAssistCanary \
  --variant-a HRAssistV1 \
  --variant-b HRAssistV2 \
  --split 90/10    # Only 10% of users see v2
```

---

## 12. Component 9 — Policy

### What It Is

AgentCore Policy uses **Cedar** (an open-source policy language from AWS) to define **deterministic rules** about what agents can and cannot do.

### Why Cedar vs Just Using the LLM Guardrails?

```
LLM GUARDRAILS (probabilistic):
  "Don't process refunds over $500"
  → LLM might follow this 98% of the time
  → Edge cases exist (prompt engineering, unusual phrasing)
  → Not auditable ("the model decided...")

CEDAR POLICY (deterministic):
  permit(principal, action == Action::"processRefund")
    when { context.amount <= 500 };
  → ALWAYS blocks refunds over $500, no exceptions
  → Code-level enforcement, not model-level
  → Complete audit trail
  → Update policy without redeploying agent code
```

### Cedar Policy Example

```
// Customer support agent — refund policy
// File: refund-policy.cedar

// Allow standard agents to process small refunds
permit(
    principal in Group::"CustomerSupportAgents",
    action == Action::"processRefund",
    resource is RefundRequest
) when {
    // JWT claim: amount from the user's request
    context.amount <= 100 &&
    context.reason_code in ["DEFECTIVE", "NOT_AS_DESCRIBED", "NEVER_ARRIVED"]
};

// Allow senior agents to process larger refunds
permit(
    principal in Group::"SeniorSupportAgents",
    action == Action::"processRefund",
    resource is RefundRequest
) when {
    context.amount <= 500
};

// Allow managers to process any refund
permit(
    principal in Group::"SupportManagers",
    action == Action::"processRefund",
    resource is RefundRequest
);

// Block all other refund attempts
forbid(
    principal,
    action == Action::"processRefund",
    resource is RefundRequest
);
```

```bash
# Apply the policy to your gateway
agentcore add policy \
  --name RefundPolicy \
  --policy-file refund-policy.cedar \
  --target EnterpriseToolGateway

# Now: when agent calls processRefund with amount=600 as a StandardAgent
# → Policy Engine evaluates → DENY
# → Agent gets 403 error → must inform user "I can't process refunds over $500"
```

---

## 13. Component 10 — Agent Registry

### What It Is

The Agent Registry is a **searchable catalog of all agents in your organization**. When you have dozens of agents, the registry lets you discover and invoke agents by capability.

```
SCENARIO: Multi-Agent Orchestration
  Coordinator agent receives: "Analyze Q3 sales and create a report"
  
  WITHOUT REGISTRY:
    Coordinator must know hardcoded ARNs of all specialist agents
    Adding a new specialist requires code changes to coordinator
  
  WITH REGISTRY:
    Coordinator queries: registry.search("sales analysis")
    → Returns: SalesAnalystAgent (ARN, capabilities, description)
    Coordinator queries: registry.search("report writing")
    → Returns: ReportWriterAgent (ARN, capabilities, description)
    Coordinator delegates to the right agents dynamically
```

```python
import boto3

registry = boto3.client("bedrock-agentcore-control")

# Register your agent in the catalog
registry.create_agent(
    agentName="SalesAnalystAgent",
    description="Analyzes sales data, generates insights, and creates visualizations",
    capabilities=["sales-analysis", "data-visualization", "trend-detection"],
    runtimeArn="arn:aws:bedrock-agentcore:us-east-1:123:runtime/SalesAnalystAgent",
)

# Coordinator searches for the right agent
results = registry.list_agents(
    filters=[{"key": "capability", "values": ["sales-analysis"]}]
)

for agent in results["agents"]:
    print(f"Found: {agent['agentName']} — {agent['description']}")
    print(f"ARN: {agent['runtimeArn']}")
```

---

## 14. Framework Support — Strands, LangGraph, CrewAI, OpenAI

AgentCore is **framework-agnostic**. The `BedrockAgentCoreApp` wrapper works with any framework.

### Strands Agents (AWS's Native Framework)

```python
from strands import Agent, tool
from strands.models import BedrockModel
from bedrock_agentcore.runtime import BedrockAgentCoreApp

app = BedrockAgentCoreApp()

@tool
def calculator(expression: str) -> str:
    """Evaluate a math expression."""
    return str(eval(expression))

model = BedrockModel(model_id="global.anthropic.claude-haiku-4-5-20251001-v1:0")
agent = Agent(model=model, tools=[calculator], system_prompt="You are a math assistant.")

@app.entrypoint
def strands_handler(payload):
    return agent(payload.get("prompt")).message["content"][0]["text"]

if __name__ == "__main__":
    app.run()
```

### LangGraph (Stateful Graph Agents)

```python
from langgraph.graph import StateGraph, MessagesState
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_aws import ChatBedrock
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, SystemMessage
from bedrock_agentcore.runtime import BedrockAgentCoreApp

app = BedrockAgentCoreApp()

@tool
def calculator(expression: str) -> str:
    """Calculate a math expression."""
    import math
    safe_env = {k: getattr(math, k) for k in dir(math) if not k.startswith("_")}
    return str(eval(expression, {"__builtins__": {}}, safe_env))

@tool
def weather() -> str:
    """Get current weather."""
    return "sunny"

def create_agent():
    llm = ChatBedrock(model_id="global.anthropic.claude-haiku-4-5-20251001-v1:0")
    tools = [calculator, weather]
    llm_with_tools = llm.bind_tools(tools)
    
    def chatbot(state: MessagesState):
        messages = state["messages"]
        if not isinstance(messages[0], SystemMessage):
            messages = [SystemMessage("You are a helpful assistant.")] + messages
        return {"messages": [llm_with_tools.invoke(messages)]}
    
    graph = StateGraph(MessagesState)
    graph.add_node("chatbot", chatbot)
    graph.add_node("tools", ToolNode(tools))
    graph.add_conditional_edges("chatbot", tools_condition)
    graph.add_edge("tools", "chatbot")
    graph.set_entry_point("chatbot")
    return graph.compile()

agent = create_agent()

@app.entrypoint
def langgraph_handler(payload):
    result = agent.invoke({"messages": [HumanMessage(payload.get("prompt"))]})
    return result["messages"][-1].content

if __name__ == "__main__":
    app.run()
```

### CrewAI (Role-Based Teams)

```python
from crewai import Agent, Task, Crew
from bedrock_agentcore.runtime import BedrockAgentCoreApp

app = BedrockAgentCoreApp()

researcher = Agent(
    role="Research Analyst",
    goal="Find accurate information about any topic",
    backstory="Expert researcher with comprehensive knowledge",
    verbose=True,
)

writer = Agent(
    role="Content Writer",
    goal="Write clear, engaging content based on research",
    backstory="Experienced writer who makes complex topics accessible",
    verbose=True,
)

@app.entrypoint
def crewai_handler(payload):
    topic = payload.get("prompt")
    
    research_task = Task(
        description=f"Research {topic} thoroughly",
        expected_output="Comprehensive research findings",
        agent=researcher,
    )
    writing_task = Task(
        description="Write a clear summary based on the research",
        expected_output="Well-written summary",
        agent=writer,
        context=[research_task],
    )
    
    crew = Crew(agents=[researcher, writer], tasks=[research_task, writing_task])
    result = crew.kickoff()
    return str(result)

if __name__ == "__main__":
    app.run()
```

---

## 15. The AgentCore CLI — Developer Workflow

The AgentCore CLI is the **fastest way to create, develop, and deploy agents**. It replaces hours of infrastructure setup with a few commands.

### Complete CLI Workflow

```bash
# ── INSTALL ────────────────────────────────────────────────────────────
npm install -g @aws/agentcore
agentcore --version

# ── CREATE A NEW PROJECT ───────────────────────────────────────────────
agentcore create \
  --name CustomerSupport \
  --framework Strands \
  --model-provider Bedrock \
  --defaults
cd CustomerSupport

# ── PROJECT STRUCTURE CREATED ─────────────────────────────────────────
# CustomerSupport/
# ├── agentcore/
# │   ├── agentcore.json         ← Project config
# │   ├── aws-targets.json       ← Deployment targets (region, account)
# │   ├── .env.local             ← Local secrets (gitignored)
# │   └── cdk/                   ← CDK infrastructure (auto-managed)
# └── app/
#     └── CustomerSupport/
#         ├── main.py            ← Your agent code (edit this)
#         ├── model/load.py      ← Model configuration
#         └── pyproject.toml     ← Python dependencies

# ── EDIT YOUR AGENT CODE (app/CustomerSupport/main.py) ───────────────
# (see the complete agent code in section 17)

# ── LOCAL DEVELOPMENT ──────────────────────────────────────────────────
agentcore dev               # Start interactive chat on :8080
agentcore dev --logs        # Show logs while running
agentcore dev "What products do you have?" --stream   # Non-interactive test

# ── DEPLOY TO AWS ──────────────────────────────────────────────────────
agentcore deploy            # Packages + provisions + deploys to AWS

# ── CHECK STATUS ───────────────────────────────────────────────────────
agentcore status
# → Agents: CustomerSupport — READY (arn:aws:bedrock-agentcore:...)

# ── INVOKE DEPLOYED AGENT ──────────────────────────────────────────────
agentcore invoke "What's the return policy for electronics?" --stream

# ── ADD CAPABILITIES ───────────────────────────────────────────────────
agentcore add memory --name UserMemory --strategies SEMANTIC,USER_PREFERENCE --expiry 30
agentcore add gateway --name ToolGateway --runtimes CustomerSupport
agentcore add evaluator --name QualityCheck --type llm-as-a-judge
agentcore add online-eval --name ContinuousMonitor --runtime CustomerSupport \
  --evaluator Builtin.GoalSuccessRate --sampling-rate 100 --enable-on-create

# Sync all changes to AWS
agentcore deploy

# ── VIEW LOGS AND TRACES ───────────────────────────────────────────────
agentcore logs                          # Stream live logs
agentcore traces list --limit 10        # See recent traces
agentcore traces get --id trace-abc123  # Inspect specific trace

# ── CLEAN UP ───────────────────────────────────────────────────────────
agentcore remove all
agentcore deploy    # Applies the removal to AWS
```

---

## 16. Repository Structure Walkthrough

```
agentcore-samples-main/
│
├── 00-getting-started/               ← START HERE
│   ├── README.md                     ← Step-by-step first agent guide
│   └── main.py                       ← The complete customer support agent code
│
├── 01-features/                      ← DEEP DIVES INTO EACH FEATURE
│   ├── 01-harness/                   ← Low-level Harness API
│   │   ├── 00-getting-started/
│   │   │   └── getting_started.py    ← Full Harness demo (create/invoke/shell)
│   │   ├── 01-advanced-examples/
│   │   │   ├── 01-custom-containers/ ← Bring your own Docker image
│   │   │   ├── 02-gateway-integration/ ← Harness + Gateway combo
│   │   │   ├── 03-execution-limits/  ← Timeouts and resource limits
│   │   │   ├── 04-mcp-integration/   ← MCP tools in Harness
│   │   │   ├── 05-agent-skills/      ← Custom reusable skills
│   │   │   ├── 06-async-step-function/ ← Long-running async tasks
│   │   │   ├── 07-oauth/             ← OAuth tool authentication
│   │   │   ├── 08-gemini-model-provider/ ← Use Gemini instead of Claude
│   │   │   ├── 09-openai-model-provider/ ← Use OpenAI instead of Claude
│   │   │   └── 10-agent-inspector/   ← Debug agent state visually
│   │   └── 02-use-cases/
│   │       ├── 01-travel-agent/      ← Full travel planning agent
│   │       ├── 02-webapp-visual-testing/ ← QA automation agent
│   │       └── 03-aws-builder-agent/ ← Agent that builds AWS infrastructure
│   │
│   ├── 02-host-your-agent/           ← RUNTIME DEPLOYMENT
│   │   └── 01-runtime/
│   │       └── 01-hosting-agents/
│   │           └── 01-http-protocol/
│   │               ├── 01-strands-bedrock/ ← Strands + Claude on Bedrock
│   │               ├── 02-langgraph-bedrock/ ← LangGraph + Claude on Bedrock
│   │               ├── 03-strands-openai/ ← Strands + OpenAI
│   │               └── 04-strands-gemini/ ← Strands + Gemini
│   │
│   ├── 03-connect-your-agent-to-anything/ ← TOOLS
│   │   ├── 01-code-interpreter/      ← Sandboxed Python execution
│   │   └── 02-browser/               ← Web browsing tool
│   │
│   ├── 04-manage-context-of-your-agent/ ← MEMORY
│   │   └── memory/
│   │       ├── 00-getting-started/   ← Memory concepts + quickstarts
│   │       ├── 01-short-term-memory/ ← Session-level memory
│   │       ├── 02-long-term-memory/  ← Cross-session persistent memory
│   │       └── 03-integrations/      ← Connect memory to runtime
│   │
│   ├── 05-authenticate-and-authorize/ ← IDENTITY
│   │   ├── 01-inbound-auth/          ← JWT protection for your agent
│   │   ├── 02-outbound-auth/         ← OAuth for external APIs
│   │   ├── 03-m2m-3lo/              ← Combined M2M + Auth Code
│   │   ├── 04-entra-obo-mcp-runtime/ ← Advanced: Entra ID OBO
│   │   ├── auth0-multi-agent-obo/    ← Multi-agent token delegation
│   │   └── okta-auth-three-tier-end-to-end-demo/ ← Full Okta demo
│   │
│   ├── 06-observe-evaluate-optimize-your-agent/ ← OBS + EVAL
│   │   ├── 01-observe/               ← Custom spans, data protection
│   │   ├── 02-evaluate/              ← Ground truth, LLM judge, custom
│   │   └── 03-optimize/              ← Config bundles, A/B testing
│   │
│   ├── 07-centralize-and-govern-your-ai-infrastructure/ ← GATEWAY + POLICY
│   │   ├── 01-gateway/               ← MCP gateway setup and targets
│   │   ├── 02-policy/                ← Cedar policy enforcement
│   │   └── 03-registry/              ← Agent discovery catalog
│   │
│   └── 08-agents-that-transact/      ← PAYMENTS
│       ├── 00-getting-started/       ← Payment-capable agents
│       └── 02-use-cases/             ← E-commerce, subscription agents
│
├── 02-use-cases/                     ← DOMAIN-SPECIFIC EXAMPLES
│   ├── 01-conversational-agents/     ← Chatbots with memory
│   ├── 02-workflow-automation-agents/ ← Automate business processes
│   └── 03-coding-assistants/         ← Software development agents
│
├── 03-integrations/                  ← CONNECT TO YOUR STACK
│   ├── 3p-observability/             ← Grafana, Datadog, Dynatrace
│   ├── agentic-frameworks/           ← All frameworks side by side
│   ├── AgentOps-Langfuse/            ← Alternative observability
│   ├── agents-hosted-outside-runtime/ ← Self-hosted agents using AgentCore services
│   ├── bedrock-agent/                ← Connect Bedrock native agents
│   ├── data-platforms/               ← Snowflake, Redshift, etc.
│   ├── gateway/                      ← Gateway integration patterns
│   ├── nova/                         ← Amazon Nova model integration
│   ├── ux-examples/                  ← Streamlit, AG-UI frontends
│   └── vector-stores/                ← Pinecone, Qdrant, OpenSearch
│
├── 04-infrastructure-as-code/        ← DEPLOYMENT AUTOMATION
│   ├── cdk/                          ← AWS CDK templates
│   ├── cloudformation/               ← CloudFormation templates
│   └── terraform/                    ← Terraform modules
│
├── 05-blueprints/                    ← FULL REFERENCE APPS
│   ├── customer-support-agent-with-agentcore/ ← Full prod customer support
│   ├── end-to-end-customer-service-agent/ ← Alternative full e2e example
│   ├── multitenant-agentic-platform/ ← SaaS multi-tenant architecture
│   ├── shopping-concierge-agent/     ← E-commerce shopping assistant
│   └── travel-concierge-agent/       ← Full travel booking agent
│
└── 06-workshops/                     ← GUIDED LEARNING PATHS
    ├── 01-AgentCore-runtime/         ← Runtime workshop
    ├── 02-AgentCore-gateway/         ← Gateway workshop
    ├── 03-AgentCore-identity/        ← Identity workshop
    ├── 04-AgentCore-memory/          ← Memory workshop
    ├── 05-AgentCore-tools/           ← Tools workshop
    ├── 06-AgentCore-observability/   ← Observability workshop
    ├── 07-AgentCore-evaluations/     ← Evaluations workshop
    ├── 08-AgentCore-policy/          ← Policy workshop
    ├── 09-AgentCore-E2E/             ← End-to-end integration workshop
    ├── 10-Agent-Registry/            ← Registry workshop
    ├── 11-AgentCore-harness/         ← Harness workshop
    ├── 12-AgentCore-optimization/    ← Optimization workshop
    └── 13-AgentCore-payments/        ← Payments workshop
```

---

## 17. End-to-End Example 1 — Customer Support Agent

This is the flagship getting-started example. Here is the complete code with every line explained:

```python
# ── IMPORTS ────────────────────────────────────────────────────────────────
from strands import Agent, tool           # Strands agent framework
from bedrock_agentcore.runtime import BedrockAgentCoreApp  # AgentCore wrapper
from model.load import load_model         # Model loader (Claude via Bedrock)

# ── APP INITIALIZATION ─────────────────────────────────────────────────────
# BedrockAgentCoreApp is the bridge between your agent code and AgentCore
# It handles:
#   - HTTP server for local dev (port 8080)
#   - Protocol translation (HTTP ↔ streaming SSE)
#   - Logging to CloudWatch
#   - OpenTelemetry trace emission
app = BedrockAgentCoreApp()
log = app.logger   # Structured logger that goes to CloudWatch

# ── DATA LAYER ────────────────────────────────────────────────────────────
# In production: these would be database queries, not hardcoded dicts
RETURN_POLICIES = {
    "electronics": {
        "window": "30 days",
        "condition": "Original packaging required, must be unused or defective",
        "refund": "Full refund to original payment method",
    },
    "accessories": {
        "window": "14 days",
        "condition": "Must be in original packaging, unused",
        "refund": "Store credit or exchange",
    },
    "audio": {
        "window": "30 days",
        "condition": "Defective items only after 15 days",
        "refund": "Full refund within 15 days, replacement after",
    },
}

PRODUCTS = {
    "PROD-001": {"name": "Wireless Headphones", "price": 79.99, "category": "audio",
                 "description": "Noise-cancelling Bluetooth headphones with 30h battery life",
                 "warranty_months": 12},
    "PROD-002": {"name": "Smart Watch", "price": 249.99, "category": "electronics",
                 "description": "Fitness tracker with heart rate monitor, GPS, and 5-day battery",
                 "warranty_months": 24},
    "PROD-003": {"name": "Laptop Stand", "price": 39.99, "category": "accessories",
                 "description": "Adjustable aluminum laptop stand for ergonomic desk setup",
                 "warranty_months": 6},
}

# ── TOOL DEFINITIONS ──────────────────────────────────────────────────────
# @tool decorator: turns a Python function into an LLM-callable tool
# The DOCSTRING is what the LLM reads to understand when/how to call the tool
# Args section in docstring = parameter descriptions the LLM uses

@tool
def get_return_policy(product_category: str) -> str:
    """Get return policy information for a specific product category.

    Args:
        product_category: Product category (e.g., 'electronics', 'accessories', 'audio')

    Returns:
        Formatted return policy details including timeframes and conditions
    """
    category = product_category.lower()
    if category in RETURN_POLICIES:
        policy = RETURN_POLICIES[category]
        return (f"Return policy for {category}: "
                f"Window: {policy['window']}, "
                f"Condition: {policy['condition']}, "
                f"Refund: {policy['refund']}")
    return f"No specific return policy found for '{product_category}'. Please contact support."


@tool
def get_product_info(query: str) -> str:
    """Search for product information by name, ID, or keyword.

    Args:
        query: Product name, ID (e.g., 'PROD-001'), or search keyword

    Returns:
        Product details including name, price, category, and description
    """
    query_lower = query.lower()
    
    # Exact ID match
    if query.upper() in PRODUCTS:
        p = PRODUCTS[query.upper()]
        return (f"{p['name']} ({query.upper()}): ${p['price']}, "
                f"Category: {p['category']}, {p['description']}, "
                f"Warranty: {p['warranty_months']} months")
    
    # Keyword search
    results = [
        f"{pid}: {p['name']} - ${p['price']} - {p['description']}"
        for pid, p in PRODUCTS.items()
        if query_lower in p['name'].lower()
        or query_lower in p['description'].lower()
        or query_lower in p['category'].lower()
    ]
    
    return "Found products:\n" + "\n".join(results) if results else f"No products found matching '{query}'."


# ── AGENT CONFIGURATION ────────────────────────────────────────────────────
# The system prompt defines the agent's identity, capabilities, and rules
SYSTEM_PROMPT = """You are a helpful and professional customer support assistant.

Your role is to:
- Provide accurate information using the tools available to you
- Be friendly, patient, and understanding with customers
- Always offer additional help after answering questions

You have access to:
1. get_return_policy() - Look up return policies by product category
2. get_product_info() - Search product information by name, ID, or keyword

Always use the appropriate tool rather than guessing.
Never make up product information or policies."""

# Singleton pattern: create agent once, reuse across requests
_agent = None

def get_or_create_agent():
    """Lazy initialization: agent is created on first request"""
    global _agent
    if _agent is None:
        _agent = Agent(
            model=load_model(),             # Claude Sonnet via Bedrock
            system_prompt=SYSTEM_PROMPT,
            tools=[get_return_policy, get_product_info],
        )
    return _agent


# ── ENTRYPOINT ────────────────────────────────────────────────────────────
# @app.entrypoint marks this function as the handler AgentCore calls
# payload = the JSON body of the invocation request
# context = AWS request context (session ID, trace ID, etc.)

@app.entrypoint
async def invoke(payload, context):
    """Stream the agent's response back to the caller."""
    log.info(f"Invoking agent with prompt: {payload.get('prompt', '')[:100]}")
    
    agent = get_or_create_agent()
    
    # stream_async generates token-by-token output
    stream = agent.stream_async(payload.get("prompt"))
    
    async for event in stream:
        if "data" in event and isinstance(event["data"], str):
            yield event["data"]   # Each yield sends a chunk to the client


# ── LOCAL ENTRY POINT ──────────────────────────────────────────────────────
if __name__ == "__main__":
    app.run()   # Starts local dev server on :8080
                # `agentcore dev` calls this automatically
```

### What Happens When a User Sends "I want to return my Smart Watch"

```
STEP 1: User sends request
  POST /invoke {"prompt": "I want to return my Smart Watch (PROD-002)"}

STEP 2: BedrockAgentCoreApp receives request
  - Validates request format
  - Injects trace context (run_id, session_id)
  - Calls invoke() function

STEP 3: Agent receives prompt
  agent.stream_async("I want to return my Smart Watch (PROD-002)")

STEP 4: LLM thinks (internal)
  "The user wants to return a product. I should:
   1. Call get_product_info('PROD-002') to get its category
   2. Then call get_return_policy(category) to get the policy"

STEP 5: LLM calls get_product_info
  → Input: {"query": "PROD-002"}
  → Output: "Smart Watch (PROD-002): $249.99, Category: electronics, ..."

STEP 6: LLM calls get_return_policy
  → Input: {"product_category": "electronics"}
  → Output: "Return policy for electronics: Window: 30 days, Condition: Original packaging required..."

STEP 7: LLM generates response (streamed)
  "I'd be happy to help with your Smart Watch return!
   
   Here are the return details for electronics:
   - Return Window: 30 days from purchase
   - Condition: Original packaging required, must be unused or defective
   - Refund: Full refund to original payment method
   
   Is there anything else I can help you with?"

STEP 8: Response streams to user
  Each token yields through the event generator → SSE to client

STEP 9: Trace sent to CloudWatch
  - Full span tree with timing for each step
  - Token counts and cost
  - Tool call inputs and outputs
```

---

## 18. End-to-End Example 2 — Harness (Low-Level API)

The Harness API is for when you need direct control over the AI execution environment:

```python
"""
Low-level Harness walkthrough — complete with all steps explained
"""
import time
import uuid
import boto3
from utils.iam import create_harness_role, delete_harness_role
from utils.client import get_agentcore_control_client, get_agentcore_client

# Two clients — management vs execution
control = get_agentcore_control_client()   # bedrock-agentcore-control
client  = get_agentcore_client()           # bedrock-agentcore

# Models available via Bedrock global inference profiles
CLAUDE_HAIKU  = "global.anthropic.claude-haiku-4-5-20251001-v1:0"
CLAUDE_SONNET = "global.anthropic.claude-sonnet-4-6"

# ── 1. IAM SETUP ──────────────────────────────────────────────────────────────
# The Harness needs permission to call Bedrock, write to CloudWatch, etc.
role_arn = create_harness_role()
time.sleep(10)  # Wait for IAM to propagate globally

# ── 2. CREATE THE HARNESS ─────────────────────────────────────────────────────
# This provisions a pool of isolated microVMs ready to serve sessions
resp = control.create_harness(
    harnessName=f"Demo_{uuid.uuid4().hex[:8]}",
    executionRoleArn=role_arn,
)
harness_id  = resp["harness"]["harnessId"]
harness_arn = resp["harness"]["arn"]

# Wait for READY (microVMs are warming up)
for _ in range(12):
    if control.get_harness(harnessId=harness_id)["harness"]["status"] == "READY":
        break
    time.sleep(5)

# ── 3. INVOKE WITH CLAUDE HAIKU ───────────────────────────────────────────────
# Session ID = one isolated VM instance
session_id = str(uuid.uuid4()).upper()

response = client.invoke_harness(
    harnessArn=harness_arn,
    runtimeSessionId=session_id,
    messages=[{
        "role": "user",
        "content": [{"text": "List top 3 Seattle activities. Save to activities.md"}]
    }],
    model={"bedrockModelConfig": {"modelId": CLAUDE_HAIKU}},
)

# Process streaming events
for event in response["stream"]:
    if "contentBlockDelta" in event:
        delta = event["contentBlockDelta"].get("delta", {})
        if "text" in delta:
            print(delta["text"], end="", flush=True)
    elif "contentBlockStart" in event:
        start = event["contentBlockStart"].get("start", {})
        if "toolUse" in start:
            print(f"\n[Tool call: {start['toolUse']['name']}]")

# ── 4. CONTINUE SAME SESSION WITH DIFFERENT MODEL ─────────────────────────────
# Session state (files, history) persists — SAME session_id, DIFFERENT model
response2 = client.invoke_harness(
    harnessArn=harness_arn,
    runtimeSessionId=session_id,           # ← Same session = same VM state
    messages=[{
        "role": "user",
        "content": [{"text": "Now add a header 'Written by Claude Sonnet' to the file"}]
    }],
    model={"bedrockModelConfig": {"modelId": CLAUDE_SONNET}},  # ← Different model
)

# ── 5. EXECUTE SHELL COMMANDS ON THE AGENT'S VM ───────────────────────────────
def run(cmd: str):
    """Run a shell command on the remote microVM and print output."""
    print(f"\n$ {cmd}")
    resp = client.invoke_agent_runtime_command(
        agentRuntimeArn=harness_arn,
        runtimeSessionId=session_id,
        body={"command": cmd},
    )
    for event in resp["stream"]:
        if "chunk" in event:
            d = event["chunk"].get("contentDelta", {})
            if "stdout" in d:
                print(d["stdout"], end="")
            if "stderr" in d:
                print(d["stderr"], end="")

# See what files the agent created
run("ls -la")

# Read the markdown file the agent wrote
run("cat activities.md")

# Run a Python script on the VM
run("python3 -c 'import sys; print(sys.version)'")

# Check disk usage
run("df -h /")

# ── 6. CLEANUP ────────────────────────────────────────────────────────────────
control.delete_harness(harnessId=harness_id)
delete_harness_role()
```

---

## 19. Blueprints — Production Reference Applications

### Blueprint 1: Customer Support Agent (Most Complete Reference)

**Location:** `05-blueprints/customer-support-agent-with-agentcore/`

**What it demonstrates:**
```
COMPONENTS USED:
  ✓ AgentCore Runtime (Strands agent hosted as container)
  ✓ AgentCore Gateway (MCP gateway for tool routing)
  ✓ AgentCore Policy (Cedar policy for refund limits)
  ✓ AgentCore Memory (per-user persistent memory)
  ✓ AgentCore Identity (Cognito JWT inbound auth)
  ✓ CloudWatch (auto-instrumented OpenTelemetry traces)
  ✓ Lambda (mock customer and order API backends)

ARCHITECTURE:
  User → Cognito authentication → gets JWT
  → calls AgentCore Runtime with JWT
  → Runtime verifies JWT
  → Agent calls tools via AgentCore Gateway
  → Gateway checks Cedar Policy (refund limits)
  → Gateway routes to Lambda functions
  → Agent reads/writes user memory via AgentCore Memory
  → All traces go to CloudWatch automatically
```

**The Policy in Action:**
```
# Cedar policy enforced by the Gateway:
# Standard support agents can only refund up to $100
# Senior agents up to $500
# Managers unlimited

When customer asks for $600 refund:
  Agent calls → Gateway → Policy Engine → DENY
  Agent response: "I can only process refunds up to $100. 
                   Let me escalate to a manager for you."
```

### Blueprint 2: Travel Concierge Agent

**Location:** `05-blueprints/travel-concierge-agent/`

An agent that books flights, hotels, and activities — with full OAuth to external travel APIs.

### Blueprint 3: Multi-Tenant Agentic Platform

**Location:** `05-blueprints/multitenant-agentic-platform/`

Shows how to build a SaaS platform where multiple companies share the same AgentCore infrastructure but have complete data isolation.

---

## 20. Infrastructure as Code

### AWS CDK (Python)

```python
# cdk/agent_stack.py — Infrastructure as code for AgentCore deployment
from aws_cdk import Stack, aws_iam as iam, aws_bedrock_agentcore as agentcore
from constructs import Construct

class AgentStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)
        
        # IAM role for the agent runtime
        execution_role = iam.Role(
            self, "AgentExecutionRole",
            assumed_by=iam.ServicePrincipal("bedrock-agentcore.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonBedrockFullAccess"),
                iam.ManagedPolicy.from_aws_managed_policy_name("CloudWatchLogsFullAccess"),
            ]
        )
        
        # AgentCore Runtime
        runtime = agentcore.CfnAgentRuntime(
            self, "CustomerSupportRuntime",
            agent_runtime_name="CustomerSupport",
            agent_runtime_artifact={
                "containerConfiguration": {
                    "containerUri": f"{self.account}.dkr.ecr.{self.region}.amazonaws.com/agent:latest"
                }
            },
            execution_role_arn=execution_role.role_arn,
            network_configuration={"authorizationType": "AWS_IAM"},
        )
```

### Terraform

```hcl
# terraform/main.tf
resource "aws_iam_role" "agent_execution_role" {
  name = "AgentCoreExecutionRole"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "bedrock-agentcore.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "bedrock_access" {
  role       = aws_iam_role.agent_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonBedrockFullAccess"
}

# Note: AgentCore Terraform resources are managed via the AgentCore CLI/CDK
# Terraform manages supporting infrastructure (IAM, ECR, VPC)
```

---

## 21. Workshops — Learning Paths

The `06-workshops/` folder contains 13 guided workshops you can follow in sequence:

| Workshop | What You'll Build | Duration |
|---------|------------------|---------|
| 01 — Runtime | Deploy your first agent to AgentCore Runtime | 30 min |
| 02 — Gateway | Set up a centralized tool gateway | 45 min |
| 03 — Identity | Add JWT auth + OAuth to your agent | 60 min |
| 04 — Memory | Give your agent cross-session memory | 45 min |
| 05 — Tools | Integrate Code Interpreter and Browser tools | 60 min |
| 06 — Observability | Set up custom spans and CloudWatch dashboards | 45 min |
| 07 — Evaluations | Run batch evals with LLM-as-judge | 45 min |
| 08 — Policy | Write Cedar policies for agent governance | 60 min |
| 09 — E2E | Build the complete integrated system | 90 min |
| 10 — Registry | Register agents in the org-wide catalog | 30 min |
| 11 — Harness | Use the low-level Harness API directly | 60 min |
| 12 — Optimization | A/B test prompt changes without redeployment | 60 min |
| 13 — Payments | Build an agent that can make payments | 60 min |

**Recommended order for beginners:** 01 → 04 → 06 → 07 → 02 → 03 → 08 → 09

---

## 22. Request Lifecycle — A to Z

Trace one user request through the complete AgentCore system:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 1: User authenticates (t=0ms)
  User logs in to your app → Cognito validates credentials
  Cognito issues JWT: {sub: "user-rayudu", groups: ["StandardSupport"]}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 2: User sends request (t=10ms)
  POST /invoke
  Headers: Authorization: Bearer <jwt_token>
  Body: {"prompt": "I want a $150 refund for order #4521"}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 3: AgentCore Runtime receives request (t=15ms)
  - Validates JWT signature against Cognito discovery URL
  - JWT valid ✓ → extract user claims (user-rayudu, StandardSupport)
  - Injects trace context (trace_id, session_id)
  - Routes to agent entrypoint function
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 4: Memory retrieval (t=30ms)
  AgentCore Memory retrieves relevant context:
  - SEMANTIC: "User had a defective product issue last time"
  - USER_PREFERENCE: "Prefers email confirmation after refunds"
  - EPISODIC: "2024-01-10: Contacted about order #3892, resolved"
  Injected into agent system prompt as context
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 5: Agent loop iteration 1 (t=50ms to t=1.2s)
  LLM call (Claude Haiku): "What info do I need?"
  → Decides to call: get_order_details(order_id="#4521")
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 6: Tool call via Gateway (t=1.2s to t=1.8s)
  Agent calls Gateway: get_order_details(order_id="#4521")
  Gateway checks: does StandardSupport have permission to call get_order_details?
  Cedar policy evaluation: ALLOW ✓
  Gateway routes to: Lambda function (mock order API)
  Result: {order: #4521, product: "Smart Watch", amount: $249.99, date: "2024-01-05"}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 7: Agent loop iteration 2 (t=1.8s to t=2.8s)
  LLM call (Claude Haiku): "I see the order. Should I process the refund?"
  → Decides to call: process_refund(order_id="#4521", amount=150)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 8: Policy enforcement (t=2.8s to t=2.82s)
  Agent calls Gateway: process_refund(order_id="#4521", amount=150)
  Gateway sends to Cedar Policy Engine:
    principal = user-rayudu (StandardSupport group)
    action = processRefund
    context = {amount: 150}
  
  Cedar evaluation:
    permit(StandardSupport, processRefund) when amount <= 100 → FALSE (150 > 100)
    permit(SeniorSupport, processRefund) when amount <= 500 → FALSE (not SeniorSupport)
  
  Result: DENY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 9: Agent handles denial (t=2.82s to t=3.8s)
  Agent receives: 403 Forbidden from Gateway
  LLM generates: "I can process refunds up to $100. For your $150 refund, 
  I'll need to escalate to a senior agent. Shall I do that for you?"
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 10: Response streams to user (t=3.8s to t=4.1s)
  SSE stream → user sees response token by token
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 11: Memory update (async, t=4.1s)
  Memory stores new episode:
  "2024-06-19: User requested $150 refund for order #4521. 
   StandardSupport limit exceeded. Escalation offered."
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 12: Observability (async, t=4.1s)
  CloudWatch receives full trace:
  invoke_agent (4.1s total, $0.003)
  ├── jwt_validation (5ms)
  ├── memory_retrieval (15ms)
  ├── model_call_1: haiku (1.15s, 840 tokens)
  ├── tool_call: get_order_details (600ms)
  ├── model_call_2: haiku (1.0s, 420 tokens)
  ├── tool_call: process_refund (20ms) → DENIED
  └── model_call_3: haiku (980ms, 380 tokens)
  
  Online evaluation (async):
  GoalSuccessRate: 0.7 (partial - escalation offered but not resolved)
  Helpfulness: 0.9 (clear explanation of limits)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## 23. Common Patterns and Anti-Patterns

### Pattern 1: Memory-Augmented Conversations

```python
# GOOD: Retrieve memories BEFORE building the prompt
@app.entrypoint
async def invoke(payload, context):
    user_id = context.get("user_id")
    query = payload.get("prompt")
    
    # Get relevant memories
    memories = memory_client.retrieve(
        actor_id=user_id,
        query=query,
        top_k=5
    )
    
    # Inject into agent context
    memory_context = "\n".join([f"- {m['content']}" for m in memories])
    
    agent = Agent(
        model=model,
        system_prompt=f"Context about this user:\n{memory_context}",
        tools=tools,
    )
    
    async for chunk in agent.stream_async(query):
        if "data" in chunk:
            yield chunk["data"]
```

### Pattern 2: Secure Tool Calls via Gateway

```python
# GOOD: All tool calls go through Gateway (centralized auth + logging)
from strands.tools.mcp import MCPClient

# Agent uses Gateway URL — never connects directly to tools
gateway_url = "https://gateway.bedrock-agentcore.us-east-1.amazonaws.com/mcp"

mcp_client = MCPClient(lambda: gateway_url)

agent = Agent(
    model=model,
    tools=[*mcp_client.list_tools()],  # All tools come from Gateway
    system_prompt="...",
)

# BAD: Direct connection to tools (bypasses governance)
# agent = Agent(tools=[direct_salesforce_client, direct_github_client])
```

### Pattern 3: Graceful Policy Denial Handling

```python
# GOOD: Handle 403 from Gateway gracefully
@tool
def process_refund(order_id: str, amount: float) -> str:
    """Process a customer refund."""
    try:
        result = gateway_client.call("process_refund", {
            "order_id": order_id,
            "amount": amount
        })
        return f"Refund of ${amount} processed for order {order_id}"
    
    except PermissionDeniedError as e:
        # Let the LLM handle this gracefully in the response
        return f"POLICY_DENIED: Refund of ${amount} exceeds your authorization limit. Escalation required."

# The LLM will then tell the user in a friendly way
# rather than crashing or returning a raw error
```

### Anti-Pattern 1: Storing Credentials in Agent Code

```python
# BAD: Credentials in agent code
GITHUB_TOKEN = "ghp_xxxxxxxxxxxx"
agent = Agent(tools=[GitHubTool(token=GITHUB_TOKEN)])

# GOOD: Use AgentCore Identity for credential management
# Credentials stored in AgentCore, agent gets a token at runtime
agentcore add credential --name GitHubToken --type api-key --api-key $GITHUB_TOKEN
# Agent code has no hardcoded credentials
```

### Anti-Pattern 2: Skipping Evaluation

```python
# BAD: Deploy and never check quality
agentcore deploy
# ← You have no idea if the agent is helping users

# GOOD: Enable continuous evaluation from day one
agentcore add online-eval \
  --name ProdEval \
  --runtime MyAgent \
  --evaluator Builtin.GoalSuccessRate Builtin.Helpfulness \
  --sampling-rate 100 \
  --enable-on-create
agentcore deploy
# ← Now you get quality scores for every session
```

---

## 24. Cheatsheet

### CLI Quick Reference

```bash
# Project lifecycle
agentcore create --name MyAgent --framework Strands --model-provider Bedrock --defaults
agentcore dev                               # Local development
agentcore dev "test prompt" --stream        # Non-interactive test
agentcore deploy                            # Deploy to AWS
agentcore status                            # Check deployment status
agentcore invoke "prompt" --stream          # Test deployed agent
agentcore logs                              # Stream live logs
agentcore traces list --limit 10            # Recent traces
agentcore remove all && agentcore deploy    # Teardown

# Add capabilities
agentcore add memory --name M --strategies SEMANTIC,USER_PREFERENCE --expiry 30
agentcore add gateway --name G --runtimes MyAgent
agentcore add credential --name K --type api-key --api-key $KEY
agentcore add evaluator --name E --type llm-as-a-judge
agentcore add online-eval --name OE --runtime MyAgent --evaluator Builtin.GoalSuccessRate \
  --sampling-rate 100 --enable-on-create

# Evaluation
agentcore run eval --runtime MyAgent --evaluator Builtin.GoalSuccessRate --session-id S
agentcore run batch-evaluation --runtime MyAgent --evaluator Builtin.GoalSuccessRate
agentcore run recommendation --runtime MyAgent --type system-prompt --evaluator Builtin.GoalSuccessRate
```

### Component Summary

| Component | What It Does | CLI Command | When to Use |
|-----------|-------------|-------------|-------------|
| **Runtime** | Hosts your agent code | `agentcore deploy` | Always — this is the base |
| **Harness** | Low-level isolated sessions | boto3 API | Custom sandbox needs |
| **Gateway** | Centralized tool hub (MCP) | `agentcore add gateway` | When sharing tools across teams |
| **Memory** | Cross-session memory | `agentcore add memory` | Personalized agents |
| **Identity** | Auth in + auth out | boto3 / CLI | User-facing agents |
| **Code Interpreter** | Safe Python sandbox | SDK `code_session()` | Agents that run code |
| **Browser** | Web navigation | SDK `BrowserTool()` | Web research/automation |
| **Observability** | Traces + metrics | Auto (enable Transaction Search) | Always |
| **Evaluation** | Quality scoring | `agentcore add evaluator` | Production agents |
| **Policy** | Cedar guardrails | `agentcore add policy` | Enterprise governance |
| **Registry** | Agent discovery | `agentcore add agent` | Multi-agent systems |

### Framework Comparison in AgentCore

| Framework | Best For | Key Class | Tool Definition |
|-----------|---------|-----------|----------------|
| **Strands** | Simple, clean agents; AWS-native | `strands.Agent` | `@tool` decorator |
| **LangGraph** | Complex stateful workflows | `StateGraph` | `@tool` from langchain |
| **CrewAI** | Role-based teams | `Crew` | Tools list per Agent |
| **OpenAI Agents SDK** | OpenAI-style tools | `Agent` | `function_tool` decorator |
| **Google ADK** | Google-native workflows | `GenericAgent` | Tool functions |

### Key Code Pattern — Minimal Agent

```python
from strands import Agent, tool
from bedrock_agentcore.runtime import BedrockAgentCoreApp

app = BedrockAgentCoreApp()

@tool
def my_tool(input: str) -> str:
    """Describe what this tool does and when to use it."""
    return f"Result for: {input}"

agent = Agent(
    model=load_model(),
    tools=[my_tool],
    system_prompt="You are a helpful assistant.",
)

@app.entrypoint
async def invoke(payload, context):
    async for event in agent.stream_async(payload.get("prompt")):
        if "data" in event and isinstance(event["data"], str):
            yield event["data"]

if __name__ == "__main__":
    app.run()
```

### Harness Key Pattern

```python
control = get_agentcore_control_client()
client  = get_agentcore_client()

# Create → Wait for READY → Invoke → ExecuteCommand → Delete
role_arn = create_harness_role()
harness_id = control.create_harness(harnessName="...", executionRoleArn=role_arn)["harness"]["harnessId"]
# wait for READY...

session_id = str(uuid.uuid4()).upper()
response = client.invoke_harness(
    harnessArn=harness_arn,
    runtimeSessionId=session_id,
    messages=[{"role": "user", "content": [{"text": "your prompt"}]}],
    model={"bedrockModelConfig": {"modelId": "global.anthropic.claude-haiku-4-5-20251001-v1:0"}},
)
# process response["stream"] events...

control.delete_harness(harnessId=harness_id)
```

---

## 25. Summary and Conclusion

### What Amazon Bedrock AgentCore Is

Amazon Bedrock AgentCore is AWS's answer to the question: *"I've built an AI agent — now how do I deploy it, secure it, monitor it, and operate it at scale without building all the plumbing myself?"*

It provides **10 managed components** that together form a complete agent operations platform:

```
DEPLOY:     Runtime     → Host any agent framework without building infrastructure
            Harness     → Isolated microVM sessions for direct AI execution

CONNECT:    Gateway     → Centralized, governed tool access via MCP
            Code Interp → Safe Python sandbox for agent-generated code
            Browser     → Web navigation capability

REMEMBER:   Memory      → Cross-session short-term and long-term memory

SECURE:     Identity    → JWT inbound auth + OAuth outbound auth
            Policy      → Cedar-based deterministic guardrails

IMPROVE:    Observability → OpenTelemetry traces in CloudWatch
            Evaluation  → LLM-as-judge quality scoring + A/B optimization

DISCOVER:   Registry    → Org-wide agent catalog for multi-agent discovery
```

### The Three Most Important Things to Learn First

1. **The AgentCore CLI workflow** — `create → dev → deploy → invoke` — this is the daily development loop for everything

2. **How BedrockAgentCoreApp wraps your agent** — understanding this one class shows you how AgentCore integrates with any framework

3. **The Runtime + Memory + Gateway combination** — these three components together give you 80% of what makes an agent production-ready

### Why AgentCore Matters for AI Engineers

Before AgentCore, building a production AI agent required:
- 2-4 weeks of infrastructure setup per agent
- Custom auth implementation per team
- Custom observability per team
- No centralized governance or policy

With AgentCore:
- Deploy in minutes with the CLI
- Auth, memory, observability, and policy built in
- Consistent patterns across every agent in your org
- One control plane for all agents

### What to Study Next

```
BEGINNER PATH:
  1. Follow 00-getting-started/README.md end-to-end
  2. Run the customer support agent locally and deployed
  3. Add memory with `agentcore add memory`
  4. Watch the traces in CloudWatch

INTERMEDIATE PATH:
  5. Study 01-features/01-harness for direct Harness API
  6. Set up Gateway with a Lambda backend tool
  7. Add Cedar policy to restrict what the agent can do
  8. Enable evaluation and check quality scores

ADVANCED PATH:
  9. Build a Blueprint (05-blueprints/)
  10. Implement multi-agent with the Registry
  11. Set up A/B testing with config bundles
  12. Complete all 13 workshops in order
```

### The Bottom Line

Amazon Bedrock AgentCore eliminates the infrastructure tax on AI agent development. By providing managed runtime, memory, auth, gateway, observability, evaluation, and policy — all through a single CLI and SDK — it lets you focus on what makes your agent unique: the tools, the prompts, and the business logic.

The `agentcore-samples-main` repository gives you working examples for every component, every framework, and every production pattern. Start with `00-getting-started/`, follow one path to deployment, then add components one at a time as your requirements grow.

---

*This explanation was written for complete beginners to Amazon Bedrock AgentCore. All code examples are drawn directly from the `agentcore-samples-main` repository. Follow the numbered sections in order for the clearest learning path.*
