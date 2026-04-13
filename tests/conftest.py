import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from customer_management.bootstrap import create_schema
from customer_management.db import make_session_factory
from customer_management.models import TagOption
from customer_management.repositories.records import create_record
from customer_management.repositories.sales_users import create_sales_user
from customer_management.bootstrap import seed_default_metadata


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


@pytest.fixture
def dashboard_seed_data(db_session):
    seed_default_metadata(db_session)
    alice = create_sales_user(
        db_session, name="Alice", password="alice-pass", must_change_password=False
    )
    bob = create_sales_user(
        db_session, name="Bob", password="bob-pass", must_change_password=False
    )

    option_ids = {
        option.value: option.id
        for option in db_session.query(TagOption).all()
    }

    create_record(
        db_session,
        sales_user_id=alice.id,
        customer_name="ACME",
        contact_name="Bob",
        phone="13800000000",
        remark="first",
        selected_option_ids=[
            option_ids["general"],
            option_ids["converted"],
            option_ids["shell"],
        ],
        custom_field_values={},
    )
    create_record(
        db_session,
        sales_user_id=alice.id,
        customer_name="Globex",
        contact_name="Ada",
        phone="13900000000",
        remark="second",
        selected_option_ids=[
            option_ids["important"],
            option_ids["not_converted"],
            option_ids["mobil"],
        ],
        custom_field_values={},
    )
    create_record(
        db_session,
        sales_user_id=bob.id,
        customer_name="Initech",
        contact_name="Ken",
        phone="13700000000",
        remark="third",
        selected_option_ids=[
            option_ids["general"],
            option_ids["converted"],
            option_ids["greatwall"],
        ],
        custom_field_values={},
    )

    return {"alice": alice, "bob": bob}
