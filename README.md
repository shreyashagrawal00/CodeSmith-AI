# CodeSmith AI – Autonomous Multi-Agent Software Engineering Team

CodeSmith AI is an autonomous, stateful, multi-agent software engineering platform built with **LangGraph**, **FastAPI**, and **React + Vite + Tailwind CSS**. It simulates a complete software development lifecycle where specialized, state-contained agents collaborate through a single shared state to transform a natural-language prompt into a production-ready application.

---

## 🚀 Features

- **Multi-Agent Collaboration**: Orchestrates 11 specialized roles (Product Manager, Architect, DB Designer, Backend Engineer, Frontend Engineer, Code Reviewer, Security Auditor, QA Tester, Bug Fixer, Tech Writer, and DevOps Engineer) in an iterative, self-correcting LangGraph pipeline.
- **Stateful Workflow Orchestration**: Uses LangGraph's shared state pattern to pass context between agents. No agent communicates directly with another; all state modifications are checked and merged through `ProjectState`.
- **Structured LLM Outputs**: Enforces strict Pydantic schemas using model-level structured outputs to parse agent results reliably.
- **Multi-LLM Routing**: Automatically routes tasks to optimal LLMs (Gemini, Groq, Mistral) based on task needs.
- **WebSocket Streaming**: Stream agent progress, active logs, and status updates to the client in real-time.
- **Downloadable Archives**: Automatically builds folder structures for generated projects and packages them as downloadable ZIP archives.

### 🆕 Advanced Self-Correction & Workspace Features (Newly Upgraded)
- **Automated Compiler Feedback Loop**: During the verification phase, the platform now writes generated code to disk and runs real compiler checks:
  - **Frontend:** Installs dependencies and runs a full `vite build` check.
  - **Backend:** Executes Python compilation checks (`py_compile`) to catch syntax, import, and logic errors.
  - **Self-Correction:** Any compilation, build, or package resolution errors are captured and routed directly back to the **Bug Fixer** agent. It patches the code and repeats the process until the build compiles cleanly (up to 3 iterations).
- **IDE Workspace Code Explorer**: The frontend output viewer includes a premium multi-file code browser. Instead of viewing a single static file dump, you can browse all generated source files—including components, routes, services, dependency manifests, configuration scripts, and middlewares—in an IDE-style explorer layout.
- **Nested Folder Structure Support (`extra_files`)**: The backend generation engine now supports generating and creating files inside custom subfolders (e.g., `routes/taskRoutes.js`, `middleware/auth.js`, `utils/helpers.py`), matching the LLM's import statements perfectly.
- **Resilient Previews**: Supports automated NPM package checks with dynamic `--legacy-peer-deps` fallback retries to handle conflicting React dependencies seamlessly.

---

## 🛠️ Architecture Workflow

```mermaid
graph TD
    User([User Prompt]) --> PM[Product Manager]
    PM --> Arch[System Architect]
    Arch --> DB[Database Designer]
    DB --> BE[Backend Engineer]
    BE --> FE[Frontend Engineer]
    FE --> Rev[Code Reviewer / Compiler Validation]
    
    subgraph Self-Correction Loop (Up to 3 Iterations)
        Rev --> |If Compilation or Quality Fails| BF[Bug Fixer]
        BF --> |Re-Write & Re-Compile| Rev
    end

    Rev --> |If Approved| Sec[Security Auditor]
    Sec --> QA[QA Tester]
    QA --> Doc[Tech Writer]
    Doc --> DevOps[DevOps Engineer]
    DevOps --> End([Complete ZIP & Running Preview])
```

---

## 📂 Project Structure

```
CodeSmith AI/
├── backend/
│   ├── app/
│   │   ├── agents/          # Specialized agent packages (PM, Architect, Reviewer, etc.)
│   │   ├── api/             # REST routes and WebSocket streaming
│   │   ├── core/            # BaseAgent, BaseLLMAgent, Providers definition
│   │   ├── database/        # SQLite Persistence & SQLAlchemy tables
│   │   ├── graph/           # LangGraph builder, state, and routing rules
│   │   ├── guardrails/      # Output validators and parser logic
│   │   ├── llms/            # Individual model drivers (Gemini, Groq, Mistral)
│   │   └── services/        # Disk writes, build validation, live preview servers
│   ├── main.py              # FastAPI application server entrypoint (uses Lifespan)
│   └── test_graph.py        # Pipeline dry-run script
├── frontend/
│   ├── src/
│   │   ├── components/      # UI Elements (ProjectForm, ProgressBar, OutputViewer workspace)
│   │   ├── App.jsx          # Dashboard layout & WebSocket orchestration
│   │   └── index.css        # Tailwind v4 theme styling
│   ├── package.json
│   └── vite.config.js
├── docker/                  # Docker build resources
├── docker-compose.yml       # Production Compose orchestrator
└── README.md                # System documentation
```

---

## ⚡ Quickstart

### Prerequisite Environment Configuration

Create a `.env` file inside `backend/`:
```env
GEMINI_API_KEY=your_gemini_key
GROQ_API_KEY=your_groq_key
MISTRAL_API_KEY=your_mistral_key
```

### Option A: Local Development

#### 1. Backend Setup
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Or `.venv\Scripts\activate` on Windows
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

#### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
Open [http://localhost:5173](http://localhost:5173) in your browser.

### Option B: Docker Compose
```bash
docker-compose up --build
```
- Frontend: [http://localhost:3000](http://localhost:3000)
- Backend: [http://localhost:8000](http://localhost:8000)

---

## 📈 Verification

To verify that the multi-agent graph builder runs correctly without starting the API server, execute the mock workflow runner:
```bash
cd backend
.venv/bin/python test_graph.py
```
