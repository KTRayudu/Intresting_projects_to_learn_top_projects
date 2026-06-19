# OpenClaw Mission Control — Complete Explanation Guide

> **Who this is for:** Beginners who want to understand how a production-grade operations platform for managing AI agents is built — covering governance, approval flows, and multi-team orchestration.

---

## Table of Contents

1. [What is OpenClaw Mission Control?](#what-is-openclaw)
2. [The Problem It Solves](#the-problem)
3. [Core Concepts](#core-concepts)
4. [Platform Architecture](#platform-architecture)
5. [The Backend — FastAPI + Python](#backend)
6. [The Frontend — Next.js](#frontend)
7. [Authentication Modes](#authentication)
8. [Key Features Deep Dive](#key-features)
9. [How to Deploy](#how-to-deploy)
10. [API Structure](#api-structure)
11. [Cheatsheet](#cheatsheet)
12. [Summary and Conclusion](#summary-and-conclusion)

---

## What is OpenClaw Mission Control?

OpenClaw Mission Control is a **centralized control plane** for managing AI agents across teams and organizations.

Think of it like this: **AWS Console is to cloud servers** as **OpenClaw Mission Control is to AI agents**.

When you run AI agents in production:
- You have many agents doing many things
- Teams need to collaborate on shared agent workflows
- Some actions need human approval before executing
- You need to audit what happened when something goes wrong
- You need to manage multiple execution environments (gateways)

Mission Control gives you **one place to do all of this**.

### What is "OpenClaw"?

OpenClaw appears to be an AI agent execution platform. Mission Control is the **operations layer on top** of it — the dashboard and control surface.

The name suggests a claw-like orchestration tool for grabbing and controlling multiple agent workstreams.

---

## The Problem It Solves

### Scenario: Without Mission Control

```
Team A is running agents on their own laptop
Team B is running agents on a cloud VM
Team C is using a third-party API

→ No visibility into what's running
→ No way to stop a runaway agent
→ No approval process for sensitive actions
→ No audit trail when something breaks
→ Three separate dashboards to check
```

### Scenario: With Mission Control

```
All teams connect their agents to Mission Control
→ One dashboard shows ALL running agents
→ Any team member can pause/stop any agent
→ Sensitive actions require approval before executing
→ Everything is logged with timestamps
→ One place to debug any incident
```

---

## Core Concepts

### Organization
The top-level container. A company or team namespace.

### Board Group
A collection of related boards. Think of it like a project folder.

### Board
A workspace for a set of related tasks. Like a Kanban board but for AI agent tasks.

### Task
A unit of work assigned to an agent. Can have states: pending, running, complete, failed, blocked (waiting for approval).

### Tag
Labels for organizing tasks (e.g., "high-priority", "needs-review", "production").

### Gateway
A connection to an execution environment where agents actually run. A gateway could be:
- A local machine
- A cloud VM
- A Kubernetes cluster
- A third-party API service

### Approval
Before a sensitive agent action executes, it enters an "approval pending" state. A human reviews it and approves or rejects it. Only then does the agent proceed.

### Activity Timeline
A chronological log of everything that happened: tasks created, agents started, approvals given, errors encountered.

---

## Platform Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     MISSION CONTROL UI                       │
│  (Next.js frontend running at http://localhost:3000)         │
├─────────────────────────────────────────────────────────────┤
│                     BACKEND API                              │
│  (FastAPI/Python running at http://localhost:8000)           │
│                                                              │
│  Endpoints:                                                  │
│  /api/organizations  /api/boards  /api/tasks  /api/gateways  │
│  /api/approvals      /api/activity  /api/agents              │
├──────────────────┬──────────────────────────────────────────┤
│  DATABASE        │  AUTHENTICATION                          │
│  (PostgreSQL via  │  Bearer token (local mode)              │
│   SQLAlchemy +    │  OR Clerk JWT (production mode)         │
│   Alembic)        │                                         │
└──────────────────┴──────────────────────────────────────────┘
```

### Docker Compose Services

```yaml
# compose.yml
services:
  backend:
    build: ./backend
    ports: ["8000:8000"]
    
  frontend:
    build: ./frontend  
    ports: ["3000:3000"]
    
  db:
    image: postgres:16
    volumes: [postgres_data:/var/lib/postgresql/data]
```

---

## The Backend: FastAPI + Python

### Technology Stack

| Tool | Purpose |
|------|---------|
| **FastAPI** | Python web framework for the REST API |
| **SQLAlchemy** | Python ORM (Object-Relational Mapper) for database operations |
| **Alembic** | Database migration management |
| **PostgreSQL** | Relational database for all data |
| **Pydantic** | Data validation (request/response schemas) |
| **UV** | Fast Python package manager (alternative to pip) |

### FastAPI Basics

FastAPI lets you define API endpoints with Python functions:

```python
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel

app = FastAPI()

class TaskCreate(BaseModel):
    title: str
    description: str
    board_id: int
    tags: list[str] = []

@app.post("/api/tasks", response_model=TaskResponse)
async def create_task(task: TaskCreate, db: Session = Depends(get_db)):
    # Validate → Create in DB → Return
    db_task = Task(**task.dict())
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task
```

FastAPI automatically:
- Validates input against `TaskCreate` schema
- Generates interactive API docs at `/docs`
- Returns proper HTTP error codes

### Database Models (SQLAlchemy)

```python
# models.py
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship

class Organization(Base):
    __tablename__ = "organizations"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    board_groups = relationship("BoardGroup", back_populates="organization")

class BoardGroup(Base):
    __tablename__ = "board_groups"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    organization_id = Column(Integer, ForeignKey("organizations.id"))
    organization = relationship("Organization", back_populates="board_groups")
    boards = relationship("Board", back_populates="board_group")

class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    status = Column(String, default="pending")
    board_id = Column(Integer, ForeignKey("boards.id"))
    approved_at = Column(DateTime, nullable=True)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=True)
```

### Database Migrations with Alembic

When your data models change, you need to update the database schema. Alembic does this safely:

```bash
# Create a migration
alembic revision --autogenerate -m "add approved_at to tasks"

# Apply migrations to database
alembic upgrade head

# Roll back if something breaks
alembic downgrade -1
```

Alembic creates numbered migration files that can be applied in order. This means you can update the database schema without losing data.

### The `/healthz` Endpoint

Every production service needs a health check:

```python
@app.get("/healthz")
async def health_check():
    # Check database connectivity
    try:
        db.execute("SELECT 1")
    except Exception:
        raise HTTPException(status_code=503, detail="Database unavailable")
    
    return {"status": "ok", "version": "1.0.0"}
```

Docker Compose uses this to restart the container if it becomes unhealthy.

---

## The Frontend: Next.js

### Why Next.js?

Next.js is a React framework that adds:
- **Server-side rendering** (pages load faster, better SEO)
- **API routes** (optional backend logic within the frontend)
- **File-based routing** (create `pages/boards.tsx` → accessible at `/boards`)
- **Image optimization** (automatic compression)

### Frontend Structure

```
frontend/
├── pages/               # Each file = one URL route
│   ├── index.tsx        # → /  (dashboard home)
│   ├── boards/
│   │   ├── index.tsx    # → /boards (list all boards)
│   │   └── [id].tsx     # → /boards/123 (specific board)
│   ├── tasks/
│   │   └── [id].tsx     # → /tasks/456
│   └── gateways/
│       └── index.tsx    # → /gateways
├── components/          # Reusable UI components
│   ├── TaskCard.tsx
│   ├── ApprovalModal.tsx
│   └── ActivityTimeline.tsx
└── lib/
    └── api.ts           # Functions to call the backend API
```

### API Communication

```typescript
// lib/api.ts
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export async function getTasks(boardId: number): Promise<Task[]> {
  const response = await fetch(`${API_URL}/api/tasks?board_id=${boardId}`, {
    headers: {
      'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
    }
  });
  
  if (!response.ok) throw new Error('Failed to fetch tasks');
  return response.json();
}
```

### The Environment Variable Pattern

```bash
# .env (backend)
DATABASE_URL=postgresql://user:password@localhost:5432/openclaw
LOCAL_AUTH_TOKEN=your-very-long-secure-token-here-at-least-50-chars

# frontend/.env (Next.js frontend)  
NEXT_PUBLIC_API_URL=http://localhost:8000
# NEXT_PUBLIC_ prefix = accessible in browser JavaScript
```

---

## Authentication Modes

### Mode 1: Local Auth (Default)

A **shared bearer token** — everyone who knows the token has full access.

```bash
# .env
AUTH_MODE=local
LOCAL_AUTH_TOKEN=abc123xyz789...  # Must be 50+ characters
```

When using the API:
```bash
curl http://localhost:8000/api/tasks \
  -H "Authorization: Bearer abc123xyz789..."
```

**Use for:** Self-hosted deployments, single-team use, internal tools.

**Security note:** Anyone with the token has full admin access. Keep it secret.

### Mode 2: Clerk JWT (Production)

**Clerk** is an authentication-as-a-service provider. Users log in with email/password or social login (Google, GitHub), and receive a JWT (JSON Web Token).

```bash
# .env
AUTH_MODE=clerk
CLERK_SECRET_KEY=sk_live_...
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_live_...
```

**Use for:** Multi-user deployments, when you need different users to have different access levels.

**How JWT works:**
```
1. User logs in → Clerk verifies credentials
2. Clerk issues JWT (signed token with user info inside)
3. Frontend includes JWT in every API request header
4. Backend verifies JWT signature using Clerk's public key
5. Backend extracts user ID and permissions from token
```

---

## Key Features Deep Dive

### 1. Work Orchestration

The hierarchical structure:
```
Organization
└── Board Group (project)
    └── Board (sprint or workflow)
        └── Task (unit of work)
            └── Tags (labels for filtering)
```

You can:
- Create tasks manually via UI
- Create tasks via API (for automation)
- View tasks in a Kanban-style view by status
- Filter tasks by tags, agent, status, date

### 2. Agent Lifecycle Management

Create an agent:
```http
POST /api/agents
{
  "name": "Data Analysis Agent",
  "gateway_id": 1,
  "capabilities": ["python", "data_analysis", "visualization"],
  "config": {
    "model": "gpt-4",
    "max_tokens": 4096
  }
}
```

Inspect an agent:
```http
GET /api/agents/123
{
  "id": 123,
  "name": "Data Analysis Agent",
  "status": "running",
  "current_task_id": 456,
  "tasks_completed": 47,
  "tasks_failed": 2,
  "created_at": "2024-01-15T10:00:00Z"
}
```

### 3. Approval-Driven Governance

This is the most important production safety feature.

**How approvals work:**

```
Agent wants to execute: "DELETE all rows from customers table WHERE last_login < 2020"
                              ↓
This action is flagged as "high risk" (database deletion)
                              ↓
Task status → "approval_pending"
                              ↓
Team lead receives notification: "Action needs approval"
                              ↓
Team lead reviews: "This looks like a legitimate cleanup"
                              ↓
Team lead clicks "Approve"
                              ↓
Task status → "running"
                              ↓
Agent executes the deletion
```

**Without approval gates:** Agents can do anything autonomously, including destructive operations.
**With approval gates:** Humans stay in the loop for sensitive operations.

### 4. Gateway Management

A gateway is a connection to an execution environment:

```
┌─────────────────────┐     ┌─────────────────────┐
│  Mission Control    │────▶│  Gateway (local PC)  │
│  (cloud)            │     │  Running on port 8888│
└─────────────────────┘     └─────────────────────┘

┌─────────────────────┐     ┌─────────────────────┐
│  Mission Control    │────▶│  Gateway (AWS EC2)   │
│  (cloud)            │     │  Running on EC2      │
└─────────────────────┘     └─────────────────────┘
```

Mission Control can orchestrate agents running in multiple different environments simultaneously through their gateways.

The WebSocket-based gateway protocol (`docs/openclaw_gateway_ws.md`) allows real-time bidirectional communication between Mission Control and execution environments.

### 5. Activity Timeline

Every significant event is logged:

```
2024-01-15 10:30:01  Task "Analyze Q4 sales" created by user@company.com
2024-01-15 10:30:05  Agent "Data Analysis Agent" assigned to task
2024-01-15 10:30:07  Agent started task execution
2024-01-15 10:32:15  Agent requested approval: "Delete old records?"
2024-01-15 10:34:00  manager@company.com approved the request
2024-01-15 10:34:02  Agent executed approved action
2024-01-15 10:35:40  Task completed successfully
```

Use cases:
- **Debugging:** "What happened at 10:32? Why did the agent stop?"
- **Compliance:** "Show me all deletions that happened in January"
- **Accountability:** "Who approved the deletion of 10,000 records?"

### 6. API-First Model

Everything in the UI can also be done via API:

```bash
# Create a task via API (for automation/CI integration)
curl -X POST http://localhost:8000/api/tasks \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Deploy new model version",
    "board_id": 5,
    "tags": ["deployment", "ml-ops"],
    "agent_id": 3
  }'

# Check task status
curl http://localhost:8000/api/tasks/789 \
  -H "Authorization: Bearer TOKEN"

# Approve a pending action
curl -X POST http://localhost:8000/api/approvals/123/approve \
  -H "Authorization: Bearer TOKEN"
```

This means Mission Control can be integrated into CI/CD pipelines, monitoring systems, or other tools.

---

## How to Deploy

### Quick Start (One Command)

```bash
curl -fsSL https://raw.githubusercontent.com/abhi1693/openclaw-mission-control/master/install.sh | bash
```

The installer asks a few questions and sets everything up automatically.

### Manual Docker Deployment

```bash
# 1. Clone repo
git clone https://github.com/abhi1693/openclaw-mission-control.git
cd openclaw-mission-control

# 2. Configure environment
cp .env.example .env
# Edit .env:
# - Set LOCAL_AUTH_TOKEN (50+ character secret)
# - Set BASE_URL if not using localhost:8000

# 3. Start all services
docker compose -f compose.yml --env-file .env up -d --build

# 4. Verify
curl http://localhost:8000/healthz  # Should return {"status": "ok"}
# Open http://localhost:3000 in browser
```

### Environment Variables Reference

| Variable | Required | Default | Purpose |
|----------|----------|---------|---------|
| `AUTH_MODE` | Yes | `local` | `local` or `clerk` |
| `LOCAL_AUTH_TOKEN` | Yes (local mode) | - | Shared access token |
| `DATABASE_URL` | Yes | - | PostgreSQL connection string |
| `BASE_URL` | No | `http://localhost:8000` | Public backend URL |
| `NEXT_PUBLIC_API_URL` | No | `auto` | Frontend → backend URL |
| `CLERK_SECRET_KEY` | Yes (clerk mode) | - | Clerk authentication |

### Updating

```bash
git pull
docker compose -f compose.yml --env-file .env up -d --build --force-recreate
```

### Clean Rebuild (When Things Break)

```bash
docker compose -f compose.yml --env-file .env build --no-cache --pull
docker compose -f compose.yml --env-file .env up -d --force-recreate
```

---

## API Structure

### Core Resource Endpoints

```
Organizations:
  GET    /api/organizations          → List all organizations
  POST   /api/organizations          → Create organization
  GET    /api/organizations/{id}     → Get specific org
  PUT    /api/organizations/{id}     → Update org
  DELETE /api/organizations/{id}     → Delete org

Board Groups:
  GET    /api/board-groups           → List board groups
  POST   /api/board-groups           → Create board group
  GET    /api/board-groups/{id}      → Get specific board group

Boards:
  GET    /api/boards                 → List boards
  POST   /api/boards                 → Create board
  GET    /api/boards/{id}            → Get board with tasks

Tasks:
  GET    /api/tasks                  → List tasks (with filters)
  POST   /api/tasks                  → Create task
  GET    /api/tasks/{id}             → Get task
  PUT    /api/tasks/{id}             → Update task
  DELETE /api/tasks/{id}             → Delete task
  POST   /api/tasks/{id}/start       → Start task (assign to agent)
  POST   /api/tasks/{id}/complete    → Mark task complete

Agents:
  GET    /api/agents                 → List agents
  POST   /api/agents                 → Register agent
  GET    /api/agents/{id}            → Get agent details
  DELETE /api/agents/{id}            → Remove agent

Gateways:
  GET    /api/gateways               → List gateways
  POST   /api/gateways               → Connect gateway
  DELETE /api/gateways/{id}          → Disconnect gateway

Approvals:
  GET    /api/approvals              → List pending approvals
  POST   /api/approvals/{id}/approve → Approve an action
  POST   /api/approvals/{id}/reject  → Reject an action

Activity:
  GET    /api/activity               → Get timeline (with filters)

Health:
  GET    /healthz                    → Service health check
```

---

## Cheatsheet

### Quick Command Reference

```bash
# Start
docker compose -f compose.yml --env-file .env up -d --build

# Stop
docker compose -f compose.yml --env-file .env down

# View logs
docker compose -f compose.yml --env-file .env logs -f backend
docker compose -f compose.yml --env-file .env logs -f frontend

# Restart single service
docker compose -f compose.yml --env-file .env restart backend

# Access URLs
# UI:          http://localhost:3000
# API docs:    http://localhost:8000/docs
# Health:      http://localhost:8000/healthz
```

### Key Concepts Summary

| Concept | What It Is | Analogy |
|---------|-----------|---------|
| Organization | Top-level container | A company |
| Board Group | Collection of boards | A project folder |
| Board | Workspace for tasks | A Kanban board |
| Task | Unit of work | A ticket/card |
| Agent | AI that does work | An automated worker |
| Gateway | Connection to execution environment | A VPN to a server |
| Approval | Human review gate | Sign-off requirement |
| Activity | Event log | An audit trail |

### The Governance Flow

```
Create Task → Assign Agent → Agent Requests Approval → Human Reviews
    ↓              ↓                   ↓                      ↓
 Pending       Running           Approval Pending        Approved / Rejected
                                                              ↓          ↓
                                                           Continues   Blocked
```

---

## Summary and Conclusion

### What OpenClaw Mission Control Demonstrates

Mission Control is a production-grade example of **AI governance infrastructure** — the systems that make AI agents safe and manageable when used by teams and organizations.

The key ideas it implements:

1. **Centralized visibility** — See all agents across all environments in one place
2. **Approval gates** — Human oversight for sensitive AI actions
3. **Audit trail** — Complete history of who did what and when
4. **Gateway abstraction** — Manage agents in multiple execution environments
5. **API-first** — Both UI and automation use the same API

### Why This Matters for AI Safety

As AI agents become more capable and widespread, governance becomes critical:
- Agents can make mistakes with real-world consequences
- Multiple agents can conflict with each other
- Regulatory compliance requires audit trails
- Organizations need human control points

Mission Control provides the infrastructure for this kind of responsible AI deployment.

### What Beginners Can Learn

Even if you don't deploy Mission Control in production, studying this project teaches:
- **Full-stack web development** — FastAPI backend + Next.js frontend + PostgreSQL database
- **Docker and Docker Compose** — Multi-service deployment
- **REST API design** — Clean, consistent endpoint structure
- **Authentication patterns** — Both simple (bearer token) and production (JWT/Clerk)
- **Database migrations** — How to evolve your schema safely with Alembic
- **Production deployment patterns** — Environment variables, health checks, clean rebuilds

### The Bottom Line

OpenClaw Mission Control shows what happens **after** you build AI agents. The agent code is only half the work. The other half is:
- Running them reliably
- Making them safe for team use
- Giving humans appropriate oversight
- Maintaining accountability for automated actions

This is the infrastructure layer that most AI tutorials skip but every production deployment needs.

---

*This guide explains OpenClaw Mission Control from first principles for beginners who are new to both AI agent operations and full-stack web development.*
