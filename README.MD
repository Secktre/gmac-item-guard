# Enterprise Architecture Case Study: Asynchronous Multi-Agent Psychometric Validation Pipeline (PIG-VA)

An autonomous, non-blocking item generation and verification system engineered to mitigate content-bank exhaustion, logical hallucination vectors, and psychometric anti-bias regulatory compliance violations for high-stakes adaptive testing infrastructures.

---

## 📈 System Operational Dashboard Profile

The infrastructure logs system throughput, exact byte-pair token metrics, and operational expenditure overhead down to the fifth decimal place. A standard execution of a high-concurrency parameter batch yields the following telemetry:

```text
======================================================================
        SYSTEM PRODUCTION METRICS & VALIDATION REPORT DASHBOARD
======================================================================
🔹 Total Evaluated Item Assets Ingested : 25
   |-- APPROVED (Safe for Pool)        : 9
   |-- REJECTED_LOGIC (Failed Proof)  : 13
   |-- REJECTED_BIAS (Linguistic Drop) : 3
🔹 Total Clean Yield Efficiency Rate    : 36.00%
----------------------------------------------------------------------
💵 Total Consolidated LLM Financial Cost : $0.03598
📦 Total BPE Tokens Parsed (cl100k_base): 20,334 tokens
⚡ Average Asynchronous Node Latency     : 22.68 seconds
======================================================================
```

---

## 💼 Executive Overview & Engineering Context

In Computer Adaptive Testing (CAT) environments (such as the GMAT), item bank exhaustion demands a constant supply of psychometrically valid evaluation questions. Leveraging Generative AI to automate this asset generation introduces three core liabilities:
1. **The Structural Hallucination Paradox:** Foundation models routinely generate contextually dense scenarios where the underlying mathematical or verbal logic collapses, rendering the test question psychometrically invalid.
2. **Context-Prejudice Contamination:** Traditional verification structures leak the intended answer key into the grading prompt, causing the evaluator model to validate flawed items due to context bias.
3. **Socio-Demographic Parity Breaches:** Generative models introduce localized idioms, regional cultural variables, and socio-economic assumptions that violate international psychometric testing equity mandates.

### The Solution Strategy
This system implements an asynchronous, multi-agent pipeline that isolates content generation from validation via a **Double-Blind Reasoning Extraction** architecture. It integrates a stateful **Self-Healing Critique Loop** to programmatically repair broken items, while protecting the storage engine from write-collisions using a thread-safe **Background FIFO Ingestion Queue**.

---

## 🏗️ Architectural Core Paradigms

```text
  [Batch Job Parameter Matrix]
               │
               ▼
┌──────────────────────────────┐
│  1. Asynchronous Generator   │◄──────────────────────────────┐
└──────────────┬───────────────┘                               │
               │ (Raw Text Asset Draft)                        │
               ▼                                               │
┌──────────────────────────────┐                               │
│  2. Static Compliance Gate   │ (Regex Filter Match)           │
└──────────────┬───────────────┘                               │
               │ (Passes Local Dictionary)                     │
               ▼                                               │ (Self-Healing
┌──────────────────────────────┐                               │  Critique Loop)
│  3. Blind Solver-Verifier    │                               │
└──────────────┬───────────────┘                               │
               │ (Computes Isolated Proof String)              │
               ▼                                               │
┌──────────────────────────────┐                               │
│  4. Structured Extraction    │                               │
└──────────────┬───────────────┘                               │
               │                                               │
       [DOES KEY MATCH?] ──(MISMATCH / ATTEMPTS < 2)───────────┘
               │
           (MATCHES)
               ▼
┌──────────────────────────────┐
│  5. Unconstrained Auditor    │
└──────────────┬───────────────┘
               │ (Generates Linguistic Report)
               ▼
┌──────────────────────────────┐
│  6. Metadata Schema Parser   │
└──────────────┬───────────────┘
               │
       [IS CONTENT CLEAN?]
               │
           (APPROVED)
               ▼
┌──────────────────────────────┐
│ 7. In-Memory FIFO Write Queue│
└──────────────┬───────────────┘
               │ (Thread-Safe Hand-off)
               ▼
┌──────────────────────────────┐
│ 8. Dedicated Storage Worker  │ ──► [Persistent SQLite Storage]
└──────────────────────────────┘
```

### 1. Double-Blind Reasoning Extraction
Forcing a model to adhere to rigid JSON structures while simultaneously executing complex mathematical or verbal proofs causes **Structured Output Collapse**. Under tight schema constraints, a model concentrates its token budget on generating valid JSON tags, truncating or completely corrupting its logical reasoning text.

To eliminate this failure mode, this system decouples **Reasoning** from **Structuring**:
* **The Blind Reasoning Step:** The agent isolates the raw question text from all metadata and answer keys. Operating at a deterministic temperature ($T=0.0$), it utilizes its full context window to write a plain-text mathematical/verbal logic proof from scratch.
* **The Metadata Extraction Step:** A separate, downstream structured serialization interface parses the raw proof text, extracts the derived key, and verifies correctness programmatically outside the model context.

### 2. Multi-Pass Self-Healing Curation Loops
When the verification step exposes a logic or key mismatch, the pipeline does not abort execution or waste processing overhead. It extracts the raw reasoning text detailing *why* the question failed, captures the structural anomalies, and routes the payload back to the generation channel for a **Remediation Attempt**. This critique loop dynamically rebuilds the question text to reconcile its mathematical variables before declaring a terminal rejection state.

### 3. Thread-Safe Background Storage Ingestion
In a high-concurrency architecture running native asynchronous coroutines, multiple tasks completing simultaneously will attempt to commit metrics to the persistence engine at the exact same fraction of a second. Slamming an ACID-compliant engine like SQLite with concurrent disk writes triggers an immediate `OperationalError: database is locked` crash, dropping telemetry and corrupting the state.

This system isolates persistence logic using a **Threaded FIFO Producer-Consumer Pattern**:
* The asynchronous processing pipelines act as **Producers**, non-blockingly dropping completed data objects into a thread-safe `queue.Queue()`.
* An independent background thread acts as the **Consumer**, maintaining a single, continuous, isolated data connection, writing logs sequentially and safely without database locking risks.

---

## 📂 System Topography

```text
gmac-item-guard/
├── data/
│   └── item_bank.db          # Thread-safe database instance file
├── src/
│   ├── engine/
│   │   ├── __init__.py
│   │   ├── nodes.py          # Asynchronous multi-stage critique & execution logic
│   │   └── schemas.py        # Rigid Pydantic model validation data schemas
│   └── storage/
│       ├── __init__.py
│       └── item_db.py        # Queue-backed data ingestion engine worker
├── main.py                   # Master asynchronous runtime loop entryway
├── dashboard.py              # Operational analytics reporting panel
└── requirements.txt          # Explicit system workspace dependencies
```

---

## 📊 Relational Target Data Schema

The relational database layer maintains strict structural separation between operational item assets and validation metrics to preserve a pristine, queryable audit trail for system optimization loops:

### `item_bank` Table
Tracks core test-ready question profiles and consolidated operating expenditures:
```sql
CREATE TABLE item_bank (
    item_id TEXT PRIMARY KEY,
    timestamp TEXT NOT NULL,
    category TEXT NOT NULL,      -- Quant, Verbal, Data Insights
    difficulty TEXT NOT NULL,    -- Easy, Medium, Hard
    raw_question TEXT NOT NULL,  -- Reconciled prompt text asset
    intended_key TEXT NOT NULL,  -- Validated answer choice option
    final_status TEXT NOT NULL,  -- APPROVED, APPROVED_REMEDIATED, REJECTED_LOGIC, REJECTED_BIAS
    total_calculated_cost REAL NOT NULL
);
```

### `validation_telemetry` Table
Maintains pristine, raw, uncollapsed reasoning proofs and metadata tracking dimensions:
```sql
CREATE TABLE validation_telemetry (
    telemetry_id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id TEXT NOT NULL,
    solver_status TEXT NOT NULL,     -- MATCH, MISMATCH
    solver_rationale TEXT,           -- Untruncated, plain-text logical proof string
    bias_score REAL NOT NULL,        -- Strict float normalization between 0.0 and 1.0
    bias_rationale TEXT,             -- Explanatory linguistic analysis report
    generation_latency_ms INTEGER NOT NULL,
    input_tokens INTEGER NOT NULL,   -- Count verified via BPE tiktoken math
    output_tokens INTEGER NOT NULL,  -- Count verified via BPE tiktoken math
    FOREIGN KEY(item_id) REFERENCES item_bank(item_id)
);
```

---

## 🛠️ Environmental Deployment & Run Verification

Ensure a local instance of [Ollama](https://ollama.com/) is active inside your system daemon environment before launching the initialization pipeline script loops:

```bash
# 1. Fetch targeted localized open-weights reasoning model dependencies
ollama pull llama3

# 2. Establish isolated system virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\Activate.ps1

# 3. Apply explicit, production-grade library bindings
pip install -r requirements.txt
pip install tiktoken

# 4. Trigger the concurrent multi-agent batch curation pipeline
python main.py

# 5. Extract system performance metrics, yield efficiency, and financial profiles
python dashboard.py
```

---

## 💡 Engineering Defense (FAANG Architecture Review Readiness)

When cross-examined on system implementation choices during systemic reviews, this codebase anchors defenses on three foundational decisions:
* **Why `asyncio` over multi-threading for LLM nodes?** LLM orchestration is heavily bound by network I/O sockets waiting on responses from local or cloud daemon runtimes. Utilizing `asyncio.gather` avoids the thread context-switching overhead of the Python Global Interpreter Lock (GIL), allowing processing pathways to scale efficiently.
* **Why implement custom extraction nodes instead of standard structured outputs?** Small, edge-deployable open-weights systems ($8B$ parameters or lower) lack the attention weight density to balance formatting constraints with deep logical reasoning. Decoupling the reasoning phase ensures maximum accuracy, while the extraction pass handles structured mapping.
* **Why a background consumer queue for a local SQLite file?** It enforces a single point of entry for disk access. This isolates stateful database access paths, converting concurrent asynchronous tasks into predictable serial operations, preventing resource crashes entirely.