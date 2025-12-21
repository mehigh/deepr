import pytest
import asyncio
from httpx import AsyncClient, ASGITransport
import json
# Assuming PYTHONPATH includes deepr/backend
from main import app
from database import get_db, Base, engine
from models import User, UserSettings, NodeType
from auth import create_access_token
from encryption import encrypt_key
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# Configure asyncio mode
pytest_plugins = ('pytest_asyncio',)

@pytest.fixture(scope="session")
def event_loop_policy():
    return asyncio.get_event_loop_policy()

@pytest.fixture(scope="function")
async def db_engine():
    # Use in-memory SQLite for testing
    # We need a new engine for in-memory to ensure it persists across the test
    test_engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=True)
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield test_engine
    await test_engine.dispose()

@pytest.fixture(scope="function")
async def db_session(db_engine):
    async_session = sessionmaker(
        db_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        yield session

@pytest.fixture(scope="function")
async def client(db_session):
    # Override get_db dependency to use the same session (for in-memory DB sharing)
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()

@pytest.fixture(scope="function")
async def auth_token(client, db_session):
    # Create test user
    email = "test@example.com"
    user = User(email=email)
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    # Add settings with API key
    import os
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        pytest.fail("OPENROUTER_API_KEY environment variable not set")

    encrypted_key = encrypt_key(api_key, user.id)
    settings = UserSettings(user_id=user.id, encrypted_api_key=encrypted_key)
    db_session.add(settings)
    await db_session.commit()

    # Generate token
    token = create_access_token(data={"sub": email})
    return token

@pytest.mark.asyncio
async def test_ensemble_method(client, auth_token):
    headers = {"Authorization": f"Bearer {auth_token}"}

    payload = {
        "prompt": "What is the capital of France? One word answer.",
        "council_members": ["openai/gpt-3.5-turbo", "openai/gpt-3.5-turbo"],
        "chairman_model": "openai/gpt-3.5-turbo",
        "method": "ensemble"
    }

    print("Starting request...")
    # Increase timeout for the request
    async with client.stream("POST", "/council/run", json=payload, headers=headers, timeout=60.0) as response:
        assert response.status_code == 200
        print("Response received. Reading stream...")

        events = []
        async for line in response.aiter_lines():
            print(f"Received line: {line}")
            if line.startswith("data: "):
                data = json.loads(line[6:])
                events.append(data)
                if data['type'] == 'error':
                    print(f"Error from server: {data['message']}")
                if data['type'] == 'done':
                    print("Received done event")

        types = [e['type'] for e in events]
        assert 'start' in types
        assert 'node' in types

        nodes = [e.get('node') for e in events if e.get('type') == 'node']

        research_nodes = [n for n in nodes if n['type'] == 'research']
        synthesis_nodes = [n for n in nodes if n['type'] == 'synthesis']

        assert len(research_nodes) > 0
        assert len(synthesis_nodes) == 1

        print("Research Content:", [n['content'] for n in research_nodes])
        print("Synthesis Content:", synthesis_nodes[0]['content'])

        assert "Paris" in synthesis_nodes[0]['content']

@pytest.mark.asyncio
async def test_dag_method(client, auth_token):
    headers = {"Authorization": f"Bearer {auth_token}"}

    payload = {
        "prompt": "Is the earth flat? One word answer.",
        "council_members": ["openai/gpt-3.5-turbo"],
        "chairman_model": "openai/gpt-3.5-turbo",
        "method": "dag"
    }

    print("Starting DAG request...")
    async with client.stream("POST", "/council/run", json=payload, headers=headers, timeout=60.0) as response:
        assert response.status_code == 200
        print("Response received. Reading stream...")

        events = []
        async for line in response.aiter_lines():
            print(f"Received line: {line}")
            if line.startswith("data: "):
                data = json.loads(line[6:])
                events.append(data)
                if data['type'] == 'done':
                    break

        node_types = [e['node']['type'] for e in events if e.get('type') == 'node']
        assert 'plan' in node_types
        assert 'research' in node_types
