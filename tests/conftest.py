import asyncio
import os
from dataclasses import dataclass
from dataclasses import field
from typing import Any
from typing import Generator
from typing import TypedDict
from uuid import UUID
from uuid import uuid4

import asyncpg
import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from starlette.testclient import TestClient

import settings
from db.session import get_db
from hashing import Hasher
from main import app
from security import create_access_token

CLEAN_TABLES = [
    "users",
]


class User(TypedDict):
    user_id: UUID
    name: str
    surname: str
    email: str
    is_active: bool


@dataclass
class UserData:
    user_id: UUID = field(default_factory=uuid4)
    name: str = "Boba"
    surname: str = "Bobenko"
    email: str = field(init=False)
    is_active: bool = True
    hashed_password: str = "SampleHashedPass"

    def __post_init__(self):
        self.email = f"boba{str(self.user_id)[:6]}@boba.com"


async def create_sample_user(create_user_in_database) -> UserData:
    user_data = UserData()
    await create_user_in_database(**user_data.__dict__)
    return user_data


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
async def run_migrations():
    os.system("alembic init migrations")
    os.system('alembic revision --autogenerate -m "test running migrations"')
    os.system("alembic upgrade heads")


@pytest.fixture(scope="session")
async def async_session_test():
    engine = create_async_engine(settings.TEST_DATABASE_URL, future=True, echo=True)
    async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    yield async_session


@pytest.fixture(scope="function", autouse=True)
async def clean_tables(async_session_test):
    """Clean data in all tables before running test function"""
    async with async_session_test() as session, session.begin():
        for table_for_cleaning in CLEAN_TABLES:
            await session.execute(text(f"""TRUNCATE TABLE {table_for_cleaning};"""))


async def _get_test_db():
    try:
        # create async engine for interaction with database
        test_engine = create_async_engine(
            url=settings.TEST_DATABASE_URL, future=True, echo=True
        )

        # create session for the interaction with database
        test_async_session = sessionmaker(
            test_engine, expire_on_commit=False, class_=AsyncSession
        )
        yield test_async_session()
    finally:
        pass


@pytest.fixture(scope="function")
async def client() -> Generator[TestClient, Any, None]:
    """
    Create a new FastAPI TestClient that uses the `db_session` fixture to override
    the `get_db` dependency that is injected into routes.
    """

    app.dependency_overrides[get_db] = _get_test_db
    with TestClient(app) as client:
        yield client


@pytest.fixture(scope="session")
async def asyncpg_pool():
    pool = await asyncpg.create_pool(
        "".join(settings.TEST_DATABASE_URL.split("+asyncpg"))
    )
    yield pool
    pool.close()


@pytest.fixture
async def get_user_from_database(asyncpg_pool):
    async def get_user_from_database_by_uuid(user_id: str):
        async with asyncpg_pool.acquire() as connection:
            return await connection.fetch(
                """SELECT * FROM users WHERE user_id = $1;""", user_id
            )

    return get_user_from_database_by_uuid


@pytest.fixture
async def create_user_in_database(asyncpg_pool):
    async def create_user_in_database(
        user_id: str,
        name: str,
        surname: str,
        email: str,
        is_active: bool,
        hashed_password: str,
    ):
        async with asyncpg_pool.acquire() as connection:
            return await connection.execute(
                """INSERT INTO users VALUES ($1, $2, $3, $4, $5, $6)""",
                user_id,
                name,
                surname,
                email,
                is_active,
                Hasher.get_password_hash(hashed_password),
            )

    return create_user_in_database


def create_test_auth_headers_for_user(email: str) -> dict[str, str]:
    token = create_access_token(data={"sub": email})
    return {"Authorization": f"Bearer {token}"}


def create_bad_test_auth_headers_for_user(email: str) -> dict[str, str]:
    token = create_access_token(data={"sub": email}) + "crycazyabra"
    return {"Authorization": f"Bearer {token}"}
