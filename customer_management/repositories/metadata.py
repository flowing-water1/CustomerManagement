import re
from typing import Optional

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


def list_tag_groups(session):
    return session.query(TagGroup).order_by(TagGroup.sort_order.asc(), TagGroup.id.asc()).all()


def list_tag_options(session, group_id=None):
    query = session.query(TagOption)
    if group_id is not None:
        query = query.filter(TagOption.group_id == group_id)
    return query.order_by(TagOption.sort_order.asc(), TagOption.id.asc()).all()


def create_tag_group(
    session, *, name: str, selection_mode: str, code: Optional[str] = None
):
    group = TagGroup(
        name=name.strip(),
        code=_make_unique_text(session, TagGroup, "code", code or name, "tag_group"),
        selection_mode=selection_mode,
        sort_order=_next_sort_order(session, TagGroup),
        is_active=True,
    )
    session.add(group)
    session.commit()
    session.refresh(group)
    return group


def set_tag_group_active(session, group_id: int, is_active: bool):
    group = session.get(TagGroup, group_id)
    if group is None:
        raise ValueError("Tag group not found")
    group.is_active = is_active
    session.add(group)
    session.commit()
    session.refresh(group)
    return group


def create_tag_option(
    session, *, group_id: int, label: str, value: Optional[str] = None
):
    option = TagOption(
        group_id=group_id,
        label=label.strip(),
        value=_make_unique_text(session, TagOption, "value", value or label, "tag_option"),
        sort_order=_next_sort_order(session, TagOption, group_id=group_id),
        is_active=True,
    )
    session.add(option)
    session.commit()
    session.refresh(option)
    return option


def set_tag_option_active(session, option_id: int, is_active: bool):
    option = session.get(TagOption, option_id)
    if option is None:
        raise ValueError("Tag option not found")
    option.is_active = is_active
    session.add(option)
    session.commit()
    session.refresh(option)
    return option


def list_custom_fields(session):
    return (
        session.query(CustomField)
        .order_by(CustomField.sort_order.asc(), CustomField.id.asc())
        .all()
    )


def list_custom_field_options(session, field_id=None):
    query = session.query(CustomFieldOption)
    if field_id is not None:
        query = query.filter(CustomFieldOption.field_id == field_id)
    return query.order_by(CustomFieldOption.sort_order.asc(), CustomFieldOption.id.asc()).all()


def create_custom_field(
    session,
    *,
    name: str,
    field_type: str,
    is_required: bool,
    code: Optional[str] = None,
):
    field = CustomField(
        name=name.strip(),
        code=_make_unique_text(
            session, CustomField, "code", code or name, "custom_field"
        ),
        field_type=field_type,
        is_required=is_required,
        sort_order=_next_sort_order(session, CustomField),
        is_active=True,
    )
    session.add(field)
    session.commit()
    session.refresh(field)
    return field


def set_custom_field_active(session, field_id: int, is_active: bool):
    field = session.get(CustomField, field_id)
    if field is None:
        raise ValueError("Custom field not found")
    field.is_active = is_active
    session.add(field)
    session.commit()
    session.refresh(field)
    return field


def create_custom_field_option(
    session, *, field_id: int, label: str, value: Optional[str] = None
):
    option = CustomFieldOption(
        field_id=field_id,
        label=label.strip(),
        value=_make_unique_text(
            session,
            CustomFieldOption,
            "value",
            value or label,
            "custom_field_option",
        ),
        sort_order=_next_sort_order(session, CustomFieldOption, field_id=field_id),
        is_active=True,
    )
    session.add(option)
    session.commit()
    session.refresh(option)
    return option


def set_custom_field_option_active(session, option_id: int, is_active: bool):
    option = session.get(CustomFieldOption, option_id)
    if option is None:
        raise ValueError("Custom field option not found")
    option.is_active = is_active
    session.add(option)
    session.commit()
    session.refresh(option)
    return option


def _make_unique_text(session, model, field_name: str, raw_value: str, prefix: str):
    base = re.sub(r"[^a-z0-9]+", "_", raw_value.lower()).strip("_")
    if not base:
        base = prefix
    candidate = base
    counter = 1
    column = getattr(model, field_name)
    while session.query(model).filter(column == candidate).one_or_none() is not None:
        counter += 1
        candidate = f"{base}_{counter}"
    return candidate


def _next_sort_order(session, model, group_id=None, field_id=None):
    query = session.query(model)
    if group_id is not None and hasattr(model, "group_id"):
        query = query.filter(model.group_id == group_id)
    if field_id is not None and hasattr(model, "field_id"):
        query = query.filter(model.field_id == field_id)
    count = query.count()
    return (count + 1) * 10
