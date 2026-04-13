from customer_management.bootstrap import seed_default_metadata
from customer_management.services.forms import build_record_form_schema


def test_build_record_form_schema_returns_active_tags_and_fields(db_session):
    seed_default_metadata(db_session)

    schema = build_record_form_schema(db_session)

    assert schema.tag_groups
    assert any(group.code == "customer_level" for group in schema.tag_groups)
    assert schema.custom_fields == []
