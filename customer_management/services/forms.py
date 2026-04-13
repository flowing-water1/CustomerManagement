from dataclasses import dataclass, field

from customer_management.repositories.metadata import (
    list_active_custom_fields,
    list_active_tag_groups,
)


@dataclass
class TagOptionSchema:
    id: int
    label: str
    value: str


@dataclass
class TagGroupSchema:
    id: int
    name: str
    code: str
    selection_mode: str
    options: list = field(default_factory=list)


@dataclass
class CustomFieldOptionSchema:
    id: int
    label: str
    value: str


@dataclass
class CustomFieldSchema:
    id: int
    name: str
    code: str
    field_type: str
    is_required: bool
    options: list = field(default_factory=list)


@dataclass
class RecordFormSchema:
    tag_groups: list
    custom_fields: list


def build_record_form_schema(session) -> RecordFormSchema:
    groups, options_by_group_id = list_active_tag_groups(session)
    fields, options_by_field_id = list_active_custom_fields(session)

    tag_groups = [
        TagGroupSchema(
            id=group.id,
            name=group.name,
            code=group.code,
            selection_mode=group.selection_mode,
            options=[
                TagOptionSchema(id=option.id, label=option.label, value=option.value)
                for option in options_by_group_id.get(group.id, [])
            ],
        )
        for group in groups
    ]

    custom_fields = [
        CustomFieldSchema(
            id=field.id,
            name=field.name,
            code=field.code,
            field_type=field.field_type,
            is_required=field.is_required,
            options=[
                CustomFieldOptionSchema(
                    id=option.id, label=option.label, value=option.value
                )
                for option in options_by_field_id.get(field.id, [])
            ],
        )
        for field in fields
    ]

    return RecordFormSchema(tag_groups=tag_groups, custom_fields=custom_fields)
