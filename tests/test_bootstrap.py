from sqlalchemy import create_engine, inspect

from customer_management.bootstrap import create_schema


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
