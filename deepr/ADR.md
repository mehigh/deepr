# Architectural Decision Records (ADR)

## 001. Database Management and Migrations

### Context
The application uses a relational database (PostgreSQL) with SQLAlchemy as the ORM. As the application evolves, the database schema (tables, columns, relationships) will inevitably change. We need a reliable way to manage these changes across different environments (local development, staging, production) without losing data.

In the early stages of development, it is often convenient to simply drop the database and recreate it. However, this is not a viable strategy for a production environment or when we want to preserve test data.

### Decision
We will use **Alembic** for database migrations. Alembic provides a robust framework for generating, managing, and applying schema changes.

- **`deepr/backend/alembic` directory**: Contains the migration scripts and environment configuration.
- **`deepr/backend/alembic.ini`**: Configuration file for Alembic.
- **`deepr/backend/alembic/env.py`**: A Python script that defines how the migration environment connects to the database. This file has been customized to read the database URL from environment variables and support `asyncpg`.

### Consequences
1.  **Strict Schema Control**: All changes to the database schema must be accompanied by a corresponding Alembic migration script.
2.  **No Manual DDL**: Developers should not manually execute SQL DDL (e.g., `CREATE TABLE`, `ALTER TABLE`) on the database.
3.  **Deployment Process**: The deployment pipeline must include a step to apply pending migrations (`alembic upgrade head`).

### Workflow: Making Database Changes

1.  **Modify Models**: Update the SQLAlchemy models in `deepr/backend/models.py`.
2.  **Generate Migration**: Run the following command to generate a new migration script based on the changes:
    ```bash
    # From deepr/backend directory
    # Ensure your local DB is running (docker compose up db -d)
    DATABASE_URL=postgresql+asyncpg://deepr:deepr_password@localhost/deepr_db ../backend/venv/bin/alembic revision --autogenerate -m "description of changes"
    ```
3.  **Review Migration**: Check the generated file in `deepr/backend/alembic/versions/` to verify it correctly captures the intended changes.
4.  **Apply Migration (Local)**:
    ```bash
    DATABASE_URL=postgresql+asyncpg://deepr:deepr_password@localhost/deepr_db ../backend/venv/bin/alembic upgrade head
    ```
5.  **Commit**: Commit the new migration file and the updated `models.py`.

### Workflow: Applying Changes in Production

In a production environment, you would run the upgrade command as part of the startup script or deployment pipeline:
```bash
alembic upgrade head
```

### Why we wiped the DB this time (2025-12-16)
We encountered a situation where the local database schema was out of sync with the code, and we hadn't established the initial migration history yet. Since it was a local testing environment, it was faster and cleaner to wipe the volume and start fresh. Going forward, we will use the migration workflow described above.
