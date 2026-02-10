## Project Overview

DeepR is a multi-agent AI research platform (The "Council") comprised of:
- **Frontend**: React (Vite) + TailwindCSS. Located in `deepr/frontend`.
- **Backend**: FastAPI (Python) + SQLite/AsyncPG. Located in `deepr/backend`.
- **Infrastructure**: Docker Compose for orchestration.

## Dev Environment Tips

- **Docker First**: The preferred way to run the app is `docker compose up --build`. This sets up both frontend and backend with hot-reloading.
    - Frontend accessible at: `http://${HOST_IP}:${FRONTEND_PORT}`
    - Backend accessible at: `http://${HOST_IP}:${BACKEND_PORT}`
- **Manual Setup**:
    - **Frontend**:
        - Navigate to `deepr/frontend`
        - Run `npm install`
        - Start dev server: `npm run dev`
    - **Backend**:
        - Navigate to `deepr/backend`
        - Create virtual env: `python -m venv venv`
        - Activate: `source venv/bin/activate`
        - Install deps: `pip install -r requirements.txt`
        - Start server: `uvicorn main:app --reload`

## Code Style Guidelines

- **Frontend**:
    - Run `npm run lint` in `deepr/frontend` to check ESLint rules.
    - Follow standard React + Hooks best practices.
    - Use Functional Components.
- **Backend**:
    - Follow PEP 8 standards.
    - Use `pydantic` models for input/output validation.
    - Ensure all DB operations use `async`/`await`.

## Testing Instructions

### Automated Tests
The project includes both backend integration tests and frontend E2E tests.

**Prerequisites:**
Ensure you have the testing dependencies installed:
`pip install pytest pytest-asyncio playwright httpx`
(For frontend tests) `playwright install chromium`

**1. Backend Tests:**
Located in `tests/test_backend.py`. These verify the API and orchestration logic using an in-memory database.
- **Run:** `pytest tests/test_backend.py`
- **Env:** Requires `OPENROUTER_API_KEY` to be set.

**2. Frontend E2E Tests:**
Located in `tests/test_frontend.py`. These use Playwright to verify the full user flow.
- **Setup:**
    1. Start Backend: `uvicorn deepr.backend.main:app --port 8000`
    2. Start Frontend: `npm run dev -- --port 3000` (from `deepr/frontend`)
- **Run:** `pytest tests/test_frontend.py`
- **Note:** The test runs in a headless browser. It requires `OPENROUTER_API_KEY` to be set in the environment to configure the simulated user settings.

### Manual Testing
- **API**: Test endpoints directly via Swagger UI at `http://localhost:8000/docs`.
- **UI**: Manually verify responsiveness if visual changes are made that are not covered by E2E scenarios.

## Security Considerations

- **API Keys**: OpenRouter API keys are stored encrypted. Do not hardcode keys in codebase.
- **Secrets**: Use `.env` files for local development secrets.
- **Validation**: Ensure all API inputs are validated via Pydantic models to prevent injection attacks.

## Environment Variables (from .env)

| Variable | Current Value | Description |
|----------|---------------|-------------|
| `HOST_IP` | `[IP_ADDRESS]` | Host IP address |
| `BACKEND_PORT` | `8000` | Port for the FastAPI backend |
| `FRONTEND_PORT` | `80` | Port for the React frontend |
| `DB_PORT` | `5432` | Port for the PostgreSQL database |
| `POSTGRES_USER` | `deepr` | Database username |
| `POSTGRES_DB` | `deepr_db` | Database name |


## PR Instructions

- **Title Format**: `[DeepR] <Short Description>`
- **Pre-Commit Checks**:
    - Ensure the application builds and runs in Docker.
    - Run `npm run lint` in `deepr/frontend`.
    - Manually verify the "Council" workflow (Coordinator -> Researchers -> Critics) still functions.
    - Update `ADR.md` if making significant architectural decisions.

## Collaboration Workflow

To ensure smooth collaboration between agents on the same branch:

1.  **Pull Before Working**: Always pull the latest changes from the branch before starting any new task to avoid conflicts.
2.  **Commit After Completing**: Commit all changes immediately after completing a task or request.
3.  **Preservation & Documentation Management**:
    *   **File Preservation**: Do not delete files, directories, or test suites unless explicitly instructed. Unintentional deletions disrupt the development flow and project history.
    *   **Documentation Integrity**: Documentation serves as the shared context for the team. Never discard large sections; instead, refactor or update them to maintain clarity and relevance.
    *   **Review Process**: If a file or documentation block appears redundant or obsolete, flag it for review or propose a reorganization OR removal rather than performing deletions
