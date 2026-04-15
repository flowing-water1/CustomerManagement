import pytest

from customer_management.bootstrap import seed_default_metadata
from customer_management.models import CustomField, CustomFieldOption, TagGroup, TagOption
from customer_management.repositories.metadata import (
    can_delete_custom_field,
    can_delete_custom_field_option,
    can_delete_tag_group,
    can_delete_tag_option,
    create_custom_field,
    create_custom_field_option,
    create_tag_group,
    create_tag_option,
    delete_custom_field,
    delete_custom_field_option,
    delete_tag_group,
    delete_tag_option,
    update_custom_field,
    update_custom_field_option,
    update_tag_group,
    update_tag_option,
)
from customer_management.repositories.records import create_record
from customer_management.repositories.sales_users import create_sales_user


def test_update_tag_group_and_option_persists_business_labels(db_session):
    group = create_tag_group(db_session, name="品牌", selection_mode="single")
    option = create_tag_option(db_session, group_id=group.id, label="壳牌")

    updated_group = update_tag_group(
        db_session,
        group_id=group.id,
        name="客户品牌",
        selection_mode="multiple",
    )
    updated_option = update_tag_option(
        db_session,
        option_id=option.id,
        label="美孚",
    )

    assert updated_group.name == "客户品牌"
    assert updated_group.selection_mode == "multiple"
    assert updated_option.label == "美孚"


def test_update_custom_field_and_option_persists_required_state(db_session):
    field = create_custom_field(
        db_session,
        name="采购周期",
        field_type="select",
        is_required=False,
    )
    option = create_custom_field_option(db_session, field_id=field.id, label="月结")

    updated_field = update_custom_field(
        db_session,
        field_id=field.id,
        name="采购周期（月）",
        field_type="select",
        is_required=True,
    )
    updated_option = update_custom_field_option(
        db_session,
        option_id=option.id,
        label="现结",
    )

    assert updated_field.name == "采购周期（月）"
    assert updated_field.is_required is True
    assert updated_option.label == "现结"


def test_unused_tag_group_and_option_can_be_deleted(db_session):
    group = create_tag_group(db_session, name="临时分类", selection_mode="single")
    option = create_tag_option(db_session, group_id=group.id, label="临时选项")

    assert can_delete_tag_group(db_session, group.id) is True
    assert can_delete_tag_option(db_session, option.id) is True

    delete_tag_option(db_session, option.id)
    delete_tag_group(db_session, group.id)

    assert db_session.get(TagOption, option.id) is None
    assert db_session.get(TagGroup, group.id) is None


def test_used_tag_group_and_option_cannot_be_deleted(db_session):
    seed_default_metadata(db_session)
    sales_user = create_sales_user(
        db_session,
        name="Alice",
        password="alice-pass",
        must_change_password=False,
    )

    brand_options = {
        option.label: option
        for option in db_session.query(TagOption)
        .join(TagGroup, TagGroup.id == TagOption.group_id)
        .filter(TagGroup.code == "brand")
        .all()
    }
    brand_group = db_session.query(TagGroup).filter(TagGroup.code == "brand").one()
    used_option = brand_options["壳牌"]
    unused_option = brand_options["昆仑"]

    create_record(
        db_session,
        sales_user_id=sales_user.id,
        customer_name="ACME",
        contact_name="Bob",
        phone="13800000000",
        remark="first",
        selected_option_ids=[used_option.id],
        custom_field_values={},
    )

    assert can_delete_tag_group(db_session, brand_group.id) is False
    assert can_delete_tag_option(db_session, used_option.id) is False
    assert can_delete_tag_option(db_session, unused_option.id) is True

    with pytest.raises(ValueError):
        delete_tag_group(db_session, brand_group.id)
    with pytest.raises(ValueError):
        delete_tag_option(db_session, used_option.id)


def test_unused_custom_field_and_option_can_be_deleted(db_session):
    field = create_custom_field(
        db_session,
        name="临时字段",
        field_type="select",
        is_required=False,
    )
    option = create_custom_field_option(
        db_session,
        field_id=field.id,
        label="临时字段选项",
    )

    assert can_delete_custom_field(db_session, field.id) is True
    assert can_delete_custom_field_option(db_session, option.id) is True

    delete_custom_field_option(db_session, option.id)
    delete_custom_field(db_session, field.id)

    assert db_session.get(CustomFieldOption, option.id) is None
    assert db_session.get(CustomField, field.id) is None


def test_used_custom_field_and_option_cannot_be_deleted(db_session):
    sales_user = create_sales_user(
        db_session,
        name="Alice",
        password="alice-pass",
        must_change_password=False,
    )
    field = create_custom_field(
        db_session,
        name="采购周期",
        field_type="select",
        is_required=False,
    )
    used_option = create_custom_field_option(
        db_session,
        field_id=field.id,
        label="月结",
    )
    unused_option = create_custom_field_option(
        db_session,
        field_id=field.id,
        label="现结",
    )

    create_record(
        db_session,
        sales_user_id=sales_user.id,
        customer_name="ACME",
        contact_name="Bob",
        phone="13800000000",
        remark="first",
        selected_option_ids=[],
        custom_field_values={field.id: used_option.value},
    )

    assert can_delete_custom_field(db_session, field.id) is False
    assert can_delete_custom_field_option(db_session, used_option.id) is False
    assert can_delete_custom_field_option(db_session, unused_option.id) is True

    with pytest.raises(ValueError):
        delete_custom_field(db_session, field.id)
    with pytest.raises(ValueError):
        delete_custom_field_option(db_session, used_option.id)
