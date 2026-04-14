from customer_management.repositories.metadata import (
    create_custom_field,
    create_custom_field_option,
    create_tag_group,
    create_tag_option,
    update_custom_field,
    update_custom_field_option,
    update_tag_group,
    update_tag_option,
)


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
