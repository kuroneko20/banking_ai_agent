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
banking_ai_agent/
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

## ☁️ Chạy trên Google Colab (Khuyến nghị)

> Mở [Google Colab](https://colab.research.google.com) và chạy từng cell theo thứ tự dưới đây.

### Cell 1 — Clone repo

```python
!git clone https://github.com/kuroneko20/banking_ai_agent.git
!ls banking_ai_agent/
```

### Cell 2 — Cài dependencies

```python
!pip install -r banking_ai_agent/requirements.txt
```

### Cell 3 — Cài zstd và Ollama

```python
!apt-get install -y zstd
!curl -fsSL https://ollama.com/install.sh | sh
```

### Cell 4 — Khởi động Ollama + FastAPI

```python
import subprocess, time

# 1. Khởi động Ollama
subprocess.Popen(["ollama", "serve"],
                 stdout=subprocess.DEVNULL,
                 stderr=subprocess.DEVNULL)
time.sleep(5)
print("✅ Ollama started")

# 2. Khởi động FastAPI
server = subprocess.Popen(
    ["python", "run.py"],
    cwd="/content/banking_ai_agent",
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT
)
time.sleep(4)

for _ in range(10):
    line = server.stdout.readline().decode(errors="ignore").strip()
    if line: print(line)
```

Kết quả mong đợi:
```
✅ Ollama started
✅ Ollama is reachable at http://localhost:11434
INFO: Uvicorn running on http://0.0.0.0:8000
```

### Cell 5 — Mở Pinggy tunnel (expose ra internet)

```python
import subprocess, threading, time

output_lines = []
def read_output(proc):
    for line in proc.stdout:
        output_lines.append(line.decode(errors="ignore").strip())

tunnel = subprocess.Popen([
    "ssh", "-p", "443", "-R", "0:localhost:8000",
    "-o", "StrictHostKeyChecking=no",
    "-o", "ServerAliveInterval=30",
    "a.pinggy.io"
], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

threading.Thread(target=read_output, args=(tunnel,), daemon=True).start()
time.sleep(6)

for line in output_lines:
    print(line)
```

Kết quả mong đợi:
```
http://xxxx-34-142-211-236.run.pinggy-free.link
https://xxxx-34-142-211-236.run.pinggy-free.link   ← dùng cái này
```

### Cell 6 — Test API

```python
import urllib.request, json

BASE_URL = "https://xxxx-34-142-211-236.run.pinggy-free.link"  # ← thay URL của bạn

# Health check
with urllib.request.urlopen(f"{BASE_URL}/health") as r:
    print("Health:", json.loads(r.read()))

# Chat test
req = urllib.request.Request(
    f"{BASE_URL}/agent/chat",
    data=json.dumps({"message": "My account was blocked after a transfer"}).encode(),
    headers={"Content-Type": "application/json"},
    method="POST"
)
with urllib.request.urlopen(req) as r:
    res = json.loads(r.read())
    print("Intent:  ", res["intent_result"]["intent"])
    print("Priority:", res["priority_result"]["priority"])
    print("Routing: ", res["routing_decision"])
    print("Response:", res["final_response"])
```

### Cell 7 — Demo đầy đủ tất cả scenarios

```python
import urllib.request, json

BASE_URL = "https://xxxx-34-142-211-236.run.pinggy-free.link"  # ← thay URL của bạn

scenarios = [
    ("🔴 FRAUD",     "I was hacked! There are unauthorized charges on my account!"),
    ("🔴 BLOCKED",   "My account was blocked after a suspicious transfer"),
    ("🔴 LOST CARD", "I lost my debit card at the mall, please block it immediately"),
    ("🟡 TRANSFER",  "I sent $500 three days ago but receiver still hasn't received it"),
    ("🟡 REFUND",    "I returned a product 2 weeks ago but refund hasn't arrived"),
    ("🟢 BALANCE",   "What is my current account balance?"),
    ("🟢 PASSWORD",  "I forgot my password and the reset link is not working"),
    ("🟢 LOAN",      "I want to apply for a personal loan of $10,000"),
]

print("╔══════════════════════════════════════════════════════════════╗")
print("║           🏦  BANKING AI-AGENT — DEMO                       ║")
print("╚══════════════════════════════════════════════════════════════╝")

for label, msg in scenarios:
    req = urllib.request.Request(
        f"{BASE_URL}/agent/chat",
        data=json.dumps({"message": msg}).encode(),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req) as r:
        res = json.loads(r.read())

    print(f"\n{label}")
    print(f"  📨 Message  : {msg[:55]}")
    print(f"  🎯 Intent   : {res['intent_result']['intent']} ({res['intent_result']['confidence']:.0%})")
    print(f"  ⚡ Priority  : {res['priority_result']['priority'].upper()}")
    print(f"  🔀 Routing  : {res['routing_decision']}")
    print(f"  💬 Response : {res['final_response'][:80]}...")
    print(f"  ⏱️  Latency  : {res['total_latency_ms']}ms")
    print("  " + "─" * 60)
```

### Cell 8 — Hiển thị Workflow Trace từng bước

```python
import urllib.request, json

BASE_URL = "https://xxxx-34-142-211-236.run.pinggy-free.link"  # ← thay URL của bạn

req = urllib.request.Request(
    f"{BASE_URL}/agent/chat",
    data=json.dumps({"message": "My account was blocked after a suspicious transfer"}).encode(),
    headers={"Content-Type": "application/json"},
    method="POST"
)
with urllib.request.urlopen(req) as r:
    res = json.loads(r.read())

print("📊 WORKFLOW TRACE — 6 STEPS")
print("=" * 55)
for step in res['workflow_trace']:
    icon = "✅" if step['status'] == "success" else "❌"
    print(f"  Step {step['step']}: {icon} {step['node']}")
    print(f"           → {step['summary']}")
    print(f"           ⏱  {step['latency_ms']}ms")
print("=" * 55)
print(f"  Total latency : {res['total_latency_ms']}ms")
print(f"\n💬 FINAL RESPONSE:\n{res['final_response']}")
```

> ⚠️ **Lưu ý khi dùng Colab:**
> - Mỗi lần Colab **restart** phải chạy lại từ Cell 4
> - Pinggy URL **thay đổi** mỗi lần — cập nhật `BASE_URL` sau mỗi lần chạy Cell 5
> - Tunnel Pinggy miễn phí tồn tại **60 phút** — chạy lại Cell 5 nếu hết hạn
> - Không bấm **Stop** cell đang chạy server — FastAPI sẽ bị kill

---

## 🖥️ Chạy trên Local (máy tính)

> Yêu cầu: RAM ≥ 16GB, Python 3.11+

### 1. Clone repo

```bash
git clone https://github.com/kuroneko20/banking_ai_agent.git
cd banking_ai_agent
```

### 2. Tạo virtual environment

```bash
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
```

### 3. Cài dependencies

```bash
pip install -r requirements.txt
```

### 4. Cài và chạy Ollama

```bash
# Cài Ollama tại https://ollama.com
curl -fsSL https://ollama.com/install.sh | sh

# Pull model
ollama pull gpt-oss:20b
```

### 5. Chạy server

```bash
python run.py
```

Server chạy tại:
- **API**: `http://localhost:8000`
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

---

## 🔌 API Reference

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
    "confidence": 0.85
  },
  "priority_result": {
    "priority": "high",
    "reason": "Intent 'blocked_account' is inherently high-risk"
  },
  "workflow_trace": [
    { "step": 1, "node": "IntentDetectionNode", "status": "success", "latency_ms": 2.1, "summary": "intent=blocked_account confidence=85%" },
    { "step": 2, "node": "PriorityRiskNode", "status": "success", "latency_ms": 0.5, "summary": "priority=high" },
    { "step": 3, "node": "PolicyRetrievalNode", "status": "success", "latency_ms": 0.1, "summary": "policy_found=True" },
    { "step": 4, "node": "DraftResponseNode", "status": "success", "latency_ms": 30.2, "summary": "model=gpt-oss:20b" },
    { "step": 5, "node": "ValidationNode", "status": "success", "latency_ms": 0.2, "summary": "valid=True score=100%" },
    { "step": 6, "node": "RouterEscalationNode", "status": "success", "latency_ms": 0.1, "summary": "decision=escalate_to_human" }
  ],
  "total_latency_ms": 35.2
}
```

### GET `/health`

```json
{
  "status": "healthy",
  "ollama": "connected",
  "model": "gpt-oss:20b"
}
```

---

## 🧪 Test bằng cURL

```bash
# Blocked account
curl -X POST https://YOUR-PINGGY-URL/agent/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"My account was blocked after a transfer"}'

# Suspicious transaction
curl -X POST https://YOUR-PINGGY-URL/agent/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"I see unauthorized charges, I think I was hacked!"}'

# Transfer failed
curl -X POST https://YOUR-PINGGY-URL/agent/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"I sent $500 three days ago but receiver did not get it"}'
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

- **Vector store** — replace static policies with semantic search (ChromaDB, Pinecone)
- **Conversation memory** — multi-turn dialogue with session state
- **LLM intent classification** — higher-accuracy intent detection via LLM
- **Authentication** — API key / JWT for production use
- **Database logging** — persist all requests and responses
- **Streaming responses** — stream LLM output via Server-Sent Events
- **Human handoff** — connect to ticketing system (Zendesk, Freshdesk)
- **Metrics dashboard** — Prometheus + Grafana for monitoring

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
| Tunnel (demo) | Pinggy (free) |
| Language | Python 3.11+ |