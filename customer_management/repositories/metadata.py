from customer_management.models import (
    CustomField,
    CustomFieldOption,
    TagGroup,
    TagOption,
)


def list_active_tag_groups(session):
    groups = (
        session.query(TagGroup)
        .filter(TagGroup.is_active.is_(True))
        .order_by(TagGroup.sort_order.asc(), TagGroup.id.asc())
        .all()
    )
    options = (
        session.query(TagOption)
        .filter(TagOption.is_active.is_(True))
        .order_by(TagOption.sort_order.asc(), TagOption.id.asc())
        .all()
    )
    options_by_group_id = {}
    for option in options:
        options_by_group_id.setdefault(option.group_id, []).append(option)
    return groups, options_by_group_id


def list_active_custom_fields(session):
    fields = (
        session.query(CustomField)
        .filter(CustomField.is_active.is_(True))
        .order_by(CustomField.sort_order.asc(), CustomField.id.asc())
        .all()
    )
    options = (
        session.query(CustomFieldOption)
        .filter(CustomFieldOption.is_active.is_(True))
        .order_by(CustomFieldOption.sort_order.asc(), CustomFieldOption.id.asc())
        .all()
    )
    options_by_field_id = {}
    for option in options:
        options_by_field_id.setdefault(option.field_id, []).append(option)
    return fields, options_by_field_id
