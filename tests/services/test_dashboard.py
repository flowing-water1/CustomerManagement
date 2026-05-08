from customer_management.bootstrap import seed_default_metadata
from customer_management.models import TagOption
from customer_management.repositories.records import create_record
from customer_management.repositories.sales_users import create_sales_user
import pytest

from customer_management.services.dashboard import build_dashboard_snapshot, list_admin_records


def test_build_dashboard_snapshot_returns_totals_rankings_and_distributions(
    db_session, dashboard_seed_data
):
    snapshot = build_dashboard_snapshot(db_session)

    assert snapshot.total_records == 3
    assert snapshot.sales_rankings[0].count >= snapshot.sales_rankings[-1].count
    assert any(item.group_code == "customer_type" for item in snapshot.tag_distributions)
    assert {item.label: item.count for item in snapshot.customer_level_distribution} == {
        "一般": 2,
        "重要": 1,
    }
    assert {item.label: item.count for item in snapshot.customer_type_distribution} == {
        "已成交": 2,
        "未成交": 1,
    }
    assert not hasattr(snapshot, "cross_statistics")


@pytest.mark.parametrize(
    ("query", "expected_customer_names"),
    [
        ("ACME", ["ACME"]),
        ("Ada", ["Globex"]),
        ("13700000000", ["Initech"]),
        ("second", ["Globex"]),
    ],
)
def test_list_admin_records_filters_by_search_query(
    db_session, dashboard_seed_data, query, expected_customer_names
):
    records = list_admin_records(db_session, query=query)

    assert [record["customer_name"] for record in records] == expected_customer_names


def test_build_dashboard_snapshot_can_filter_by_test_user_flag(db_session):
    seed_default_metadata(db_session)
    alice = create_sales_user(
        db_session,
        name="Alice",
        password="alice-pass",
        must_change_password=False,
    )
    tester = create_sales_user(
        db_session,
        name="Tester",
        password="tester-pass",
        must_change_password=False,
        is_test_user=True,
    )
    option_ids = {
        option.value: option.id for option in db_session.query(TagOption).all()
    }

    create_record(
        db_session,
        sales_user_id=alice.id,
        customer_name="ACME",
        contact_name="Bob",
        phone="13800000000",
        remark="normal",
        selected_option_ids=[
            option_ids["general"],
            option_ids["converted"],
            option_ids["shell"],
        ],
        custom_field_values={},
    )
    create_record(
        db_session,
        sales_user_id=tester.id,
        customer_name="Test Corp",
        contact_name="Mock",
        phone="13900000000",
        remark="test",
        selected_option_ids=[
            option_ids["important"],
            option_ids["not_converted"],
            option_ids["mobil"],
        ],
        custom_field_values={},
    )

    snapshot = build_dashboard_snapshot(db_session, is_test_user=False)
    test_snapshot = build_dashboard_snapshot(db_session, is_test_user=True)

    assert snapshot.total_records == 1
    assert snapshot.active_sales_count == 1
    assert [(item.label, item.count) for item in snapshot.sales_rankings] == [("Alice", 1)]
    assert {item.label: item.count for item in snapshot.customer_level_distribution} == {
        "一般": 1
    }
    assert {item.label: item.count for item in snapshot.customer_type_distribution} == {
        "已成交": 1
    }
    assert test_snapshot.total_records == 1
    assert test_snapshot.active_sales_count == 1
    assert [(item.label, item.count) for item in test_snapshot.sales_rankings] == [
        ("Tester", 1)
    ]
    assert {item.label: item.count for item in test_snapshot.customer_level_distribution} == {
        "重要": 1
    }
    assert {item.label: item.count for item in test_snapshot.customer_type_distribution} == {
        "未成交": 1
    }
