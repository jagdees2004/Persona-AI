# Persona AI Chatbot 🤖

A highly advanced, production-ready AI agent system featuring dynamic **Multi-Persona** management, **Dual-Layer Memory (Short-term & Semantic Long-term)**, comprehensive **User Onboarding**, and robust **LangChain integrations** utilizing Hugging Face's latest Inference Endpoints.

This project delivers a state-of-the-art conversational experience where users can seamlessly switch between distinct AI personalities, all while the system retains deep conversational context and respects user-level personalization.

---

## 📊 Project Summary

| Attribute | Details |
|---|---|
| **Project Name** | Persona AI Chatbot |
| **Version** | 1.1.0 (MongoDB Migration) |
| **Framework** | FastAPI (Python 3.10+) |
| **Database** | **MongoDB Atlas (Cloud)** via `motor` (async) |
| **Vector Store** | **ChromaDB** + `sentence-transformers/all-MiniLM-L6-v2` |
| **LLM** | HuggingFace Inference API (`Meta-Llama-3-8B-Instruct`) via LangChain |
| **Frontend** | Static HTML/CSS/JS (3 pages) |
| **Deployment** | Docker + docker-compose |
| **Total Source Files** | ~35 files |
| **Personas Defined** | 6 (Friend, Mentor, Girlfriend, General Assistant, Dietitian, Doctor) |

---

## 🌟 Core Features

### 🎭 Dynamic Multi-Persona Engine
- Chat with **6 specialized AI personas**: Friend, Mentor, Girlfriend, General Assistant, Dietitian, and Doctor.
- Each persona has a unique `system_prompt`, `tone`, `behavior_rules`, `response_style`, and `safety_constraints`.
- User's active persona is tracked per session with automatic resolution and switching.

### 🧠 Dual-Layer Advanced Memory
- **Short-Term Memory**: In-memory rolling window with **MongoDB persistence** (TTL-ready). Context survives server restarts.
- **Long-Term / Vector Memory (ChromaDB)**: Embeds conversations and stores them in ChromaDB with **native metadata filtering**. Retrieves top-k semantically similar past conversations.
- **Strict Persona Isolation**: Memory is siloed by `user_id` + `persona` at every layer — no cross-persona data leakage.

### 👤 Comprehensive User Profiling (Onboarding)
- **Global Profiles**: Shared across all personas.
- **Persona-Specific Preferences**: Custom settings per persona (e.g., coding language for mentor).

### 🛡️ Safety & Moderation System
- **Pre-input filtering**: Crisis keyword detection and harmful content pattern matching.
- **Post-output filters**: Per-persona disclaimers (e.g., medical disclaimers for the Doctor persona).

---

## 🏗️ Architecture & Data Flow

### Chat Endpoint Orchestration

When a user sends a message to `/chat`, the following 8-step pipeline executes:

1. **Safety Check (Pre-Input)**: Crisis/harmful keyword detection.
2. **Resolve Persona**: Switch persona if provided, else use stored.
3. **Retrieve Memory**: Short-term (recent 10) + Long-term (top-5 ChromaDB) + Persona summary.
4. **Load User Data**: Global profile + persona-specific preferences (all from MongoDB).
5. **Build Prompt**: 7-layer hierarchy including summary and long-term memory.
6. **Call LLM**: HuggingFace InferenceClient (streaming) with 5 retries.
7. **Safety Filter (Post-Output)**: Per-persona post-processing.
8. **Store & Respond**: Save to Short-term (In-Memory + MongoDB) + ChromaDB + MongoDB Atlas.

---

## 📁 Directory Structure

```text
📂 Persona AI/
├── 📂 app/                          # Backend Python Application
│   ├── 📂 core/                     # Infrastructure (config.py, database.py)
│   ├── 📂 memory/                   # Short-term + ChromaDB Vector Memory
│   ├── 📂 models/                   # Pydantic Schemas (MongoDB Schema Docs)
│   ├── 📂 onboarding/              # User Profile Logic
│   ├── 📂 personas/                # Persona Configs (personas_config.json)
│   ├── 📂 routes/                  # Chat, Memory, Onboarding, Health
│   ├── 📂 services/               # LLM, Prompt Builder, Safety
│   ├── main.py                      # FastAPI entry point
│   ├── requirements.txt             # Dependency manifest
│   ├── .env                         # Environment variables
│   └── Dockerfile                   # Container recipe
├── 📂 frontend/                     # Static HTML UI
└── docker-compose.yml               # Multi-service orchestration
```

---

## 📦 Dependencies

| Package | Used By |
|---|---|
| `fastapi` | API Framework |
| `motor` | **Async MongoDB Client** |
| `chromadb` | **Vector Similarity Search** |
| `huggingface-hub` | LLM Inference |
| `langchain` | Prompt & Model orchestration |
| `slowapi` | Rate Limiting |

---

## 🚀 Getting Started

### 1️⃣ Local Development Setup

1. **Install Dependencies**:
   ```bash
   pip install -r app/requirements.txt
   ```

2. **Configure `.env`**:
   Update `app/.env` with your **MongoDB Atlas URI** and **HuggingFace API Key**.

3. **Start the App**:
   ```bash
   cd app
   python main.py
   ```

### 2️⃣ Docker Deployment
```bash
docker-compose up --build -d
```
Docker Compose now includes a `mongodb` service as a local fallback, but is configured to connect to Atlas if providing a cloud URI in `.env`.

---

## 🔌 API Reference (Highlights)
- `POST /chat` — The main intelligence endpoint.
- `POST /onboarding` — Save global user profile.
- `GET /personas` — List all available AI personalities.
- `GET /memory` — View current context and stats.
- `POST /reset` — Clear a persona's specific memories.
