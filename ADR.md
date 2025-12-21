# Architectural Decision Records (ADR)

## 1. System Architecture
- **Status:** Accepted
- **Decision:** Use a decoupled Client-Server architecture.
    - **Frontend:** React with Vite for a fast, responsive Single Page Application (SPA).
    - **Backend:** FastAPI (Python) for high-performance, async API handling.
- **Context:** We need a responsive UI that can handle real-time updates from multiple heavy AI processes running on the backend.

## 2. Real-Time Communication
- **Status:** Accepted
- **Decision:** Use Server-Sent Events (SSE).
- **Context:** The "Council" workflow involves long-running processes (multiple LLM calls). Waiting for a single HTTP response is bad UX. WebSockets were considered but SSE is simpler for one-way streaming (Server -> Client) which matches our "observe the thought process" requirement.

## 3. Database & Storage
- **Status:** Accepted
- **Decision:** SQL Alchemy with AsyncIO.
- **Context:** We need to store conversation history and structured "Thoughts" (Nodes). Async support is critical to not block the main event loop while waiting for database I/O, especially given the async nature of the AI streaming.

## 4. AI Model Integration
- **Status:** Accepted
- **Decision:** Use OpenRouter as the aggregation layer.
- **Context:** DeepR's core value proposition is "Cognitive Diversity" (running different models like Claude, GPT, Llama side-by-side). OpenRouter provides a unified API for all these models, simplifying the backend implementation significantly.

## 5. Security (API Keys)
- **Status:** Accepted
- **Decision:** Encrypt User API Keys at rest.
- **Context:** Determining where to store the OpenRouter API key.
    - **Option A:** Environment Variable (Server-side). Risk: Shared across all users.
    - **Option B:** Client-side only. Risk: UX friction (entering it every time).
    - **Decision:** Store in Database encrypted with a user-specific key/salt. This allows a multi-user setup (future-proofing) where each user brings their own key, without exposing it in plain text in the DB.

## 6. Containerization
- **Status:** Accepted
- **Decision:** Docker Compose for orchestration.
- **Context:** To ensure reproducible builds and easy "Quick Start" for users, the entire stack (Frontend, Backend) is containerized. This avoids "it works on my machine" issues related to Node/Python versions.

## 7. Workflow-Adaptive Visualization
- **Status:** Accepted
- **Decision:** The UI Visualization (`NodeTree`) must adapt its rendering strategy based on the workflow type.
    - **DAG Workflows (Council):** Use **Grouped/Topological Layouts** (Plan -> All Research -> All Critiques -> Synthesis). This emphasizes the hierarchy and parallel nature of the work.
    - **Debate/Iterative Workflows (DxO):** Use **Chronological/Threaded Layouts** (Proposal -> Critique -> Refinement). This emphasizes the evolution of the idea over time.
- **Context:** A single "one size fits all" visualization breaks the narrative for iterative processes like DxO, where the *order* of operations (Draft v1 -> Critique -> Draft v2) is more important than the *category* of the node.

## 8. Database Migrations
- **Status:** Accepted
- **Decision:** Use Alembic for database migrations.
- **Context:** To manage schema changes across environments without data loss.
- **Consequences:**
    1. **Strict Schema Control:** All changes must have a migration script.
    2. **No Manual DDL:** Do not execute SQL DDL manually.
    3. **Deployment Process:** Pipeline must include `alembic upgrade head`.

### Workflow: Making Database Changes
1. Modify `models.py`.
2. Generate migration: `alembic revision --autogenerate -m "..."`.
3. Review migration script.
4. Apply local: `alembic upgrade head`.
5. Commit migration file and models.
