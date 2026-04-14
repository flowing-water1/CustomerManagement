from datetime import date
import pandas as pd
import streamlit as st

from customer_management.auth import (
    clear_authenticated_actor,
    get_authenticated_actor,
    set_authenticated_actor,
)
from customer_management.repositories.records import (
    create_record,
    delete_record,
    get_record_details,
    list_records_for_sales_user,
    update_record,
)
from customer_management.repositories.sales_users import (
    authenticate_sales_user,
    change_sales_password,
    get_sales_user_by_id,
    list_active_sales_users,
)
from customer_management.services.forms import build_record_form_schema
from customer_management.ui.shared import render_flash, set_flash


def render_sales_area(session_factory):
    st.subheader("销售入口")
    render_flash(st.session_state)

    with session_factory() as session:
        actor = get_authenticated_actor(st.session_state)
        if actor and actor["actor_type"] == "sales":
            sales_user = get_sales_user_by_id(session, actor["actor_id"])
            if sales_user is None or not sales_user.is_active:
                clear_authenticated_actor(st.session_state)
                set_flash(st.session_state, "当前销售账号不可用", level="error")
                st.rerun()
            if sales_user.must_change_password:
                _render_change_password(session, sales_user)
                return
            _render_workspace(session, sales_user)
            return

        _render_login(session)


def _render_login(session):
    sales_users = list_active_sales_users(session)
    names = [user.name for user in sales_users] or [""]

    with st.form("sales_login_form"):
        selected_name = st.selectbox("选择销售姓名", names, key="sales_user_name")
        password = st.text_input("销售密码", type="password", key="sales_password")
        submitted = st.form_submit_button("销售登录")

        if submitted:
            if not selected_name:
                st.error("当前还没有可登录的销售账号")
                return

            authenticated = authenticate_sales_user(session, selected_name, password)
            if authenticated is None:
                st.error("销售姓名或密码错误")
                return

            set_authenticated_actor(
                st.session_state,
                actor_type="sales",
                actor_id=authenticated.id,
                actor_name=authenticated.name,
            )
            set_flash(st.session_state, f"欢迎，{authenticated.name}")
            st.rerun()


def _render_change_password(session, sales_user):
    st.info("首次登录请先修改密码")
    with st.form("sales_change_password_form"):
        old_password = st.text_input("旧密码", type="password", key="sales_old_password")
        new_password = st.text_input("新密码", type="password", key="sales_new_password")
        confirm_password = st.text_input(
            "确认新密码", type="password", key="sales_confirm_password"
        )
        submitted = st.form_submit_button("更新密码")

        if submitted:
            if not new_password or new_password != confirm_password:
                st.error("新密码为空或两次输入不一致")
                return
            try:
                change_sales_password(session, sales_user.id, old_password, new_password)
            except ValueError as exc:
                st.error(str(exc))
                return
            set_flash(st.session_state, "密码更新成功")
            st.rerun()


def _render_workspace(session, sales_user):
    schema = build_record_form_schema(session)

    header_left, header_right = st.columns([3, 1])
    with header_left:
        st.caption(f"当前销售: {sales_user.name}")
    with header_right:
        if st.button("退出登录", key="sales_logout"):
            clear_authenticated_actor(st.session_state)
            _reset_record_form(schema)
            st.rerun()

    query = st.text_input("搜索客户", key="sales_record_query")
    records = list_records_for_sales_user(session, sales_user.id, query=query)

    _render_records_table(records)
    _render_record_actions(session, sales_user.id, records, schema)
    _render_record_form(session, sales_user.id, schema)


def _render_records_table(records):
    st.markdown("#### 我的客户记录")
    if not records:
        st.info("暂无客户记录")
        return

    frame = pd.DataFrame(
        [
            {
                "ID": record.id,
                "客户名称": record.customer_name,
                "联系人": record.contact_name,
                "电话": record.phone,
                "备注": record.remark,
            }
            for record in records
        ]
    )
    st.dataframe(frame, use_container_width=True)


def _render_record_actions(session, sales_user_id: int, records, schema):
    st.markdown("#### 记录操作")
    if not records:
        return

    record_options = {f"{record.id} - {record.customer_name}": record.id for record in records}
    selected_label = st.selectbox(
        "选择记录",
        list(record_options.keys()),
        key="sales_selected_record_label",
    )
    selected_record_id = record_options[selected_label]

    action_left, action_right = st.columns(2)
    with action_left:
        if st.button("加载编辑", key="sales_load_record"):
            details = get_record_details(
                session,
                record_id=selected_record_id,
                sales_user_id=sales_user_id,
            )
            _load_record_form(schema, details)
            st.rerun()

    with action_right:
        if st.button("删除所选记录", key="sales_request_delete"):
            st.session_state["sales_pending_delete_id"] = selected_record_id
            st.rerun()

    pending_delete_id = st.session_state.get("sales_pending_delete_id")
    if pending_delete_id == selected_record_id:
        st.warning("确认删除当前记录？该操作不可恢复。")
        confirm_left, confirm_right = st.columns(2)
        with confirm_left:
            if st.button("确认删除", key="sales_confirm_delete"):
                delete_record(
                    session,
                    record_id=pending_delete_id,
                    sales_user_id=sales_user_id,
                )
                st.session_state.pop("sales_pending_delete_id", None)
                _reset_record_form(schema)
                set_flash(st.session_state, "记录已删除")
                st.rerun()
        with confirm_right:
            if st.button("取消删除", key="sales_cancel_delete"):
                st.session_state.pop("sales_pending_delete_id", None)
                st.rerun()


def _render_record_form(session, sales_user_id: int, schema):
    st.markdown("#### 新建 / 编辑记录")
    if st.session_state.pop("sales_form_needs_reset", False):
        _reset_record_form(schema)
    _ensure_form_defaults(schema)

    editing_record_id = st.session_state.get("sales_edit_record_id")
    if editing_record_id:
        st.caption(f"当前正在编辑记录 #{editing_record_id}")

    with st.form("sales_record_form"):
        st.text_input("客户名称", key="customer_name")
        st.text_input("联系人", key="contact_name")
        st.text_input("电话", key="phone")
        st.text_area("备注", key="remark")

        for group in schema.tag_groups:
            if group.selection_mode == "single":
                labels = [""] + [option.label for option in group.options]
                st.selectbox(group.name, labels, key=f"tag_group_{group.code}")
            else:
                labels = [option.label for option in group.options]
                st.multiselect(group.name, labels, key=f"tag_group_{group.code}")

        for field in schema.custom_fields:
            field_key = f"custom_field_{field.code}"
            if field.field_type == "textarea":
                st.text_area(field.name, key=field_key)
            elif field.field_type == "number":
                if field_key in st.session_state:
                    st.number_input(field.name, key=field_key, placeholder="请输入数字")
                else:
                    st.number_input(
                        field.name,
                        key=field_key,
                        value=None,
                        placeholder="请输入数字",
                    )
            elif field.field_type == "date":
                if field_key in st.session_state:
                    st.date_input(field.name, key=field_key, format="YYYY/MM/DD")
                else:
                    st.date_input(
                        field.name,
                        key=field_key,
                        value=None,
                        format="YYYY/MM/DD",
                    )
            elif field.field_type == "select":
                labels = [""] + [option.label for option in field.options]
                st.selectbox(field.name, labels, key=field_key)
            else:
                st.text_input(field.name, key=field_key)

        submitted = st.form_submit_button("保存记录")
        if submitted:
            payload = _collect_form_payload(schema)
            if (
                not payload["customer_name"]
                or not payload["contact_name"]
                or not payload["phone"]
            ):
                st.error("客户名称、联系人、电话不能为空")
                return

            if editing_record_id:
                update_record(
                    session,
                    record_id=editing_record_id,
                    sales_user_id=sales_user_id,
                    **payload,
                )
                set_flash(st.session_state, "记录已更新")
            else:
                create_record(
                    session,
                    sales_user_id=sales_user_id,
                    **payload,
                )
                set_flash(st.session_state, "记录已创建")

            st.session_state["sales_form_needs_reset"] = True
            st.rerun()


def _collect_form_payload(schema):
    selected_option_ids = []
    for group in schema.tag_groups:
        key = f"tag_group_{group.code}"
        if group.selection_mode == "single":
            selected_label = st.session_state.get(key, "")
            if selected_label:
                selected_option_ids.extend(
                    option.id for option in group.options if option.label == selected_label
                )
        else:
            selected_labels = st.session_state.get(key, [])
            selected_option_ids.extend(
                option.id for option in group.options if option.label in selected_labels
            )

    custom_field_values = {}
    for field in schema.custom_fields:
        key = f"custom_field_{field.code}"
        value = st.session_state.get(key)
        if field.field_type == "select" and value:
            matching = next(
                (option.value for option in field.options if option.label == value),
                value,
            )
            custom_field_values[field.id] = matching
        elif value not in (None, "", []):
            custom_field_values[field.id] = value

    return {
        "customer_name": st.session_state.get("customer_name", "").strip(),
        "contact_name": st.session_state.get("contact_name", "").strip(),
        "phone": st.session_state.get("phone", "").strip(),
        "remark": st.session_state.get("remark", "").strip(),
        "selected_option_ids": selected_option_ids,
        "custom_field_values": custom_field_values,
    }


def _load_record_form(schema, details):
    record = details["record"]
    selected_option_ids = set(details["selected_option_ids"])
    custom_field_values = details["custom_field_values"]

    st.session_state["sales_edit_record_id"] = record.id
    st.session_state["customer_name"] = record.customer_name
    st.session_state["contact_name"] = record.contact_name
    st.session_state["phone"] = record.phone
    st.session_state["remark"] = record.remark

    for group in schema.tag_groups:
        key = f"tag_group_{group.code}"
        matching_labels = [
            option.label for option in group.options if option.id in selected_option_ids
        ]
        if group.selection_mode == "single":
            st.session_state[key] = matching_labels[0] if matching_labels else ""
        else:
            st.session_state[key] = matching_labels

    for field in schema.custom_fields:
        key = f"custom_field_{field.code}"
        value = custom_field_values.get(field.id, "")
        if field.field_type == "select" and value:
            display_value = next(
                (option.label for option in field.options if option.value == value),
                value,
            )
            st.session_state[key] = display_value
        elif field.field_type == "number":
            parsed_value = _parse_number_value(value)
            if parsed_value is None:
                st.session_state.pop(key, None)
            else:
                st.session_state[key] = parsed_value
        elif field.field_type == "date":
            parsed_value = _parse_date_value(value)
            if parsed_value is None:
                st.session_state.pop(key, None)
            else:
                st.session_state[key] = parsed_value
        else:
            st.session_state[key] = value


def _ensure_form_defaults(schema):
    st.session_state.setdefault("sales_edit_record_id", None)
    st.session_state.setdefault("customer_name", "")
    st.session_state.setdefault("contact_name", "")
    st.session_state.setdefault("phone", "")
    st.session_state.setdefault("remark", "")
    for group in schema.tag_groups:
        key = f"tag_group_{group.code}"
        if group.selection_mode == "single":
            st.session_state.setdefault(key, "")
        else:
            st.session_state.setdefault(key, [])
    for field in schema.custom_fields:
        field_key = f"custom_field_{field.code}"
        if field.field_type in {"text", "textarea", "select"}:
            st.session_state.setdefault(field_key, "")


def _reset_record_form(schema):
    st.session_state["sales_edit_record_id"] = None
    st.session_state["customer_name"] = ""
    st.session_state["contact_name"] = ""
    st.session_state["phone"] = ""
    st.session_state["remark"] = ""
    st.session_state.pop("sales_pending_delete_id", None)
    for group in schema.tag_groups:
        if group.selection_mode == "single":
            st.session_state[f"tag_group_{group.code}"] = ""
        else:
            st.session_state[f"tag_group_{group.code}"] = []
    for field in schema.custom_fields:
        field_key = f"custom_field_{field.code}"
        if field.field_type in {"text", "textarea", "select"}:
            st.session_state[field_key] = ""
        else:
            st.session_state.pop(field_key, None)


def _parse_number_value(value):
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _parse_date_value(value):
    if value in (None, ""):
        return None
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value))
    except (TypeError, ValueError):
        return None
