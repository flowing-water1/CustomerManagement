from sqlalchemy import create_engine, inspect, select, text

from customer_management.bootstrap import create_schema, seed_default_metadata
from customer_management.models import TagGroup, TagOption
from customer_management.ui import shared


def test_create_schema_creates_core_tables():
    engine = create_engine("sqlite:///:memory:")

    create_schema(engine)

    tables = set(inspect(engine).get_table_names())

    assert {
        "admin_users",
        "sales_users",
        "customer_records",
        "tag_groups",
        "tag_options",
        "record_tags",
        "custom_fields",
        "custom_field_options",
        "record_field_values",
    } <= tables


def test_seed_default_metadata_inserts_confirmed_tag_options(db_session):
    seed_default_metadata(db_session)

    groups = {group.code for group in db_session.scalars(select(TagGroup)).all()}
    options = {option.value for option in db_session.scalars(select(TagOption)).all()}

    assert {
        "customer_level",
        "customer_type",
        "brand",
        "oil_type",
        "authorized_dealer",
        "other",
    } <= groups
    assert {
        "general",
        "important",
        "converted",
        "not_converted",
        "shell",
        "mobil",
        "greatwall",
        "kunlun",
    } <= options


def test_create_schema_adds_is_test_user_column_to_existing_sales_users_table():
    engine = create_engine("sqlite:///:memory:")

    with engine.begin() as connection:
        connection.execute(
            text(
                """
                CREATE TABLE sales_users (
                    id INTEGER PRIMARY KEY,
                    name VARCHAR(100) NOT NULL UNIQUE,
                    password_hash VARCHAR(255) NOT NULL,
                    is_active BOOLEAN NOT NULL DEFAULT 1,
                    must_change_password BOOLEAN NOT NULL DEFAULT 1,
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
        )

    create_schema(engine)

    columns = {column["name"] for column in inspect(engine).get_columns("sales_users")}

    assert "is_test_user" in columns


def test_get_session_factory_always_bootstraps_on_startup(monkeypatch):
    shared.get_session_factory.clear()
    calls = []
    sentinel_engine = object()

    class DummySessionContext:
        def __enter__(self):
            calls.append(("session_enter",))
            return "session"

        def __exit__(self, exc_type, exc, tb):
            calls.append(("session_exit",))
            return False

    class DummySessionFactory:
        def __call__(self):
            calls.append(("session_call",))
            return DummySessionContext()

    sentinel_session_factory = DummySessionFactory()

    monkeypatch.setattr(
        shared,
        "make_engine",
        lambda database_url: calls.append(("make_engine", database_url)) or sentinel_engine,
    )
    monkeypatch.setattr(
        shared,
        "make_session_factory",
        lambda engine: calls.append(("make_session_factory", engine))
        or sentinel_session_factory,
    )
    monkeypatch.setattr(
        shared,
        "create_schema",
        lambda engine: calls.append(("create_schema", engine)),
    )
    monkeypatch.setattr(
        shared,
        "seed_default_metadata",
        lambda session: calls.append(("seed_default_metadata", session)),
    )

    session_factory = shared.get_session_factory("sqlite://")

    shared.get_session_factory.clear()

    assert session_factory is sentinel_session_factory
    assert calls == [
        ("make_engine", "sqlite://"),
        ("create_schema", sentinel_engine),
        ("make_session_factory", sentinel_engine),
        ("session_call",),
        ("session_enter",),
        ("seed_default_metadata", "session"),
        ("session_exit",),
    ]
