import uuid

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from src.core.database import init_db
from src.main import app


@pytest_asyncio.fixture(scope="session")
async def prepare_db():
    await init_db()
    yield


@pytest_asyncio.fixture
async def client(prepare_db):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def sample_customer_external_id() -> str:
    return f"cust-{uuid.uuid4().hex[:8]}"
