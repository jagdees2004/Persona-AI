# Persona AI Chatbot 🤖

A highly advanced, production-ready AI agent system featuring dynamic **Multi-Persona** management, **Dual-Layer Memory (Short-term & Semantic Long-term)**, comprehensive **User Onboarding**, and robust **LangChain integrations** utilizing Hugging Face's latest Inference Endpoints.

This project delivers a state-of-the-art conversational experience where users can seamlessly switch between distinct AI personalities, all while the system retains deep conversational context and respects user-level personalization.

---

## 🌟 Core Features

- **🎭 Dynamic Multi-Persona Engine**: 
  - Chat with specialized AI personas (e.g., mentors, creative assistants, technical experts).
  - Each persona possesses a customized `system_prompt`, `tone`, `behavior_rules`, and strict `safety_constraints`.
  - Driven by `personas_config.json` for hot-swapping configurations dynamically.

- **🧠 Dual-Layer Advanced Memory**:
  - **Short-Term Memory**: Keeps track of recent conversational turns per-persona to maintain immediate flow.
  - **Vector / Long-Term Memory (FAISS & SentenceTransformers)**: Automatically chunks, embeds, and persistently stores the semantic meaning of conversations. It retrieves exact relevant historical context to inject into prompts, giving the AI near-infinite "recall" of past interactions.

- **👤 Comprehensive User Profiling (Onboarding)**:
  - Supports **Global Profiles** (e.g., Name, Age, Interests, Location).
  - Supports **Persona-Specific Preferences** (e.g., Asking a code-persona for Python examples, but asking a storytelling-persona for dark fantasy themes).

- **⚡ High-Performance Backend Architecture**:
  - Built on asynchronous **FastAPI** for maximal throughput.
  - LLM integration utilizes **LangChain** and **HuggingFace Endpoints** (via a specialized RunnableLambda adapter mapping robust `InferenceClient` connections to bypass gated repository HTTP blocks).
  - Rate limiting deployed via **SlowAPI**.

- **💿 Persistent Storage**: 
  - Relational Database via **SQLAlchemy & aiosqlite** (`persona_ai.db`), asynchronously logging all metadata.
  - Vector stores mapped securely via Chroma/FAISS persistence (`/chroma_data`).

---

## 🏗️ Architecture & Technology Stack

**Frontend Components**: Vanilla HTML, CSS, JS served as static FastAPI mounts.
**Backend Framework**: FastAPI (Python 3.10+)
**Database**: SQLite (`aiosqlite`), SQLAlchemy 2.0
**Vector Store**: FAISS (CPU), `sentence-transformers` (`all-MiniLM-L6-v2`)
**LLM Orchestration**: LangChain, HuggingFace Hub (running Llama 3 or compatible open-weights)
**Security & Rate Limiting**: SlowAPI

---

## 📁 Deep-Dive Directory Structure

```text
📦 Persona AI
├── 📂 app/                     # Backend Python Application
│   ├── 📂 core/                # Configuration and DB engine instances
│   │   ├── config.py           # Pydantic BaseSettings loading from Environment
│   │   ├── database.py         # SQLAlchemy engine and session makers
│   │   └── logging_config.py   # Standardized rotating file and console logging
│   │
│   ├── 📂 db/                  # Database management workflows
│   │   └── init_db.py          # Asynchronous schema initialization script
│   │
│   ├── 📂 memory/              # Dual-Layer Conversation Logging
│   │   ├── memory_manager.py   # Gateway combining short-term and long-term
│   │   ├── short_term_memory.py# Rolling sliding window of recent tokens/messages
│   │   └── vector_memory.py    # Embeddings, chunks, and FAISS similarity search
│   │
│   ├── 📂 models/              # Data schemas and Pydantic validation
│   │   ├── schemas.py          # Pydantic DTOs for RestAPI Requests and Responses
│   │   ├── user.py             # ORM Declarative bindings for User table
│   │   ├── chat_history.py     # ORM Declarative bindings for Chat interactions
│   │   ├── persona_summary.py  # ORM for semantic conversation summaries
│   │   └── persona_preferences.py
│   │
│   ├── 📂 onboarding/          # User Registration and Preference Engine
│   │   └── onboarding_service.py # Logic for patching Profiles and Preferences
│   │
│   ├── 📂 personas/            # Persona Resolution and Injection
│   │   ├── persona_service.py  # Loads personas_config, extracts rules and guidelines
│   │   └── personas_config.json# JSON payload shaping the distinct AI personalities
│   │
│   ├── 📂 routes/              # FastAPI Router Entrypoints
│   │   ├── chat_routes.py      # /chat -> Core orchestration (Safety -> Memory -> Prompt -> LLM -> Storage)
│   │   ├── health_routes.py    # Healthchecks and diagnostics
│   │   ├── memory_routes.py    # REST APIs for querying past interactions
│   │   ├── onboarding_routes.py# REST APIs for updating User settings
│   │   └── persona_routes.py   # REST APIs to fetch available distinct personas
│   │
│   ├── 📂 services/            # Primary External Integrations
│   │   ├── llm_service.py      # LangChain Hugging Face execution. Re-engineered as a RunnableLambda wrapping InferenceClient.
│   │   ├── prompt_builder.py   # Assembles systemic + profile + vector memory + session messages.
│   │   └── safety.py           # Pre/Post filtering and toxicity guardrails.
│   │
│   ├── 📂 utils/               # Lightweight computational helpers
│   ├── main.py                 # ASGI application startup, exception handlers, and CORS
│   ├── requirements.txt        # Verified lock of Python packages
│   ├── Dockerfile              # Container orchestration recipes
│   └── docker-compose.yml      # Multi-service mapping
│
├── 📂 frontend/                # Browser Interfaces
│   ├── main_chat_experience.html   # Primary chatbot conversational UI
│   ├── persona_selection_grid.html # Grid UI for selecting AI personality
│   └── user_onboarding_flow.html   # HTML Form step-by-step for profile ingestion
│
└── 📜 README.md                # This comprehensive document
```

---

## ⚙️ Component Deep Dive & Data Flow

### 1. The Chat Route Orchestration (`app/routes/chat_routes.py`)
When a user hits `/chat`, the following orchestration precisely triggers:
1. **Safety Filter**: Evaluates the input for compliance via `safety.py`.
2. **Persona Resolution**: Verifies the requested persona exists in `personas_config.json`.
3. **Memory Retrieval**: Hits `memory_manager.py` to retrieve up to 20 Short Term messages and embeds the current prompt to fish out the top 5 semantic memories from FAISS.
4. **Context Injection**: Profiles and memories merge in `prompt_builder.py`, creating highly specific context for the LLM.
5. **Inference Execution**: Pushed to the Hugging Face `ChatHuggingFace` Runnable wrapper in `llm_service.py`. Async waiting mechanisms ensure FastAPI's event loop isn't blocked.
6. **Storage**: Outputs and Context are synchronized securely to internal SQLite + Faiss databases.

### 2. Prompt Building Construction (`prompt_builder.py`)
To prevent models from hallucinating, Prompts are strictly constructed in this hierarchy:
- System Level Instructions
- Persona Tone & Safety Rules
- Global User Details (Name, Location)
- Persona View Preferences (What the user wants out of THIS specific persona)
- Semantic Search Vector Results (Memories)
- Recent Rolling Messages (Context)
- Real-time User Query

### 3. The LLM Service Bridge (`llm_service.py`)
A custom robust integration connects LangChain architectures directly to the HuggingFace `InferenceClient`. This ensures the application can communicate with restricted (gated) weights like `Meta-Llama-3-8B-Instruct` smoothly without encountering `403 Forbidden` API limitations typically caused by explicit tokenizer downloads natively found in standard classes.

---

## 🚀 Getting Started & Installation

### Prerequisites
- Python 3.10+
- A valid [Hugging Face](https://huggingface.co/) Account & Access Token
- Virtual Environment tool (`uv`, `venv`, or `conda`)

### 1️⃣ Local Development Setup
1. **Clone and Setup Virtual Environment**:
   ```bash
   git clone <repo-url>
   cd "Persona AI"
   python -m venv .venv
   # Windows:
   .venv\Scripts\activate
   # Linux/Mac:
   source .venv/bin/activate
   ```

2. **Install Dependencies**:
   ```bash
   cd app
   pip install -r requirements.txt
   ```

3. **Configure Environment Variables**:
   Create a `.env` file in the `app/` folder based on `.env.example`:
   ```ini
   HUGGINGFACE_API_KEY=hf_YourHuggingFaceTokenHere
   LLM_MODEL=meta-llama/Meta-Llama-3-8B-Instruct
   APP_HOST=0.0.0.0
   APP_PORT=8000
   ```

4. **Boot the Backend Server**:
   ```bash
   python main.py
   # Or via Uvicorn:
   # uvicorn main:app --reload
   ```

5. **Access the Application**:
   - Backend API Docs (Swagger): [http://localhost:8000/docs](http://localhost:8000/docs)
   - Frontend UI: Navigate to `frontend/user_onboarding_flow.html` in your browser.

### 2️⃣ Docker Deployment
For production-grade isolated runs:
```bash
cd app
docker-compose up --build -d
```
The server will bind immediately to port 8000. Logs can be investigated via `docker logs -f persona_ai_backend`.

---

## 🛣️ Future Roadmap
- **OAuth Authentication**: Tie User IDs directly to OAuth2 flows using JWT.
- **Audio/Voice Generation**: Sync `TTS (Text-to-Speech)` dynamically depending on the selected persona's defined tone.
- **WebHooks / Tool Calling**: Utilize Llama-3's capabilities to execute Python scripts, fetch internet queries, and search external databases directly inside the Chat loops.
- **Cloud Vector DBs**: Move FAISS out to Pinecone or Qdrant for horizontal persistence.
