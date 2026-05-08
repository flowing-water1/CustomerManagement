import altair as alt
import pandas as pd
import streamlit as st

from customer_management.auth import (
    clear_authenticated_actor,
    get_authenticated_actor,
    set_authenticated_actor,
)
from customer_management.repositories.admin_users import (
    authenticate_admin_user,
    change_admin_password,
    create_admin_user,
    delete_admin_user,
    get_admin_user_by_id,
    is_core_admin_username,
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
    get_sales_user_by_id,
    list_active_sales_users,
    list_sales_users,
    set_sales_user_active,
    set_sales_user_test_flag,
)
from customer_management.services.dashboard import (
    build_dashboard_snapshot,
    list_admin_records,
)
from customer_management.ui.admin_customer_config import render_customer_config
from customer_management.ui.sales import render_sales_workspace, reset_sales_workspace_state
from customer_management.ui.shared import render_flash, set_flash

ADMIN_PAGE_KEY = "admin_workspace_page"
ADMIN_PAGES = ["概览", "记录总览", "销售人员", "测试入口", "管理员", "客户资料配置"]
ADMIN_PASSWORD_FORM_VISIBLE_KEY = "admin_password_form_visible"
ADMIN_DATA_VIEW_KEY = "admin_data_view_mode"
PRODUCTION_DATA_LABEL = "生产数据"
TEST_DATA_LABEL = "测试数据"
ADMIN_DATA_VIEWS = [PRODUCTION_DATA_LABEL, TEST_DATA_LABEL]
ADMIN_TEST_ENTRY_USER_KEY = "admin_test_entry_user"
ADMIN_TEST_ENTRY_ACTIVE_USER_ID_KEY = "admin_test_entry_active_user_id"


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
    is_core_admin = is_core_admin_username(getattr(admin_user, "username", ""))
    header_left, password_column, logout_column = st.columns([3, 1, 1])
    with header_left:
        st.caption(f"当前管理员: {admin_user.display_name}")
    with password_column:
        st.button(
            "修改密码",
            key="admin_open_password_form",
            on_click=_show_admin_password_form,
        )
    with logout_column:
        if st.button("退出管理员登录", key="admin_logout"):
            clear_authenticated_actor(st.session_state)
            _hide_admin_password_form()
            st.session_state.pop(ADMIN_TEST_ENTRY_ACTIVE_USER_ID_KEY, None)
            reset_sales_workspace_state(session)
            st.rerun()

    _render_admin_password_form(session, admin_user)

    if is_core_admin:
        selected_data_view = st.radio(
            "数据视图",
            ADMIN_DATA_VIEWS,
            index=ADMIN_DATA_VIEWS.index(
                st.session_state.get(ADMIN_DATA_VIEW_KEY, PRODUCTION_DATA_LABEL)
            )
            if st.session_state.get(ADMIN_DATA_VIEW_KEY, PRODUCTION_DATA_LABEL)
            in ADMIN_DATA_VIEWS
            else 0,
            key=ADMIN_DATA_VIEW_KEY,
            horizontal=True,
        )
        is_test_user = selected_data_view == TEST_DATA_LABEL
        available_pages = ADMIN_PAGES
    else:
        is_test_user = False
        available_pages = [
            page for page in ADMIN_PAGES if page not in {"测试入口", "管理员"}
        ]

    default_page = st.session_state.get(ADMIN_PAGE_KEY, "客户资料配置")
    if default_page not in available_pages:
        default_page = "客户资料配置"
    default_index = available_pages.index(default_page)
    selected_page = st.radio(
        "管理员工作台",
        available_pages,
        index=default_index,
        key=ADMIN_PAGE_KEY,
        horizontal=True,
    )

    if selected_page == "概览":
        if is_test_user:
            _render_dashboard_overview(session, is_test_user=True)
        else:
            _render_dashboard_overview(session, is_test_user=False)
    elif selected_page == "记录总览":
        if is_test_user:
            _render_records_overview(session, is_test_user=True)
        else:
            _render_records_overview(session, is_test_user=False)
    elif selected_page == "销售人员":
        if is_test_user:
            _render_sales_management(
                session,
                is_test_user=True,
                allow_test_management=is_core_admin,
            )
        else:
            _render_sales_management(
                session,
                is_test_user=False,
                allow_test_management=is_core_admin,
            )
    elif selected_page == "测试入口":
        _render_test_entry(session)
    elif selected_page == "管理员":
        _render_admin_management(session, admin_user.id)
    else:
        render_customer_config(session)


def _render_sales_management(
    session, *, is_test_user=None, allow_test_management: bool = True
):
    st.markdown("#### 销售人员列表")
    if is_test_user is None:
        sales_users = list_sales_users(session)
    else:
        sales_users = list_sales_users(session, is_test_user=is_test_user)
    if sales_users:
        frame = pd.DataFrame(
            [
                {
                    "ID": user.id,
                    "姓名": user.name,
                    "测试账号": user.is_test_user,
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
        new_sales_is_test_user = False
        if allow_test_management:
            new_sales_is_test_user = st.checkbox(
                "标记为测试账号", value=False, key="admin_new_sales_is_test_user"
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
                is_test_user=new_sales_is_test_user,
            )
            set_flash(st.session_state, f"销售人员 {name} 已创建")
            st.rerun()

    if sales_users and allow_test_management:
        selected_user = st.selectbox(
            "选择销售人员设置测试账号",
            sales_users,
            format_func=lambda item: (
                f"{item.name} ({'测试账号' if item.is_test_user else '正式账号'})"
            ),
            key="admin_toggle_test_sales_user",
        )
        test_button_label = (
            "取消测试账号" if selected_user.is_test_user else "标记为测试账号"
        )
        if st.button(test_button_label, key="admin_toggle_test_sales_user_button"):
            set_sales_user_test_flag(
                session,
                selected_user.id,
                not selected_user.is_test_user,
            )
            set_flash(st.session_state, f"销售人员 {selected_user.name} 测试标记已更新")
            st.rerun()


def _render_test_entry(session):
    st.markdown("#### 测试入口")
    active_test_user_id = st.session_state.get(ADMIN_TEST_ENTRY_ACTIVE_USER_ID_KEY)
    if active_test_user_id is not None:
        sales_user = get_sales_user_by_id(session, active_test_user_id)
        if sales_user is None or not sales_user.is_active or not sales_user.is_test_user:
            st.session_state.pop(ADMIN_TEST_ENTRY_ACTIVE_USER_ID_KEY, None)
            st.warning("当前测试账号不可用")
            return

        render_sales_workspace(
            session,
            sales_user,
            header_text=f"当前测试账号: {sales_user.name}",
            exit_button_label="返回测试入口",
            on_exit=lambda: _close_test_entry(session),
            allow_password_change=False,
        )
        return

    test_users = list_active_sales_users(session, is_test_user=True)
    if not test_users:
        st.info("暂无可用测试账号")
        return

    st.caption("仅管理员可从这里进入测试账号工作台。")
    selected_user_name = st.selectbox(
        "选择测试账号",
        [user.name for user in test_users],
        key=ADMIN_TEST_ENTRY_USER_KEY,
    )
    if st.button("进入测试入口", key="admin_open_test_entry_button"):
        selected_user = next(
            user for user in test_users if user.name == selected_user_name
        )
        st.session_state[ADMIN_TEST_ENTRY_ACTIVE_USER_ID_KEY] = selected_user.id
        reset_sales_workspace_state(session)
        st.rerun()


def _close_test_entry(session):
    st.session_state.pop(ADMIN_TEST_ENTRY_ACTIVE_USER_ID_KEY, None)
    reset_sales_workspace_state(session)


def _render_dashboard_overview(session, *, is_test_user=None):
    if is_test_user is None:
        snapshot = build_dashboard_snapshot(session)
    else:
        snapshot = build_dashboard_snapshot(session, is_test_user=is_test_user)
    metric_columns = st.columns(5)
    metric_columns[0].metric("总记录数", snapshot.total_records)
    metric_columns[1].metric("今日新增", snapshot.records_today)
    metric_columns[2].metric("本周新增", snapshot.records_this_week)
    metric_columns[3].metric("本月新增", snapshot.records_this_month)
    metric_columns[4].metric("活跃销售", snapshot.active_sales_count)

    top_left, top_right = st.columns(2)
    with top_left:
        st.markdown("#### 新增客户记录趋势")
        if snapshot.trend_points:
            trend_frame = pd.DataFrame(
                [{"日期": item.bucket, "新增记录": item.count} for item in snapshot.trend_points]
            ).set_index("日期")
            st.line_chart(trend_frame)
        else:
            st.info("暂无趋势数据")
    with top_right:
        st.markdown("#### 各销售提交客户数")
        if snapshot.sales_rankings:
            ranking_frame = pd.DataFrame(
                [{"销售": item.label, "提交数": item.count} for item in snapshot.sales_rankings]
            ).set_index("销售")
            st.bar_chart(ranking_frame)
        else:
            st.info("暂无销售提交数据")

    bottom_left, bottom_right = st.columns(2)
    with bottom_left:
        _render_donut_chart(
            "客户等级分布",
            snapshot.customer_level_distribution,
            "暂无客户等级数据",
        )
    with bottom_right:
        _render_donut_chart(
            "已成交 / 未成交占比",
            snapshot.customer_type_distribution,
            "暂无成交状态数据",
        )

    if snapshot.tag_distributions:
        st.markdown("#### 各标签使用情况")
        distribution_frame = pd.DataFrame(
            [
                {
                    "标签组": item.group_name,
                    "标签": item.option_label,
                    "数量": item.count,
                }
                for item in snapshot.tag_distributions
            ]
        )
        st.dataframe(distribution_frame, use_container_width=True)


def _render_donut_chart(title: str, items, empty_message: str):
    st.markdown(f"#### {title}")
    if not items:
        st.info(empty_message)
        return

    frame = pd.DataFrame(
        [{"标签": item.label, "数量": item.count} for item in items]
    )
    chart = (
        alt.Chart(frame)
        .mark_arc(innerRadius=70)
        .encode(
            theta=alt.Theta(field="数量", type="quantitative"),
            color=alt.Color(field="标签", type="nominal", legend=alt.Legend(title=None)),
            tooltip=["标签", "数量"],
        )
        .properties(height=280)
    )
    st.altair_chart(chart, use_container_width=True)


def _render_admin_password_form(session, admin_user):
    if not st.session_state.get(ADMIN_PASSWORD_FORM_VISIBLE_KEY):
        return

    with st.form("admin_self_change_password_form"):
        old_password = st.text_input("当前密码", type="password", key="admin_self_old_password")
        new_password = st.text_input("新密码", type="password", key="admin_self_new_password")
        confirm_password = st.text_input("确认新密码", type="password", key="admin_self_confirm_password")
        save_column, cancel_column = st.columns(2)
        with save_column:
            save_clicked = st.form_submit_button("保存新密码")
        with cancel_column:
            cancel_clicked = st.form_submit_button("取消")

        if cancel_clicked:
            _clear_admin_password_form_fields()
            _hide_admin_password_form()
            st.rerun()

        if save_clicked:
            if not new_password or new_password != confirm_password:
                st.error("新密码为空或两次输入不一致")
                return
            try:
                change_admin_password(
                    session,
                    admin_user.id,
                    old_password,
                    new_password,
                )
            except ValueError:
                st.error("当前密码不正确")
                return
            _clear_admin_password_form_fields()
            _hide_admin_password_form()
            set_flash(st.session_state, "密码已更新，下次登录请使用新密码")
            st.rerun()


def _show_admin_password_form():
    st.session_state[ADMIN_PASSWORD_FORM_VISIBLE_KEY] = True


def _hide_admin_password_form():
    st.session_state[ADMIN_PASSWORD_FORM_VISIBLE_KEY] = False


def _clear_admin_password_form_fields():
    st.session_state.pop("admin_self_old_password", None)
    st.session_state.pop("admin_self_new_password", None)
    st.session_state.pop("admin_self_confirm_password", None)


def _render_records_overview(session, *, is_test_user=None):
    st.markdown("#### 全量记录")
    if is_test_user is None:
        sales_users = list_sales_users(session)
    else:
        sales_users = list_sales_users(session, is_test_user=is_test_user)
    tag_options = list_tag_options(session)

    filter_columns = st.columns(3)
    with filter_columns[0]:
        selected_sales = st.selectbox(
            "按销售筛选",
            [None] + sales_users,
            format_func=lambda item: "全部" if item is None else item.name,
            key="admin_records_sales_filter",
        )
    with filter_columns[1]:
        selected_option = st.selectbox(
            "按标签筛选",
            [None] + tag_options,
            format_func=lambda item: "全部" if item is None else item.label,
            key="admin_records_tag_filter",
        )
    with filter_columns[2]:
        search_query = st.text_input(
            "搜索",
            placeholder="客户名称 / 联系人 / 电话 / 备注",
            key="admin_records_search_query",
        )

    records = list_admin_records(
        session,
        sales_user_id=None if selected_sales is None else selected_sales.id,
        tag_option_id=None if selected_option is None else selected_option.id,
        query=search_query,
        is_test_user=is_test_user,
    )
    if not records:
        st.info("当前筛选条件下没有记录")
        return

    frame = pd.DataFrame(
        [
            {
                "ID": item["id"],
                "销售": item["sales_name"],
                "客户名称": item["customer_name"],
                "联系人": item["contact_name"],
                "电话": item["phone"],
                "备注": item["remark"],
                "创建时间": item["created_at"],
                "更新时间": item["updated_at"],
            }
            for item in records
        ]
    )
    st.dataframe(frame, use_container_width=True)

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
    if not toggle_candidates:
        st.session_state.pop("admin_toggle_admin_user", None)
        return

    selected_user = st.selectbox(
        "选择管理员进行管理",
        toggle_candidates,
        format_func=lambda item: f"{item.username} ({'启用' if item.is_active else '停用'})",
        key="admin_toggle_admin_user",
    )
    toggle_column, delete_column = st.columns(2)
    button_label = "停用管理员" if selected_user.is_active else "启用管理员"
    if is_core_admin_username(selected_user.username):
        with toggle_column:
            st.caption("核心管理员不允许停用")
        with delete_column:
            st.caption("核心管理员不允许删除")
    else:
        with toggle_column:
            if st.button(button_label, key="admin_toggle_admin_user_button"):
                set_admin_user_active(session, selected_user.id, not selected_user.is_active)
                set_flash(st.session_state, f"管理员 {selected_user.display_name} 状态已更新")
                st.rerun()
        with delete_column:
            if st.button("删除管理员", key="admin_delete_admin_user_button"):
                delete_admin_user(session, selected_user.id)
                st.session_state.pop("admin_toggle_admin_user", None)
                set_flash(st.session_state, f"管理员 {selected_user.display_name} 已删除")
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
