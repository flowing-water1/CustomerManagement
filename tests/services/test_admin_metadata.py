from customer_management.bootstrap import seed_default_metadata
from customer_management.models import TagOption
from customer_management.repositories.metadata import (
    create_custom_field,
    set_tag_option_active,
)
from customer_management.services.admin_metadata import build_customer_config_snapshot


def test_build_customer_config_snapshot_includes_inactive_tag_items(db_session):
    seed_default_metadata(db_session)
    kunlun = (
        db_session.query(TagOption)
        .filter(TagOption.value == "kunlun")
        .one()
    )
    set_tag_option_active(db_session, kunlun.id, False)

    snapshot = build_customer_config_snapshot(db_session)
    brand_row = next(row for row in snapshot.tag_rows if row.code == "brand")

    assert any(item.label == "昆仑" and item.is_active is False for item in brand_row.items)


def test_build_customer_config_snapshot_includes_field_rows_and_examples(db_session):
    seed_default_metadata(db_session)
    create_custom_field(
        db_session,
        name="采购周期",
        field_type="text",
        is_required=False,
    )

    snapshot = build_customer_config_snapshot(db_session)

    assert snapshot.summary_title == "当前配置情况"
    assert snapshot.field_rows
    assert snapshot.field_helper_examples == ["采购周期", "月需求量", "下次回访时间"]
