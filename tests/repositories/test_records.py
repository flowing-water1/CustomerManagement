from customer_management.bootstrap import seed_default_metadata
from customer_management.repositories.records import (
    create_record,
    delete_record,
    list_records_for_sales_user,
    update_record,
)
from customer_management.repositories.sales_users import create_sales_user


def test_sales_user_crud_only_returns_owned_records(db_session):
    seed_default_metadata(db_session)
    sales_user = create_sales_user(
        db_session,
        name="Alice",
        password="temp-pass",
        must_change_password=False,
    )

    created = create_record(
        db_session,
        sales_user_id=sales_user.id,
        customer_name="ACME",
        contact_name="Bob",
        phone="13800000000",
        remark="first",
        selected_option_ids=[],
        custom_field_values={},
    )

    records = list_records_for_sales_user(db_session, sales_user.id, query="ACME")
    assert [record.id for record in records] == [created.id]

    update_record(
        db_session,
        record_id=created.id,
        sales_user_id=sales_user.id,
        customer_name="ACME Updated",
        contact_name="Bob",
        phone="13800000000",
        remark="changed",
        selected_option_ids=[],
        custom_field_values={},
    )

    delete_record(db_session, record_id=created.id, sales_user_id=sales_user.id)
    assert list_records_for_sales_user(db_session, sales_user.id) == []
