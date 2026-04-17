from sqlalchemy import create_engine, inspect, select, text

from customer_management.bootstrap import create_schema, seed_default_metadata
from customer_management.models import TagGroup, TagOption


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
