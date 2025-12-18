# DeepR Documentation

## Development Workflows

### 1. Containerized Development (Recommended)

DeepR is designed to run entirely within Docker to ensure environment consistency. We support "Hot Reloading" for rapid development.

-   **Frontend:** Runs `vite` in development mode. Edits to `src/**/*.jsx` are reflected instantly in the browser.
-   **Backend:** Runs `uvicorn` with auto-reload. Edits to `*.py` files trigger a server restart.

**To Start Development:**
```bash
docker compose up --build
```

**To View Logs:**
```bash
docker compose logs -f
```

**To Rebuild (after adding dependencies):**
```bash
docker compose up --build -d
```

### 2. Manual Setup (Local)

If you prefer running outside Docker:

**Backend:**
1.  `cd deepr/backend`
2.  `python -m venv venv && source venv/bin/activate`
3.  `pip install -r requirements.txt`
4.  `uvicorn main:app --reload` (Runs on port 8000)

**Frontend:**
1.  `cd deepr/frontend`
2.  `npm install`
3.  `npm run dev` (Runs on port 5173 - Note: Update API_URL in `.env` if needed)
