# 🏦 Banking AI-Agent

A production-style AI Agent Workflow for banking customer support, built with **FastAPI**, **Pydantic**, and **Ollama** (local LLM).

---

## 📋 Project Overview

This project implements a **structured AI-Agent Workflow** (state-machine style) that processes customer messages through a series of specialised nodes, each responsible for one step of the support pipeline.

The system is **not a fully autonomous agent** — it is a transparent, debuggable, and auditable workflow where every decision is logged and traceable.

---

## 🏗️ Architecture

```
Customer Message
        │
        ▼
┌─────────────────────┐
│  Intent Detection   │  ← Rule-based + keyword scoring
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  Priority / Risk    │  ← Classifies LOW / MEDIUM / HIGH
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  Policy Retrieval   │  ← Looks up FAQ + resolution guideline
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  Draft Response     │  ← Calls Ollama LLM with prompt engineering
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  Validation         │  ← Quality checks on the draft
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  Router / Escalation│  ← reply_directly | ask_more_info | escalate
└────────┬────────────┘
         │
         ▼
    Final Response
```

---

## 📂 Folder Structure

```
project/
│
├── README.md
├── requirements.txt
├── run.py                        # Server entry point
│
├── app/
│   ├── main.py                   # FastAPI app + routes
│   │
│   ├── core/
│   │   ├── settings.py           # Pydantic Settings (env vars)
│   │   └── schemas.py            # All Pydantic models / schemas
│   │
│   ├── data/
│   │   └── policies.py           # Static policy / FAQ data
│   │
│   ├── clients/
│   │   ├── base.py               # Abstract LLM client
│   │   └── ollama_client.py      # Async Ollama HTTP client
│   │
│   ├── nodes/
│   │   ├── intent_node.py        # Intent detection
│   │   ├── priority_node.py      # Risk / priority scoring
│   │   ├── policy_node.py        # Policy retrieval
│   │   ├── draft_node.py         # LLM draft generation
│   │   ├── validation_node.py    # Response quality checks
│   │   └── router_node.py        # Routing / escalation
│   │
│   └── agent/
│       └── orchestrator.py       # Workflow coordinator
│
└── examples/
    └── sample_requests.json      # 12 test scenarios
```

---

## ⚙️ Workflow Nodes

| Node | File | Responsibility |
|------|------|----------------|
| **Intent Detection** | `intent_node.py` | Classifies the customer's intent using keyword scoring |
| **Priority / Risk** | `priority_node.py` | Assigns LOW / MEDIUM / HIGH risk level |
| **Policy Retrieval** | `policy_node.py` | Fetches FAQ + resolution guideline for the intent |
| **Draft Response** | `draft_node.py` | Calls Ollama LLM to generate a customer-facing draft |
| **Validation** | `validation_node.py` | Quality-checks the draft (length, confidence, policy match) |
| **Router** | `router_node.py` | Decides final action: reply / ask more / escalate |

### Routing Logic

```
HIGH priority           → escalate_to_human
Low intent confidence   → escalate_to_human
Validation failed       → ask_for_more_info  (if missing info exists)
                        → escalate_to_human  (otherwise)
Default                 → reply_directly
```

---

## 🚀 Installation

### 1. Clone / set up the project

```bash
git clone <repo-url>
cd project
```

### 2. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up Ollama

```bash
# Install Ollama (https://ollama.com)
curl -fsSL https://ollama.com/install.sh | sh

# Pull the model
ollama pull gpt-oss:20b

# Ollama runs automatically on http://localhost:11434
```

### 5. (Optional) Configure environment variables

Create a `.env` file in the project root:

```env
OLLAMA_BASE_URL=http://localhost:11434
MODEL_NAME=gpt-oss:20b
API_HOST=0.0.0.0
API_PORT=8000
LOG_LEVEL=INFO
MIN_INTENT_CONFIDENCE=0.4
MIN_VALIDATION_SCORE=0.5
```

---

## ▶️ Running the Server

```bash
python run.py
```

The API will be available at:
- **API**: `http://localhost:8000`
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

---

## 🔌 API Usage

### POST `/agent/chat`

**Request:**

```json
{
  "message": "My account was blocked after a transfer",
  "session_id": "optional-session-id"
}
```

**Response (abbreviated):**

```json
{
  "request_id": "uuid",
  "timestamp": "2024-01-15T10:30:00",
  "original_message": "My account was blocked after a transfer",
  "final_response": "Thank you for contacting us...",
  "routing_decision": "escalate_to_human",
  "intent_result": {
    "intent": "blocked_account",
    "confidence": 0.85,
    "extracted_entities": {}
  },
  "priority_result": {
    "priority": "high",
    "reason": "Intent 'blocked_account' is inherently high-risk"
  },
  "workflow_trace": [
    { "step": 1, "node": "IntentDetectionNode", "status": "success", "latency_ms": 2.1, "summary": "intent=blocked_account confidence=85%" },
    ...
  ],
  "total_latency_ms": 1234.5
}
```

### GET `/health`

Returns Ollama connectivity status:

```json
{
  "status": "healthy",
  "ollama": "connected",
  "model": "gpt-oss:20b"
}
```

---

## 🧪 Example Requests

Test with cURL:

```bash
# Blocked account
curl -X POST http://localhost:8000/agent/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"My account was blocked after a transfer"}'

# Suspicious transaction
curl -X POST http://localhost:8000/agent/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"I see unauthorized charges on my account, I think I was hacked!"}'

# Transfer failed
curl -X POST http://localhost:8000/agent/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"I sent $500 three days ago but the receiver still hasn'\''t received it"}'

# Password reset
curl -X POST http://localhost:8000/agent/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"I forgot my password and the reset link is not working"}'
```

All 12 sample scenarios are in `examples/sample_requests.json`.

---

## 🌐 Expose with Pinggy (for demo)

```bash
# Install pinggy and forward port 8000
ssh -p 443 -R0:localhost:8000 a.pinggy.io

# You'll get a public URL like:
# https://abcd1234.a.pinggy.link
```

---

## 📊 Supported Banking Intents

| Intent | Description |
|--------|-------------|
| `transfer_failed` | Money sent but not received |
| `refund_request` | Customer wants money back |
| `blocked_account` | Account locked / frozen |
| `lost_card` | Debit/credit card lost or stolen |
| `card_not_received` | New card hasn't arrived |
| `suspicious_transaction` | Unauthorised charges / fraud |
| `account_balance` | Balance inquiry |
| `loan_support` | Loan enquiries |
| `password_reset` | Forgot / change password |
| `login_issue` | Cannot log in |
| `general_inquiry` | General banking questions |

---

## 🔮 Future Improvements

- **Vector store integration** — replace static policies with semantic search (e.g., ChromaDB, Pinecone)
- **Conversation memory** — multi-turn dialogue with session state
- **LLM intent classification** — use the LLM for higher-accuracy intent detection
- **Authentication** — API key / JWT for production use
- **Database logging** — persist all requests and responses
- **Retry mechanism** — automatic retry on Ollama timeout
- **Streaming responses** — stream LLM output via Server-Sent Events
- **Human handoff integration** — connect to a real ticketing system (Zendesk, Freshdesk)
- **Metrics dashboard** — Prometheus + Grafana for latency and error tracking

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| Web framework | FastAPI |
| Data validation | Pydantic v2 |
| ASGI server | Uvicorn |
| LLM backend | Ollama (local) |
| HTTP client | httpx (async) |
| Configuration | Pydantic Settings |
| Language | Python 3.11+ |
