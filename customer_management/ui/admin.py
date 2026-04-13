import pandas as pd
import streamlit as st

from customer_management.auth import (
    clear_authenticated_actor,
    get_authenticated_actor,
    set_authenticated_actor,
)
from customer_management.repositories.admin_users import (
    authenticate_admin_user,
    create_admin_user,
    get_admin_user_by_id,
    list_admin_users,
    set_admin_user_active,
)
from customer_management.repositories.metadata import (
    create_custom_field,
    create_custom_field_option,
    create_tag_group,
    create_tag_option,
    list_custom_field_options,
    list_custom_fields,
    list_tag_groups,
    list_tag_options,
    set_custom_field_active,
    set_custom_field_option_active,
    set_tag_group_active,
    set_tag_option_active,
)
from customer_management.repositories.sales_users import (
    create_sales_user,
    list_sales_users,
    set_sales_user_active,
)
from customer_management.ui.shared import render_flash, set_flash


def render_admin_area(session_factory):
    st.subheader("管理员入口")
    render_flash(st.session_state)

    with session_factory() as session:
        actor = get_authenticated_actor(st.session_state)
        if actor and actor["actor_type"] == "admin":
            admin_user = get_admin_user_by_id(session, actor["actor_id"])
            if admin_user is None or not admin_user.is_active:
                clear_authenticated_actor(st.session_state)
                set_flash(st.session_state, "当前管理员账号不可用", level="error")
                st.rerun()
            _render_workspace(session, admin_user)
            return

        _render_login(session)


def _render_login(session):
    with st.form("admin_login_form"):
        username = st.text_input("管理员用户名", key="admin_username")
        password = st.text_input("管理员密码", type="password", key="admin_password")
        submitted = st.form_submit_button("管理员登录")

        if submitted:
            admin_user = authenticate_admin_user(session, username, password)
            if admin_user is None:
                st.error("管理员用户名或密码错误")
                return
            set_authenticated_actor(
                st.session_state,
                actor_type="admin",
                actor_id=admin_user.id,
                actor_name=admin_user.display_name,
            )
            set_flash(st.session_state, f"欢迎，{admin_user.display_name}")
            st.rerun()


def _render_workspace(session, admin_user):
    header_left, header_right = st.columns([3, 1])
    with header_left:
        st.caption(f"当前管理员: {admin_user.display_name}")
    with header_right:
        if st.button("退出管理员登录", key="admin_logout"):
            clear_authenticated_actor(st.session_state)
            st.rerun()

    overview_tab, sales_tab, admins_tab, tags_tab, fields_tab = st.tabs(
        ["概览", "销售人员", "管理员", "标签配置", "字段配置"]
    )

    with overview_tab:
        st.info("管理员统计看板将在下一步补齐。")

    with sales_tab:
        _render_sales_management(session)

    with admins_tab:
        _render_admin_management(session, admin_user.id)

    with tags_tab:
        _render_tag_management(session)

    with fields_tab:
        _render_field_management(session)


def _render_sales_management(session):
    st.markdown("#### 销售人员列表")
    sales_users = list_sales_users(session)
    if sales_users:
        frame = pd.DataFrame(
            [
                {
                    "ID": user.id,
                    "姓名": user.name,
                    "启用": user.is_active,
                    "首次改密": user.must_change_password,
                }
                for user in sales_users
            ]
        )
        st.dataframe(frame, use_container_width=True)
    else:
        st.info("暂无销售人员")

    st.markdown("#### 新增销售人员")
    with st.form("admin_create_sales_user_form"):
        name = st.text_input("销售姓名", key="admin_new_sales_name")
        password = st.text_input(
            "初始密码", type="password", key="admin_new_sales_password"
        )
        must_change_password = st.checkbox(
            "首次登录必须改密", value=True, key="admin_new_sales_must_change"
        )
        submitted = st.form_submit_button("创建销售人员")
        if submitted:
            if not name or not password:
                st.error("销售姓名和初始密码不能为空")
                return
            create_sales_user(
                session,
                name=name,
                password=password,
                must_change_password=must_change_password,
            )
            set_flash(st.session_state, f"销售人员 {name} 已创建")
            st.rerun()

    if sales_users:
        selected_user = st.selectbox(
            "选择销售人员进行启停",
            sales_users,
            format_func=lambda item: f"{item.name} ({'启用' if item.is_active else '停用'})",
            key="admin_toggle_sales_user",
        )
        button_label = "停用销售人员" if selected_user.is_active else "启用销售人员"
        if st.button(button_label, key="admin_toggle_sales_user_button"):
            set_sales_user_active(session, selected_user.id, not selected_user.is_active)
            set_flash(st.session_state, f"销售人员 {selected_user.name} 状态已更新")
            st.rerun()


def _render_admin_management(session, current_admin_user_id: int):
    st.markdown("#### 管理员列表")
    admin_users = list_admin_users(session)
    if admin_users:
        frame = pd.DataFrame(
            [
                {
                    "ID": user.id,
                    "用户名": user.username,
                    "显示名": user.display_name,
                    "启用": user.is_active,
                }
                for user in admin_users
            ]
        )
        st.dataframe(frame, use_container_width=True)
    else:
        st.info("暂无管理员账号")

    st.markdown("#### 新增管理员")
    with st.form("admin_create_admin_user_form"):
        username = st.text_input("新管理员用户名", key="admin_new_username")
        display_name = st.text_input("新管理员显示名", key="admin_new_display_name")
        password = st.text_input(
            "新管理员密码", type="password", key="admin_new_password"
        )
        submitted = st.form_submit_button("创建管理员")
        if submitted:
            if not username or not display_name or not password:
                st.error("用户名、显示名、密码不能为空")
                return
            create_admin_user(
                session,
                username=username,
                display_name=display_name,
                password=password,
            )
            set_flash(st.session_state, f"管理员 {display_name} 已创建")
            st.rerun()

    toggle_candidates = [user for user in admin_users if user.id != current_admin_user_id]
    if toggle_candidates:
        selected_user = st.selectbox(
            "选择管理员进行启停",
            toggle_candidates,
            format_func=lambda item: f"{item.username} ({'启用' if item.is_active else '停用'})",
            key="admin_toggle_admin_user",
        )
        button_label = "停用管理员" if selected_user.is_active else "启用管理员"
        if st.button(button_label, key="admin_toggle_admin_user_button"):
            set_admin_user_active(session, selected_user.id, not selected_user.is_active)
            set_flash(st.session_state, f"管理员 {selected_user.display_name} 状态已更新")
            st.rerun()


def _render_tag_management(session):
    tag_groups = list_tag_groups(session)
    tag_options = list_tag_options(session)

    st.markdown("#### 标签组")
    if tag_groups:
        frame = pd.DataFrame(
            [
                {
                    "ID": group.id,
                    "名称": group.name,
                    "代码": group.code,
                    "模式": group.selection_mode,
                    "启用": group.is_active,
                }
                for group in tag_groups
            ]
        )
        st.dataframe(frame, use_container_width=True)
    else:
        st.info("暂无标签组")

    with st.form("admin_create_tag_group_form"):
        name = st.text_input("标签组名称", key="admin_new_tag_group_name")
        selection_mode = st.selectbox(
            "标签组选择模式",
            ["single", "multiple"],
            key="admin_new_tag_group_mode",
        )
        submitted = st.form_submit_button("创建标签组")
        if submitted:
            if not name:
                st.error("标签组名称不能为空")
                return
            create_tag_group(session, name=name, selection_mode=selection_mode)
            set_flash(st.session_state, f"标签组 {name} 已创建")
            st.rerun()

    if tag_groups:
        selected_group = st.selectbox(
            "选择标签组进行启停",
            tag_groups,
            format_func=lambda item: f"{item.name} ({'启用' if item.is_active else '停用'})",
            key="admin_toggle_tag_group",
        )
        button_label = "停用标签组" if selected_group.is_active else "启用标签组"
        if st.button(button_label, key="admin_toggle_tag_group_button"):
            set_tag_group_active(session, selected_group.id, not selected_group.is_active)
            set_flash(st.session_state, f"标签组 {selected_group.name} 状态已更新")
            st.rerun()

    st.markdown("#### 标签选项")
    if tag_options:
        option_frame = pd.DataFrame(
            [
                {
                    "ID": option.id,
                    "标签组ID": option.group_id,
                    "名称": option.label,
                    "值": option.value,
                    "启用": option.is_active,
                }
                for option in tag_options
            ]
        )
        st.dataframe(option_frame, use_container_width=True)

    if tag_groups:
        with st.form("admin_create_tag_option_form"):
            selected_group = st.selectbox(
                "所属标签组",
                tag_groups,
                format_func=lambda item: item.name,
                key="admin_new_tag_option_group",
            )
            label = st.text_input("标签选项名称", key="admin_new_tag_option_label")
            submitted = st.form_submit_button("创建标签选项")
            if submitted:
                if not label:
                    st.error("标签选项名称不能为空")
                    return
                create_tag_option(session, group_id=selected_group.id, label=label)
                set_flash(st.session_state, f"标签选项 {label} 已创建")
                st.rerun()

    if tag_options:
        selected_option = st.selectbox(
            "选择标签选项进行启停",
            tag_options,
            format_func=lambda item: f"{item.label} ({'启用' if item.is_active else '停用'})",
            key="admin_toggle_tag_option",
        )
        button_label = "停用标签选项" if selected_option.is_active else "启用标签选项"
        if st.button(button_label, key="admin_toggle_tag_option_button"):
            set_tag_option_active(session, selected_option.id, not selected_option.is_active)
            set_flash(st.session_state, f"标签选项 {selected_option.label} 状态已更新")
            st.rerun()


def _render_field_management(session):
    custom_fields = list_custom_fields(session)
    field_options = list_custom_field_options(session)

    st.markdown("#### 自定义字段")
    if custom_fields:
        frame = pd.DataFrame(
            [
                {
                    "ID": field.id,
                    "名称": field.name,
                    "代码": field.code,
                    "类型": field.field_type,
                    "必填": field.is_required,
                    "启用": field.is_active,
                }
                for field in custom_fields
            ]
        )
        st.dataframe(frame, use_container_width=True)
    else:
        st.info("暂无自定义字段")

    with st.form("admin_create_custom_field_form"):
        name = st.text_input("字段名称", key="admin_new_custom_field_name")
        field_type = st.selectbox(
            "字段类型",
            ["text", "textarea", "number", "date", "select"],
            key="admin_new_custom_field_type",
        )
        is_required = st.checkbox("是否必填", key="admin_new_custom_field_required")
        submitted = st.form_submit_button("创建自定义字段")
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
            set_flash(st.session_state, f"自定义字段 {name} 已创建")
            st.rerun()

    if custom_fields:
        selected_field = st.selectbox(
            "选择自定义字段进行启停",
            custom_fields,
            format_func=lambda item: f"{item.name} ({'启用' if item.is_active else '停用'})",
            key="admin_toggle_custom_field",
        )
        button_label = "停用自定义字段" if selected_field.is_active else "启用自定义字段"
        if st.button(button_label, key="admin_toggle_custom_field_button"):
            set_custom_field_active(session, selected_field.id, not selected_field.is_active)
            set_flash(st.session_state, f"自定义字段 {selected_field.name} 状态已更新")
            st.rerun()

    st.markdown("#### 自定义字段选项")
    if field_options:
        option_frame = pd.DataFrame(
            [
                {
                    "ID": option.id,
                    "字段ID": option.field_id,
                    "名称": option.label,
                    "值": option.value,
                    "启用": option.is_active,
                }
                for option in field_options
            ]
        )
        st.dataframe(option_frame, use_container_width=True)

    select_fields = [field for field in custom_fields if field.field_type == "select"]
    if select_fields:
        with st.form("admin_create_custom_field_option_form"):
            selected_field = st.selectbox(
                "所属自定义字段",
                select_fields,
                format_func=lambda item: item.name,
                key="admin_new_custom_field_option_field",
            )
            label = st.text_input(
                "自定义字段选项名称", key="admin_new_custom_field_option_label"
            )
            submitted = st.form_submit_button("创建字段选项")
            if submitted:
                if not label:
                    st.error("字段选项名称不能为空")
                    return
                create_custom_field_option(
                    session,
                    field_id=selected_field.id,
                    label=label,
                )
                set_flash(st.session_state, f"字段选项 {label} 已创建")
                st.rerun()

    if field_options:
        selected_option = st.selectbox(
            "选择字段选项进行启停",
            field_options,
            format_func=lambda item: f"{item.label} ({'启用' if item.is_active else '停用'})",
            key="admin_toggle_custom_field_option",
        )
        button_label = "停用字段选项" if selected_option.is_active else "启用字段选项"
        if st.button(button_label, key="admin_toggle_custom_field_option_button"):
            set_custom_field_option_active(
                session, selected_option.id, not selected_option.is_active
            )
            set_flash(st.session_state, f"字段选项 {selected_option.label} 状态已更新")
            st.rerun()
