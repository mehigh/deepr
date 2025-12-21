# DeepR

DeepR is an AI Council research application. It allows you to query a prompt which is then processed by a Coordinator, researched by multiple AI models in parallel, critiqued anonymously, and finally synthesized into a comprehensive answer.

## Features
- **AI Council Workflow:** Plan -> Research -> Critique -> Synthesis.
- **Cognitive Diversity:** Run multiple models simultaneously. Currently supports **GPT-4o, Claude 3 Opus, Gemini 1.5 Pro, Llama 3 70B**, and specialized models like **DeepSeek Coder**.
- **Role-Based Interaction:** Assign a "Chairman" model to lead the synthesis while selecting specific Council Members for research and critique.
- **Anonymous Critique:** Blind peer review between models to reduce bias.
- **DAG Visualization:** Watch the research unfold in real-time via an interactive Node Tree.
- **Diagnostic Orchestration (DxO):** A multi-turn debate between specialized agents (Lead Architect, Reviewer, QA) to refine complex system designs.
- **History:** Auto-saves your sessions for later review.
- **Secure Configuration:** Encrypted storage for your OpenRouter API Key in the Settings page.

## Screenshot

![DeepR Interface](assets/screenshot.png)

## Inspiration

Inspired by Satya Nadella's [app demo that uses AI to create decision frameworks](https://www.youtube.com/watch?v=SEZADIErqyw), through which the following frameworks were shared: AI Coucil, Ensemble and also the Microsoft AI Diagnostic Orchestrator (MAI-DxO), a system designed to improve medical diagnosis accuracy.

## Quick Start (Docker)

The easiest way to run DeepR is with Docker Compose.

1.  **Prerequisites:** Install Docker and Docker Compose.
2.  **Run:**
    ```bash
    docker compose up --build
    ```
3.  **Access:**
    -   Frontend: `http://localhost:80`
    -   Backend API: `http://localhost:8000`

## Development Setup

For detailed instructions on running the environment with hot-reloading, please see [DEVELOPMENT.md](DEVELOPMENT.md).

### Quick Summary
1.  **Run:** `docker compose up --build`
2.  **Edit:** Changes to frontend or backend files are applied instantly.

## Configuration

-   **API Key:** You need an OpenRouter API Key. Enter it in the **Settings** page of the application (it is stored encrypted).
-   **Environment Variables:** See `deepr/backend/.env` (created automatically or copy from `docker-compose.yml`).
