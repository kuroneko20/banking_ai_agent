# 🏦 Banking AI-Agent

Hệ thống AI Agent Workflow hỗ trợ khách hàng ngân hàng, xây dựng bằng **FastAPI**, **Pydantic** và **Ollama** (LLM chạy local).

---

## 🎬 Video Demo

[![▶ Xem Video Demo](https://img.shields.io/badge/▶%20Xem%20Video%20Demo-Google%20Drive-blue?style=for-the-badge&logo=googledrive)](https://drive.google.com/file/d/YOUR_FILE_ID/view)



---

## 📋 Tổng quan

Dự án triển khai một **Structured AI-Agent Workflow** (dạng state-machine) xử lý tin nhắn khách hàng qua 6 nodes chuyên biệt, mỗi node đảm nhận một bước trong pipeline hỗ trợ.

Hệ thống **không phải fully autonomous agent** — workflow minh bạch, có thể debug và audit toàn bộ từng bước xử lý.

---

## 🏗️ Kiến trúc hệ thống

```
Tin nhắn khách hàng
        │
        ▼
┌─────────────────────┐
│  Intent Detection   │  ← Phân loại ý định bằng keyword scoring
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  Priority / Risk    │  ← Đánh giá mức độ LOW / MEDIUM / HIGH
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  Policy Retrieval   │  ← Tra cứu FAQ + hướng dẫn xử lý
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  Draft Response     │  ← Gọi Ollama LLM sinh phản hồi nháp
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  Validation         │  ← Kiểm tra chất lượng phản hồi
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  Router / Escalation│  ← Quyết định: trả lời / hỏi thêm / escalate
└────────┬────────────┘
         │
         ▼
    Phản hồi cuối cùng
```

---

## 📂 Cấu trúc thư mục

```
banking_ai_agent/
│
├── README.md
├── requirements.txt
├── run.py                        # Entry point khởi động server
│
├── app/
│   ├── main.py                   # FastAPI app + routes
│   │
│   ├── core/
│   │   ├── settings.py           # Cấu hình qua biến môi trường
│   │   └── schemas.py            # Toàn bộ Pydantic schemas
│   │
│   ├── data/
│   │   └── policies.py           # Dữ liệu policy / FAQ tĩnh
│   │
│   ├── clients/
│   │   ├── base.py               # Abstract LLM client
│   │   └── ollama_client.py      # Async Ollama HTTP client
│   │
│   ├── nodes/
│   │   ├── intent_node.py        # Phân loại intent
│   │   ├── priority_node.py      # Đánh giá mức độ ưu tiên
│   │   ├── policy_node.py        # Truy xuất policy
│   │   ├── draft_node.py         # Sinh phản hồi nháp qua LLM
│   │   ├── validation_node.py    # Kiểm tra chất lượng phản hồi
│   │   └── router_node.py        # Quyết định routing / escalation
│   │
│   └── agent/
│       └── orchestrator.py       # Điều phối toàn bộ workflow
│
└── examples/
    └── sample_requests.json      # 12 tình huống mẫu
```

---

## ⚙️ Các Workflow Nodes

| Node | File | Chức năng |
|------|------|-----------|
| **Intent Detection** | `intent_node.py` | Phân loại ý định khách hàng bằng keyword scoring |
| **Priority / Risk** | `priority_node.py` | Xếp loại mức độ rủi ro LOW / MEDIUM / HIGH |
| **Policy Retrieval** | `policy_node.py` | Lấy FAQ + hướng dẫn xử lý theo intent |
| **Draft Response** | `draft_node.py` | Gọi Ollama LLM sinh phản hồi cho khách hàng |
| **Validation** | `validation_node.py` | Kiểm tra độ dài, confidence, policy match |
| **Router** | `router_node.py` | Quyết định: trả lời / hỏi thêm / escalate |

### Logic Routing

```
Priority HIGH             → escalate_to_human
Confidence thấp           → escalate_to_human
Validation thất bại       → ask_for_more_info  (nếu thiếu thông tin)
                          → escalate_to_human  (trường hợp khác)
Mặc định                  → reply_directly
```

---

## ☁️ Chạy trên Google Colab

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

### Cell 5 — Mở Pinggy tunnel

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

BASE_URL = "https://xxxx.run.pinggy-free.link"  # ← thay URL của bạn

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

BASE_URL = "https://xxxx.run.pinggy-free.link"  # ← thay URL của bạn

scenarios = [
    ("🔴 FRAUD",     "I was hacked! There are unauthorized charges on my account!"),
    ("🔴 BLOCKED",   "My account was blocked after a suspicious transfer"),
    ("🔴 LOST CARD", "I lost my debit card at the mall, please block it immediately"),
    ("🟡 TRANSFER",  "I sent $500 three days ago but receiver still has not received it"),
    ("🟡 REFUND",    "I returned a product 2 weeks ago but refund has not arrived"),
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

BASE_URL = "https://xxxx.run.pinggy-free.link"  # ← thay URL của bạn

req = urllib.request.Request(
    f"{BASE_URL}/agent/chat",
    data=json.dumps({"message": "My account was blocked after a suspicious transfer"}).encode(),
    headers={"Content-Type": "application/json"},
    method="POST"
)
with urllib.request.urlopen(req) as r:
    res = json.loads(r.read())

print("📊 WORKFLOW TRACE — 6 BƯỚC XỬ LÝ")
print("=" * 55)
for step in res['workflow_trace']:
    icon = "✅" if step['status'] == "success" else "❌"
    print(f"  Bước {step['step']}: {icon} {step['node']}")
    print(f"          → {step['summary']}")
    print(f"          ⏱  {step['latency_ms']}ms")
print("=" * 55)
print(f"  Tổng thời gian : {res['total_latency_ms']}ms")
print(f"\n💬 PHẢN HỒI CUỐI CÙNG:\n{res['final_response']}")
```

> ⚠️ **Lưu ý khi dùng Colab:**
> - Mỗi lần Colab **restart** phải chạy lại từ Cell 4
> - Pinggy URL **thay đổi** mỗi lần — cập nhật `BASE_URL` sau mỗi lần chạy Cell 5
> - Tunnel Pinggy miễn phí tồn tại **60 phút** — chạy lại Cell 5 nếu hết hạn
> - Không bấm **Stop** cell đang chạy server — FastAPI sẽ bị kill theo

---

## 🖥️ Chạy trên máy tính Local

> Yêu cầu: RAM ≥ 16GB, Python 3.11+

### 1. Clone repo

```bash
git clone https://github.com/kuroneko20/banking_ai_agent.git
cd banking_ai_agent
```

### 2. Tạo môi trường ảo

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
# Tải Ollama tại https://ollama.com
curl -fsSL https://ollama.com/install.sh | sh

# Tải model
ollama pull gpt-oss:20b
```

### 5. Khởi động server

```bash
python run.py
```

Truy cập tại:
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

**Response:**

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
    { "step": 1, "node": "IntentDetectionNode",  "status": "success", "latency_ms": 2.1,  "summary": "intent=blocked_account confidence=85%" },
    { "step": 2, "node": "PriorityRiskNode",      "status": "success", "latency_ms": 0.5,  "summary": "priority=high" },
    { "step": 3, "node": "PolicyRetrievalNode",   "status": "success", "latency_ms": 0.1,  "summary": "policy_found=True" },
    { "step": 4, "node": "DraftResponseNode",     "status": "success", "latency_ms": 30.2, "summary": "model=gpt-oss:20b" },
    { "step": 5, "node": "ValidationNode",        "status": "success", "latency_ms": 0.2,  "summary": "valid=True score=100%" },
    { "step": 6, "node": "RouterEscalationNode",  "status": "success", "latency_ms": 0.1,  "summary": "decision=escalate_to_human" }
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
# Tài khoản bị khóa
curl -X POST https://YOUR-PINGGY-URL/agent/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"My account was blocked after a transfer"}'

# Giao dịch đáng ngờ
curl -X POST https://YOUR-PINGGY-URL/agent/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"I see unauthorized charges, I think I was hacked!"}'

# Chuyển tiền thất bại
curl -X POST https://YOUR-PINGGY-URL/agent/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"I sent $500 three days ago but receiver did not get it"}'
```

---

## 📊 Các Intent được hỗ trợ

| Intent | Mô tả |
|--------|-------|
| `transfer_failed` | Chuyển tiền nhưng người nhận chưa nhận được |
| `refund_request` | Yêu cầu hoàn tiền |
| `blocked_account` | Tài khoản bị khóa / đóng băng |
| `lost_card` | Thẻ bị mất hoặc bị đánh cắp |
| `card_not_received` | Thẻ mới chưa được giao |
| `suspicious_transaction` | Giao dịch lạ / gian lận |
| `account_balance` | Tra cứu số dư |
| `loan_support` | Tư vấn vay vốn |
| `password_reset` | Quên / đổi mật khẩu |
| `login_issue` | Không đăng nhập được |
| `general_inquiry` | Câu hỏi chung về ngân hàng |

---

---

## 🔮 Cải tiến trong tương lai

- **Vector store** — thay policy tĩnh bằng semantic search (ChromaDB, Pinecone)
- **Conversation memory** — hỗ trợ hội thoại nhiều lượt với session state
- **LLM intent classification** — phân loại intent chính xác hơn qua LLM
- **Authentication** — API key / JWT cho môi trường production
- **Database logging** — lưu toàn bộ request và response
- **Streaming response** — stream output LLM qua Server-Sent Events
- **Human handoff** — kết nối hệ thống ticket thật (Zendesk, Freshdesk)
- **Metrics dashboard** — Prometheus + Grafana theo dõi latency và lỗi

---

## 🛠️ Công nghệ sử dụng

| Thành phần | Công nghệ |
|-----------|-----------|
| Web framework | FastAPI |
| Data validation | Pydantic v2 |
| ASGI server | Uvicorn |
| LLM backend | Ollama (local) |
| HTTP client | httpx (async) |
| Cấu hình | Pydantic Settings |
| Tunnel demo | Pinggy (miễn phí) |
| Ngôn ngữ | Python 3.11+ |