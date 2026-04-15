import streamlit as st

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
    list_custom_field_options,
    list_custom_fields,
    list_tag_groups,
    list_tag_options,
    set_custom_field_active,
    set_custom_field_option_active,
    set_tag_group_active,
    set_tag_option_active,
    update_custom_field,
)
from customer_management.services.admin_metadata import (
    FIELD_HELPER_EXAMPLES,
    FIELD_TYPE_LABELS,
    SummaryItem,
    build_customer_config_snapshot,
)

FOCUS_KIND_KEY = "admin_customer_config_focus_kind"
FOCUS_CODE_KEY = "admin_customer_config_focus_code"


def render_customer_config(session):
    st.markdown("#### 客户资料配置")
    st.markdown(
        "这里展示销售当前会用到的客户分类和补充资料。你在这里修改后，销售录入页会同步变化。"
    )
    st.divider()

    summary_container = st.container()
    st.divider()
    _render_tag_section(session)
    st.divider()
    _render_field_section(session, FIELD_HELPER_EXAMPLES)

    snapshot = build_customer_config_snapshot(session)
    with summary_container:
        _render_summary_card(session, snapshot)


def _render_summary_card(session, snapshot):
    st.markdown(f"#### {snapshot.summary_title}")
    st.markdown("先看现在怎么配，再决定改哪里。")

    for row in snapshot.tag_rows:
        row_container = st.container()
        editor_container = st.container()
        if _is_focused("tag", row.code):
            with editor_container:
                st.divider()
                _render_tag_quick_edit(session, row)
        with row_container:
            info_column, action_column = st.columns([5, 1])
            with info_column:
                values = " / ".join(_format_items(row.items))
                st.markdown(f"**{row.name}**：{values}")
            with action_column:
                st.button(
                    "修改",
                    key=f"admin_summary_focus_tag_{row.code}",
                    on_click=_set_focus,
                    args=("tag", row.code),
                )

    if snapshot.field_rows:
        st.markdown(
            "**补充字段**："
            + " / ".join(field.name for field in snapshot.field_rows)
        )
        for row in snapshot.field_rows:
            row_container = st.container()
            editor_container = st.container()
            if _is_focused("field", row.code):
                with editor_container:
                    st.divider()
                    _render_field_quick_edit(session, row)
            with row_container:
                info_column, action_column = st.columns([5, 1])
                with info_column:
                    st.markdown(f"**{row.name}**（{row.subtitle}）")
                with action_column:
                    st.button(
                        "修改",
                        key=f"admin_summary_focus_field_{row.code}",
                        on_click=_set_focus,
                        args=("field", row.code),
                    )


def _render_tag_section(session):
    st.markdown("#### 标签区")
    st.markdown("标签用于给客户分类，方便销售选择，也方便后续筛选和统计。")

    tag_groups = list_tag_groups(session)
    tag_options = list_tag_options(session)

    with st.form("admin_customer_config_create_tag_group_form"):
        name = st.text_input("新增分类名称", key="admin_customer_config_new_tag_group_name")
        selection_mode = st.selectbox(
            "分类选择方式",
            ["single", "multiple"],
            format_func=lambda item: "单选" if item == "single" else "多选",
            key="admin_customer_config_new_tag_group_mode",
        )
        submitted = st.form_submit_button("新增分类")
        if submitted:
            if not name:
                st.error("分类名称不能为空")
                return
            create_tag_group(session, name=name, selection_mode=selection_mode)
            tag_groups = list_tag_groups(session)
            tag_options = list_tag_options(session)

    if tag_groups:
        selected_group = st.selectbox(
            "选择分类进行启停",
            tag_groups,
            format_func=lambda item: f"{item.name} ({'启用' if item.is_active else '停用'})",
            key="admin_customer_config_toggle_tag_group",
        )
        toggle_column, delete_column = st.columns([1, 1])
        button_label = "停用分类" if selected_group.is_active else "启用分类"
        with toggle_column:
            if st.button(
                button_label,
                key="admin_customer_config_toggle_tag_group_button",
            ):
                set_tag_group_active(session, selected_group.id, not selected_group.is_active)
                tag_groups = list_tag_groups(session)
                tag_options = list_tag_options(session)
        with delete_column:
            if can_delete_tag_group(session, selected_group.id) and st.button(
                "删除分类",
                key="admin_delete_tag_group_button",
            ):
                delete_tag_group(session, selected_group.id)
                tag_groups = list_tag_groups(session)
                tag_options = list_tag_options(session)

    if tag_groups:
        with st.form("admin_customer_config_create_tag_option_form"):
            selected_group = st.selectbox(
                "选择分类新增选项",
                tag_groups,
                format_func=lambda item: item.name,
                key="admin_customer_config_new_tag_option_group",
            )
            label = st.text_input("新增选项名称", key="admin_customer_config_new_tag_option_label")
            submitted = st.form_submit_button("新增选项")
            if submitted:
                if not label:
                    st.error("标签选项名称不能为空")
                    return
                create_tag_option(session, group_id=selected_group.id, label=label)
                tag_groups = list_tag_groups(session)
                tag_options = list_tag_options(session)

    if tag_options:
        selected_option = st.selectbox(
            "选择标签选项进行启停",
            tag_options,
            format_func=lambda item: f"{item.label} ({'启用' if item.is_active else '停用'})",
            key="admin_customer_config_toggle_tag_option",
        )
        toggle_column, delete_column = st.columns([1, 1])
        button_label = "停用标签选项" if selected_option.is_active else "启用标签选项"
        with toggle_column:
            if st.button(
                button_label,
                key="admin_customer_config_toggle_tag_option_button",
            ):
                set_tag_option_active(session, selected_option.id, not selected_option.is_active)
                tag_options = list_tag_options(session)
        with delete_column:
            if can_delete_tag_option(session, selected_option.id) and st.button(
                "删除标签选项",
                key="admin_delete_tag_option_button",
            ):
                delete_tag_option(session, selected_option.id)
                tag_options = list_tag_options(session)


def _render_field_section(session, field_helper_examples):
    st.markdown("#### 字段区")
    st.markdown("字段用于补充客户资料，比如采购周期、月需求量、下次回访时间。")
    st.markdown(
        "常见补充字段："
        + " / ".join(field_helper_examples)
    )

    custom_fields = list_custom_fields(session)
    field_options = list_custom_field_options(session)

    with st.form("admin_customer_config_create_custom_field_form"):
        name = st.text_input("新增字段名称", key="admin_customer_config_new_custom_field_name")
        field_type = st.selectbox(
            "字段类型",
            ["text", "textarea", "number", "date", "select"],
            format_func=lambda item: {
                "text": "文本",
                "textarea": "多行文本",
                "number": "数字",
                "date": "日期",
                "select": "下拉选项",
            }[item],
            key="admin_customer_config_new_custom_field_type",
        )
        is_required = st.checkbox("销售录入时必填", key="admin_customer_config_new_custom_field_required")
        submitted = st.form_submit_button("新增字段")
        if submitted:
            if not name:
                st.error("字段名称不能为空")
                return
            create_custom_field(
                session,
                name=name,
                field_type=field_type,
                is_required=is_required,
            )
            custom_fields = list_custom_fields(session)
            field_options = list_custom_field_options(session)

    if custom_fields:
        selected_field = st.selectbox(
            "选择字段进行启停",
            custom_fields,
            format_func=lambda item: f"{item.name} ({'启用' if item.is_active else '停用'})",
            key="admin_customer_config_toggle_field",
        )
        toggle_column, delete_column = st.columns([1, 1])
        button_label = "停用字段" if selected_field.is_active else "启用字段"
        with toggle_column:
            if st.button(
                button_label,
                key="admin_customer_config_toggle_field_button",
            ):
                set_custom_field_active(session, selected_field.id, not selected_field.is_active)
                custom_fields = list_custom_fields(session)
                field_options = list_custom_field_options(session)
        with delete_column:
            if can_delete_custom_field(session, selected_field.id) and st.button(
                "删除字段",
                key="admin_delete_custom_field_button",
            ):
                delete_custom_field(session, selected_field.id)
                custom_fields = list_custom_fields(session)
                field_options = list_custom_field_options(session)

    select_fields = [field for field in custom_fields if field.field_type == "select"]
    if select_fields:
        with st.form("admin_customer_config_create_field_option_form"):
            selected_field = st.selectbox(
                "选择字段新增选项",
                select_fields,
                format_func=lambda item: item.name,
                key="admin_customer_config_new_field_option_field",
            )
            label = st.text_input("新增字段选项名称", key="admin_customer_config_new_field_option_label")
            submitted = st.form_submit_button("新增字段选项")
            if submitted:
                if not label:
                    st.error("字段选项名称不能为空")
                    return
                create_custom_field_option(session, field_id=selected_field.id, label=label)
                field_options = list_custom_field_options(session)

    if field_options:
        selected_option = st.selectbox(
            "选择字段选项进行启停",
            field_options,
            format_func=lambda item: f"{item.label} ({'启用' if item.is_active else '停用'})",
            key="admin_customer_config_toggle_field_option",
        )
        toggle_column, delete_column = st.columns([1, 1])
        button_label = "停用字段选项" if selected_option.is_active else "启用字段选项"
        with toggle_column:
            if st.button(
                button_label,
                key="admin_customer_config_toggle_field_option_button",
            ):
                set_custom_field_option_active(
                    session, selected_option.id, not selected_option.is_active
                )
                field_options = list_custom_field_options(session)
        with delete_column:
            if can_delete_custom_field_option(session, selected_option.id) and st.button(
                "删除字段选项",
                key="admin_delete_custom_field_option_button",
            ):
                delete_custom_field_option(session, selected_option.id)
                field_options = list_custom_field_options(session)


def _render_tag_quick_edit(session, row):
    st.markdown(f"为 **{row.name}** 快速新增或启停选项")
    with st.form(f"admin_quick_tag_form_{row.code}", clear_on_submit=True):
        st.text_input(
            "新增选项名称",
            key=f"admin_quick_tag_option_label_{row.code}",
        )
        submitted = st.form_submit_button("新增选项")
        if submitted:
            label = st.session_state.get(f"admin_quick_tag_option_label_{row.code}", "").strip()
            if not label:
                st.error("标签选项名称不能为空")
                return
            create_tag_option(session, group_id=row.id, label=label)
            row.items.append(SummaryItem(label=label, is_active=True))

    group_options = list_tag_options(session, group_id=row.id)
    if group_options:
        selected_option = st.selectbox(
            "选择标签选项进行启停",
            group_options,
            format_func=lambda item: f"{item.label} ({'启用' if item.is_active else '停用'})",
            key=f"admin_quick_tag_toggle_option_{row.code}",
        )
        button_label = "停用标签选项" if selected_option.is_active else "启用标签选项"
        if st.button(button_label, key=f"admin_quick_tag_toggle_button_{row.code}"):
            set_tag_option_active(session, selected_option.id, not selected_option.is_active)
            for item in row.items:
                if item.label == selected_option.label:
                    item.is_active = not selected_option.is_active
                    break


def _render_field_quick_edit(session, row):
    st.markdown(f"快速修改字段 **{row.name}**")
    with st.form(f"admin_quick_field_form_{row.code}"):
        st.text_input(
            "字段名称",
            value=row.name,
            key=f"admin_quick_field_name_{row.code}",
        )
        st.checkbox(
            "销售录入时必填",
            value="必填" in row.subtitle,
            key=f"admin_quick_field_required_{row.code}",
        )
        submitted = st.form_submit_button("保存字段")
        if submitted:
            name = st.session_state.get(f"admin_quick_field_name_{row.code}", "").strip()
            if not name:
                st.error("字段名称不能为空")
                return
            is_required = st.session_state.get(
                f"admin_quick_field_required_{row.code}",
                False,
            )
            update_custom_field(
                session,
                field_id=row.id,
                name=name,
                field_type=_field_type_from_subtitle(row.subtitle),
                is_required=is_required,
            )
            row.name = name
            row.subtitle = _format_field_subtitle(_field_type_from_subtitle(row.subtitle), is_required)


def _format_items(items):
    formatted_items = []
    for item in items:
        label = item.label
        if not item.is_active:
            label = f"{label}（已停用）"
        formatted_items.append(label)
    return formatted_items


def _set_focus(kind: str, code: str):
    st.session_state[FOCUS_KIND_KEY] = kind
    st.session_state[FOCUS_CODE_KEY] = code


def _is_focused(kind: str, code: str) -> bool:
    return (
        st.session_state.get(FOCUS_KIND_KEY) == kind
        and st.session_state.get(FOCUS_CODE_KEY) == code
    )


def _field_type_from_subtitle(subtitle: str) -> str:
    field_label = subtitle.split(" / ")[0]
    reverse_map = {
        "文本": "text",
        "多行文本": "textarea",
        "数字": "number",
        "日期": "date",
        "下拉选项": "select",
    }
    return reverse_map.get(field_label, "text")


def _format_field_subtitle(field_type: str, is_required: bool) -> str:
    subtitle = FIELD_TYPE_LABELS.get(field_type, field_type)
    if is_required:
        return f"{subtitle} / 必填"
    return subtitle
