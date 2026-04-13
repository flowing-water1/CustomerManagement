from sqlalchemy import create_engine, inspect, select

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
