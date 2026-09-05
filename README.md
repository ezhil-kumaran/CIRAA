# Cloud Incident Response Advisory Agent (CIRAA)

> **An Agentic RAG System for Incident Analysis, Troubleshooting Guidance, and Remediation Instruction**

---

## 📋 Overview

The **Cloud Incident Response Advisory Agent (CIRAA)** is a production-grade, enterprise RAG (Retrieval-Augmented Generation) system engineered to help DevOps, SRE, and Cloud Operations teams rapidly diagnose and resolve infrastructure incidents. 

By combining **LangGraph stateful orchestration**, **NeMo Guardrails**, **Qdrant Vector Database**, **SentenceTransformers**, and **Portkey Gateway with Groq LPUs**, CIRAA synthesizes complex technical documentation into accurate, context-aware remediation instructions while ensuring strict input safety and operational observability.

---

## 🎯 Key Capabilities

- 🔍 **Contextual Incident Analysis**: Parses error logs, stack traces, and incident reports to retrieve matching enterprise runbooks and architectural documentation.
- 🛠️ **Step-by-Step Remediation Guidance**: Generates clear, structured troubleshooting playbooks for human operators to execute safely.
- 🛡️ **Safety Guardrails**: Input/output filtering via **NVIDIA NeMo Guardrails** to prevent off-topic prompts, jailbreaks, and prompt injection attempts before retrieval.
- 🧠 **Conversational Memory**: **LangGraph `MemorySaver`** checkpointer maintains context across incident triage threads (`thread_id`).
- ⚡ **Local Semantic Embeddings & Re-Ranking**: Uses **SentenceTransformers (`all-mpnet-base-v2`)** for 768-dim dense embeddings and **FlashRank** local cross-encoder re-ranking on top of **Qdrant Vector Search**.
- 🌐 **Groq LPU Acceleration & LLM Gateway**: Powered primarily by **Groq LPU hardware API** routed via **Portkey Gateway** with automatic failover and semantic caching.
- 📊 **Comprehensive Evaluation**: Built-in 6-metric **RAGAS** evaluation engine with a dedicated **Streamlit** dashboard.
- 🔭 **Full Stack Observability**: Dual tracing with **Pydantic Logfire** and **LangSmith** across all agent nodes and API endpoints.


https://github.com/user-attachments/assets/3ff51e11-0383-424f-a1a7-67d8c6f8921d




---
> [!IMPORTANT]
> **Advisory Scope Disclaimer**: CIRAA is an **instructional & advisory assistant**. It retrieves enterprise runbooks, post-mortems, and technical documentation to provide step-by-step diagnostic and remediation guidance to engineers. **It does NOT autonomously modify infrastructure, run SSH commands, or trigger automated production changes.** All remediation steps must be reviewed and executed manually by authorized personnel.

## ⚙️ Technical Parameters & Specifications

### 📄 Document Chunking & Parsing
- **Chunking Algorithm**: `RecursiveCharacterTextSplitter` (LangChain)
- **Chunk Size**: `1,500` characters (~375 tokens per chunk)
- **Chunk Overlap**: `200` characters (~50 tokens overlap)
- **Separator Priority**: `["\n\n", "\n", ". ", " ", ""]` (Paragraphs → Lines → Sentences → Words → Characters)
- **Supported Formats**: PDF, HTML, TXT, DOCX, PPTX (Parsed entirely on-device)

### 🎯 Vector Search & Reranking Pipeline
- **Production Embedding Model**: `SentenceTransformers` (`all-mpnet-base-v2` — 100% local, no external API)
- **Vector Dimension**: `768` dimensions
- **Vector Distance Metric**: Cosine Distance
- **Qdrant Collection**: `enterprise_rag`
- **Qdrant Upsert Batch Size**: `50` points per payload (prevents HTTP write timeouts)
- **Initial Vector Search**: Top-`10` candidate vectors retrieved from Qdrant
- **Semantic Re-Ranker**: FlashRank local cross-encoder (`ms-marco-MiniLM-L-12-v2`)
- **Final Reranked Context**: Top-`3` highest-scoring runbook chunks passed to LLM context
- **RAGAS Eval Embeddings**: `sentence-transformers/all-MiniLM-L6-v2` (`384`-dim via `LangchainEmbeddingsWrapper`)

### 🤖 LLM & Token Budget Constraints
- **Primary LLM Provider**: **Groq API** (LPU Inference Engine at `https://api.groq.com/openai/v1`)
- **LLM Gateway Router**: **Portkey AI Gateway** (handles fallbacks, retry logic, and semantic cache headers)
- **Primary Pipeline Model**: `qwen/qwen3.8-27b` (via Groq API)
- **Guardrails & Fallback Model**: `llama-3.1-8b-instant` (via Groq API)
- **Max Output Token Ceiling (`max_tokens`)**: `1,000` tokens (calibrated for Groq's 1,000 Output Tokens Per Minute (OTPM) `on_demand` limit)
- **Prompt Context Limit**: Truncated to `6,000` characters (~1,500 tokens) in Responder node to prevent Groq TPM rate limits
- **Eval Context Truncation**: `300` characters per chunk (~75 tokens), max `2` chunks per query during RAGAS eval execution

### ⏱️ Rate-Limit & Cooldown Safeguards
- **Eval Async Batch Size**: `1` sample per async call stack
- **Mini-Batch Cooldown**: `40` seconds between individual samples
- **Experiment Cooldown**: `62` seconds between evaluation experiments

---

## 🛠️ Technology Stack

| Component | Technology | Purpose |
| :--- | :--- | :--- |
| **Agentic Framework** | [LangGraph](https://github.com/langchain-ai/langgraph) | Cyclic state-machine workflow & thread memory |
| **Web API** | [FastAPI](https://fastapi.tiangolo.com/) + Uvicorn | High-performance async REST backend |
| **Embeddings** | [SentenceTransformers](https://sbert.net/) (`all-mpnet-base-v2`) | 768-dim local dense text embeddings |
| **Vector DB** | [Qdrant Cloud / Local](https://qdrant.tech/) | Vector index and similarity search |
| **Semantic Reranker** | [FlashRank](https://github.com/PrithivirajDamodaran/FlashRank) | Local cross-encoder reranking (`ms-marco-MiniLM-L-12-v2`) |
| **Safety Rails** | [NVIDIA NeMo Guardrails](https://github.com/NVIDIA/NeMo-Guardrails) | Input/output security and topic enforcement |
| **LLM Engine & Gateway**| [Groq LPU API](https://groq.com/) + [Portkey AI](https://portkey.ai/) | High-speed LLM inference, fallbacks & caching |
| **Document Parser** | Unstructured, PyPDF, pdfplumber, BeautifulSoup4 | Local parsing of PDF, HTML, DOCX, PPTX |
| **Eval Dashboard** | [Streamlit](https://streamlit.io/) + [RAGAS](https://github.com/explodinggradients/ragas) | Evaluation metric dashboard |
| **Observability** | [Pydantic Logfire](https://logfire.pydantic.dev/) + [LangSmith](https://smith.langchain.com/) | Tracing & telemetry across nodes |

---

## 🏗️ System Architecture

```
                  ┌─────────────────────────────────────────┐
                  │          User / Client Request          │
                  └────────────────────┬────────────────────┘
                                       │
                                       ▼
                  ┌─────────────────────────────────────────┐
                  │    Gate 1: NVIDIA NeMo Guardrails       │
                  │   (Safety Check / Off-Topic Filter)     │
                  └────────┬──────────────────────┬─────────┘
                           │ Blocked              │ Safe
                           ▼                      ▼
                  ┌─────────────────┐ ┌───────────────────────────────────────┐
                  │ Blocked Warning │ │ Gate 2: LangGraph State Machine       │
                  └─────────────────┘ │  (Thread-level Conversational Memory) │
                                      └───────────────────┬───────────────────┘
                                                          │
                                                          ▼
                                            ┌───────────────────────────┐
                                            │      Planner Node         │
                                            └─────────────┬─────────────┘
                                                          │
                                           ┌──────────────┴──────────────┐
                                           │ Router                      │
                                           ├─────────────────────────────┤
                                           │ Conversational -> Responder │
                                           │ Technical     -> Retriever │
                                           └──────────────┬──────────────┘
                                                          │
                                                          ▼
                                            ┌───────────────────────────┐
                                            │      Retriever Node       │
                                            │  1. SentenceTransformers  │
                                            │  2. Qdrant Vector Search  │
                                            │  3. FlashRank Reranker    │
                                            └─────────────┬─────────────┘
                                                          │
                                                          ▼
                                            ┌───────────────────────────┐
                                            │      Responder Node       │
                                            │ (Portkey Gateway / Groq)  │
                                            └─────────────┬─────────────┘
                                                          │
                                                          ▼
                                            ┌───────────────────────────┐
                                            │ Structured Remediation    │
                                            │ Guidance Output           │
                                            └───────────────────────────┘
```

---

## 🚀 Quick Start

### 1. Prerequisites

- Python 3.10+
- Groq API Key
- Qdrant Cluster Endpoint & API Key

### 2. Installation

Clone the repository and set up a virtual environment:

```bash
git clone https://github.com/your-org/cloud-incident-advisory-agent.git
cd cloud-incident-advisory-agent

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

### 3. Environment Configuration

Create a `.env` file in the root directory:

```env
# Qdrant Vector DB
QDRANT_CLUSTER_ENDPOINT=https://your-cluster.qdrant.tech
QDRANT_API_KEY=your_qdrant_api_key

# Groq Reasoning Models (Primary LLM Engine)
GROQ_API_KEY=your_primary_groq_key
GROQ_FALLBACK_API_KEY=your_fallback_groq_key
GROQ_MODEL=openai/gpt-oss-120b
GROQ_MODEL_SMALL=openai/gpt-oss-20b

# Portkey Gateway (LLM Router & Cache)
PORTKEY_API_KEY=your_portkey_api_key
PORTKEY_CONFIG_ID=your_portkey_config_id

# Observability
LOGFIRE_TOKEN=your_logfire_token
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=your_langsmith_api_key
LANGSMITH_PROJECT=cloud_incident_agent
```

---

## 🏃 Running the Application

### 1. Start the FastAPI REST API

```bash
uvicorn app.main:app --reload --port 8000
```
- Interactive API Docs: `http://localhost:8000/docs`
- Workflow Graph Image: `http://localhost:8000/graph`

### 2. Start the Evaluation Dashboard

```bash
streamlit run evals/app.py
```
- Dashboard UI: `http://localhost:8501`

---

## 📡 API Reference

### `POST /query`
Executes incident inquiry processing through Guardrails and the LangGraph workflow.

**Request Body:**
```json
{
  "q": "High CPU utilization on Kubernetes pod worker-node-04 and 504 Gateway Timeouts",
  "thread_id": "incident-2026-0905-A"
}
```

**Response Output:**
```json
{
  "question": "High CPU utilization on Kubernetes pod worker-node-04 and 504 Gateway Timeouts",
  "answer": "### Diagnostic & Remediation Steps...\n\n1. Inspect Pod Metrics...\n2. Check Ingress Controller Limits...",
  "thought_process": [
    "Planner: Identify technical incident query",
    "Retriever: Fetched 3 relevant runbook sections",
    "Responder: Synthesized remediation playbook"
  ],
  "status": "Completed",
  "sources": [
    "runbooks/k8s-high-cpu-troubleshooting.pdf",
    "post-mortems/2026-04-ingress-timeout.md"
  ]
}
```

---

## 🧪 Evaluation Suite (RAGAS)

The project includes an end-to-end evaluation pipeline that tests retrieval quality, answer correctness, and tool accuracy against a golden dataset:

1. **Faithfulness**: Measures if the generated instructions are grounded strictly in retrieved runbooks.
2. **Answer Relevancy**: Evaluates how directly the answer addresses the reported incident.
3. **Context Precision**: Evaluates the signal-to-noise ratio of retrieved runbook chunks.
4. **Context Recall**: Checks if all necessary troubleshooting details were successfully retrieved.
5. **Answer Correctness**: Compares generated guidance against ground-truth expert resolution steps.
6. **Tool Correctness**: Measures exact match accuracy of diagnostic tools recommended.

---

## 📁 Repository Structure

```
├── app/
│   ├── main.py              # FastAPI application entry point & routes
│   ├── config.py            # Global configuration settings & env loader
│   ├── agents/
│   │   ├── graph.py         # LangGraph state machine & memory checkpointer
│   │   ├── state.py         # AgentState data contract
│   │   └── nodes/           # Planner, Retriever, and Responder nodes
│   ├── guardrails/          # NVIDIA NeMo Guardrails configuration & gating
│   ├── gateway/             # Portkey LLM gateway client & fallback handling
│   ├── ingestion/           # Document parser (PDF, HTML, DOCX, PPTX)
│   └── services/            # Qdrant vector database & FlashRank reranker
├── evals/
│   ├── app.py               # Streamlit Evaluation Dashboard
│   ├── metrics.py           # RAGAS metrics & Groq judge configuration
│   ├── pipeline.py          # Phase 1 dataset enrichment pipeline
│   └── golden_dataset.json  # Benchmark incident evaluation dataset
├── ui/
│   └── app.py               # Chatbot UI interface
├── requirements.txt         # Python project dependencies
└── .gitignore               # Ignored files, data directories, and secrets
```

---

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.
