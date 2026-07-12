# Case Study: How I Engineered an Asynchronous Multi-Agent Psychometric Validation Pipeline (PIG-VA)

I built this system to solve a critical operational bottleneck in Computer Adaptive Testing (CAT) infrastructures: the high failure rate, logical inconsistencies, and socio-economic biases found in automated test-item generation. 

Instead of writing a basic wrapper script that passively queries an LLM and hopes for the best, **I architected a production-ready validation engine** that aggressively filters out flawed assets, handles automated remediation through self-healing loops, and protects the underlying storage layers using thread-safe asynchronous concurrency.

---

## 📈 System Performance & Yield Analytics

I integrated full instrumentation into this system to capture real-time execution throughput, exact byte-pair token metrics, and operational expenditure overhead down to the fifth decimal place. Here is the operational signature of a 25-item high-concurrency evaluation run:

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

## 🧠 The Engineering Problems I Solved

When automating high-stakes test question generation (like GMAT assets) using Generative AI, I encountered three core engineering failure vectors that I had to design systemic guardrails against:

1. **The Structural Hallucination Paradox:** Open-weights foundation models frequently generate complex scenarios where the underlying mathematical or verbal logic collapses, rendering the asset psychometrically invalid.
2. **Context-Prejudice Contamination:** Most baseline architectures leak the target answer key directly into the verification prompt, causing the evaluator agent to experience context bias and passively validate a broken question.
3. **Socio-Demographic Parity Breaches:** Generative systems inherently output localized idioms and regional cultural context that explicitly violate international psychometric testing equity mandates.

---

## 🏗️ Architectural Core Paradigms

This is the system topology I designed to decouple generation from evaluation and protect transaction pipelines:

```text
  [Batch Job Parameter Matrix]
               │
               ▼
┌──────────────────────────────┐
│       I. Asynchronous        │◄──────────────────────────────┐
│          Generator           │                               │
└──────────────┬───────────────┘                               │
               │ (Raw Text Asset Draft)                        │
               ▼                                               │
┌──────────────────────────────┐                               │
│    II. Static Compliance     │ (Regex Filter Match)          │
│             Gate             │                               │
└──────────────┬───────────────┘                               │
               │ (Passes Local Dictionary)                     │
               ▼                                               │ (My Self-Healing
┌──────────────────────────────┐                               │  Critique Loop)
│  III. Blind Solver-Verifier  │                               │
└──────────────┬───────────────┘                               │
               │ (Computes Isolated Proof String)              │
               ▼                                               │
┌──────────────────────────────┐                               │
│   IV. Structured Extraction  │                               │
└──────────────┬───────────────┘                               │
               │                                               │
       [DOES KEY MATCH?] ──(MISMATCH / ATTEMPTS < 2)───────────┘
               │
           (MATCHES)
               ▼
┌──────────────────────────────┐
│    V. Unconstrained Auditor  │
└──────────────┬───────────────┘
               │ (Generates Linguistic Report)
               ▼
┌──────────────────────────────┐
│  VI. Metadata Schema Parser  │
└──────────────┬───────────────┘
               │
       [IS CONTENT CLEAN?]
               │
           (APPROVED)
               ▼
┌──────────────────────────────┐
│ VII. In-Memory FIFO Queue    │
└──────────────┬───────────────┘
               │ (Thread-Safe Hand-off)
               ▼
┌──────────────────────────────┐
│VIII. Dedicated Storage Worker│ ──► [Persistent SQLite Storage]
└──────────────────────────────┘
```

### 1. I Eliminated "Structured Output Collapse" using Double-Blind Extraction
Forcing a model to output strict JSON schemas while simultaneously performing complex logical reasoning creates a massive bottleneck. The model chokes on formatting tokens, which corrupts or completely wipes out its step-by-step reasoning steps. 

**How I fixed it:** I explicitly separated the raw reasoning step from the data-structuring step. 
* First, my **Blind Solver-Verifier** agent receives *only* the question text and the five options—I completely omit the target answer key and formatting constraints. Operating at a deterministic temperature ($T=0.0$), the model focuses 100% of its attention weights on writing a raw, plain-text proof from scratch.
* Second, I pipe that clean proof into a downstream **Metadata Schema Parser** that reads the reasoning text and extracts the final keys into a strict Pydantic structure, which I then cross-verify programmatically outside the model context.

### 2. I Built an Autonomous Self-Healing Critique Loop
I didn't want my pipeline to treat a logic failure as a terminal drop, which results in zero production yield. If my verification engine catches a key mismatch, **I engineered an automated remediation system**. 

The pipeline captures the untruncated solver proof detailing exactly *why* the question logic failed. It packages that critique, along with the broken question draft, and routes it right back to the generator. The generation model reads the critique and performs a structured refactor attempt ($N=2$) to fix its own mathematical or verbal errors before the asset is declared a loss.

### 3. I Insulated the Database with a Threaded FIFO Ingestion Queue
When running highly concurrent asynchronous operations (`asyncio.gather`), multiple processing paths finish their jobs at the exact same millisecond. If they try to write to a single transactional instance like SQLite simultaneously, the database throws an immediate `OperationalError: database is locked` crash.

**How I engineered around this:** I implemented a **Threaded Producer-Consumer Architecture**. My asynchronous pipeline components act as Producers, non-blockingly dropping completed JSON payloads into an in-memory, thread-safe FIFO `queue.Queue()`. I then spun up a dedicated background thread to act as the sole Consumer. This thread maintains a single, persistent data connection, pulling records off the queue and committing them serially, completely erasing write collisions.

---

## 📂 Project Architecture

```text
gmac-item-guard/
├── data/
│   └── item_bank.db          # Queue-backed thread-safe database instance
├── src/
│   ├── engine/
│   │   ├── __init__.py
│   │   ├── nodes.py          # Asynchronous multi-stage loops and remediation logic
│   │   └── schemas.py        # Rigid Pydantic validation contracts
│   └── storage/
│       ├── __init__.py
│       └── item_db.py        # Threaded background FIFO consumer engine
├── main.py                   # Master asynchronous runtime loop entrypoint
├── dashboard.py              # Operational expenditure and metrics dashboard
└── requirements.txt          # System workspace dependencies
```

---

## 🛠️ Environmental Deployment & Verification

To verify my architecture locally, ensure an instance of [Ollama](https://ollama.com/) is running on your local machine, then run these setup steps:

```bash
# 1. Pull the open-weights reasoning model dependency
ollama pull llama3

# 2. Establish isolated virtual environment workspace
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\Activate.ps1

# 3. Install explicit, production-grade library bindings
pip install -r requirements.txt
pip install tiktoken

# 4. Trigger my concurrent asynchronous batch validation pipeline
python main.py

# 5. Compile and display my operational metrics and expenditure report
python dashboard.py
```

---

## 💡 Engineering Defense (FAANG Technical Review Strategy)

This is how I defend my architectural choices:
* **Why did I use `asyncio` instead of Multi-Threading for my agents?** LLM pipeline nodes are heavily bound by network I/O sockets waiting on response payloads from remote or local model daemons. By leveraging native `asyncio.gather` coroutines, I avoid the thread context-switching overhead of the Python Global Interpreter Lock (GIL), maximizing network throughput.
* **Why did I write explicit token-counting logic using `tiktoken`?** I wanted full infrastructure observability. Instead of using raw character length shortcuts (`len(text)//4`), I initialized an explicit byte-pair encoding tokenizer matching the `cl100k_base` profile. This allows me to measure exact payload footprints and monitor real operational expenditure costs down to the microcent.
* **Why isolate database persistence onto a separate background thread?** It creates a predictable, single point of entry for disk access. This prevents asynchronous task execution loops from clashing over shared transactional state, ensuring data persistence safety under tight production batch loads.
