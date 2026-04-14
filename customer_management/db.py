from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.pool import StaticPool


class Base(DeclarativeBase):
    pass


def normalize_database_url(database_url: str) -> str:
    if database_url.startswith("postgresql+psycopg://"):
        return "postgresql+psycopg2://" + database_url[len("postgresql+psycopg://") :]
    return database_url


def make_engine(database_url: str, *, echo: bool = False):
    database_url = normalize_database_url(database_url)
    engine_kwargs = {"echo": echo, "future": True}
    if database_url.startswith("sqlite:"):
        engine_kwargs["connect_args"] = {"check_same_thread": False}
        if database_url in {"sqlite://", "sqlite:///:memory:"}:
            engine_kwargs["poolclass"] = StaticPool
    return create_engine(database_url, **engine_kwargs)


def make_session_factory(engine):
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
