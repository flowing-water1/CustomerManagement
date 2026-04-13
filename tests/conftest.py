import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from customer_management.bootstrap import create_schema
from customer_management.db import make_session_factory


@pytest.fixture
def db_engine():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    create_schema(engine)
    try:
        yield engine
    finally:
        engine.dispose()


@pytest.fixture
def db_session(db_engine):
    session_factory = make_session_factory(db_engine)
    session = session_factory()
    try:
        yield session
    finally:
        session.close()
