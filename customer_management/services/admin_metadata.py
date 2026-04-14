from dataclasses import dataclass, field

from customer_management.repositories.metadata import (
    list_custom_field_options,
    list_custom_fields,
    list_tag_groups,
    list_tag_options,
)


FIELD_TYPE_LABELS = {
    "text": "文本",
    "textarea": "多行文本",
    "number": "数字",
    "date": "日期",
    "select": "下拉选项",
}

SELECTION_MODE_LABELS = {
    "single": "单选",
    "multiple": "多选",
}

FIELD_HELPER_EXAMPLES = ["采购周期", "月需求量", "下次回访时间"]


@dataclass
class SummaryItem:
    label: str
    is_active: bool


@dataclass
class SummaryRow:
    id: int
    code: str
    name: str
    subtitle: str
    items: list[SummaryItem] = field(default_factory=list)


@dataclass
class CustomerConfigSnapshot:
    summary_title: str
    tag_rows: list[SummaryRow]
    field_rows: list[SummaryRow]
    field_helper_examples: list[str]


def build_customer_config_snapshot(session) -> CustomerConfigSnapshot:
    tag_groups = list_tag_groups(session)
    tag_options = list_tag_options(session)
    custom_fields = list_custom_fields(session)
    custom_field_options = list_custom_field_options(session)

    tag_options_by_group_id = {}
    for option in tag_options:
        tag_options_by_group_id.setdefault(option.group_id, []).append(
            SummaryItem(label=option.label, is_active=option.is_active)
        )

    field_options_by_field_id = {}
    for option in custom_field_options:
        field_options_by_field_id.setdefault(option.field_id, []).append(
            SummaryItem(label=option.label, is_active=option.is_active)
        )

    tag_rows = [
        SummaryRow(
            id=group.id,
            code=group.code,
            name=group.name,
            subtitle=SELECTION_MODE_LABELS.get(group.selection_mode, group.selection_mode),
            items=tag_options_by_group_id.get(group.id, []),
        )
        for group in tag_groups
    ]

    field_rows = [
        SummaryRow(
            id=field.id,
            code=field.code,
            name=field.name,
            subtitle=_format_field_subtitle(field.field_type, field.is_required),
            items=field_options_by_field_id.get(field.id, []),
        )
        for field in custom_fields
    ]

    return CustomerConfigSnapshot(
        summary_title="当前配置情况",
        tag_rows=tag_rows,
        field_rows=field_rows,
        field_helper_examples=FIELD_HELPER_EXAMPLES,
    )


def _format_field_subtitle(field_type: str, is_required: bool) -> str:
    subtitle = FIELD_TYPE_LABELS.get(field_type, field_type)
    if is_required:
        return f"{subtitle} / 必填"
    return subtitle
