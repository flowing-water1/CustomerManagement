from pathlib import Path

from streamlit.testing.v1 import AppTest

from customer_management.bootstrap import create_schema, seed_default_metadata
from customer_management.db import make_engine, make_session_factory
from customer_management.models import CustomerRecord, RecordFieldValue, RecordTag, TagOption
from customer_management.repositories.admin_users import (
    authenticate_admin_user,
    create_admin_user,
    get_admin_user_by_id,
)
from customer_management.repositories.metadata import (
    create_custom_field,
    create_custom_field_option,
    set_tag_option_active,
)
from customer_management.repositories.sales_users import create_sales_user, get_sales_user_by_id


def test_admin_login_page_shows_username_and_password(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite://")
    monkeypatch.setenv("APP_SECRET_KEY", "dev-secret")

    app = AppTest.from_file(str(Path(__file__).resolve().parents[2] / "app.py"))
    app.run()

    assert any(widget.label == "管理员用户名" for widget in app.text_input)


def _build_logged_in_admin_app(tmp_path, monkeypatch):
    database_path = tmp_path / "admin-ui.db"
    database_url = f"sqlite:///{database_path.as_posix()}"
    engine = make_engine(database_url)
    create_schema(engine)
    session_factory = make_session_factory(engine)
    with session_factory() as session:
        seed_default_metadata(session)
        create_admin_user(
            session,
            username="hr-admin",
            display_name="HR",
            password="admin-pass",
        )

    monkeypatch.setenv("DATABASE_URL", database_url)
    monkeypatch.setenv("APP_SECRET_KEY", "dev-secret")

    app = AppTest.from_file(str(Path(__file__).resolve().parents[2] / "app.py"))
    app.run()
    app.text_input(key="admin_username").input("hr-admin")
    app.text_input(key="admin_password").input("admin-pass")
    next(button for button in app.button if button.label == "管理员登录").click()
    app.run()
    return app


def test_admin_workspace_shows_customer_config_summary(tmp_path, monkeypatch):
    app = _build_logged_in_admin_app(tmp_path, monkeypatch)

    markdown_values = [widget.value for widget in app.markdown]

    assert any("#### 客户资料配置" in value for value in markdown_values)
    assert any("#### 当前配置情况" in value for value in markdown_values)
    assert any("客户等级" in value for value in markdown_values)
    assert any("品牌" in value for value in markdown_values)


def test_customer_config_summary_shows_inactive_tag_and_opens_tag_quick_edit(
    tmp_path, monkeypatch
):
    database_path = tmp_path / "admin-tag-quick-edit.db"
    database_url = f"sqlite:///{database_path.as_posix()}"
    engine = make_engine(database_url)
    create_schema(engine)
    session_factory = make_session_factory(engine)
    with session_factory() as session:
        seed_default_metadata(session)
        create_admin_user(
            session,
            username="hr-admin",
            display_name="HR",
            password="admin-pass",
        )
        kunlun = (
            session.query(TagOption)
            .filter(TagOption.value == "kunlun")
            .one()
        )
        set_tag_option_active(session, kunlun.id, False)

    monkeypatch.setenv("DATABASE_URL", database_url)
    monkeypatch.setenv("APP_SECRET_KEY", "dev-secret")

    app = AppTest.from_file(str(Path(__file__).resolve().parents[2] / "app.py"))
    app.run()
    app.text_input(key="admin_username").input("hr-admin")
    app.text_input(key="admin_password").input("admin-pass")
    next(button for button in app.button if button.label == "管理员登录").click()
    app.run()

    markdown_values = [widget.value for widget in app.markdown]
    assert any("昆仑（已停用）" in value for value in markdown_values)

    app.button(key="admin_summary_focus_tag_brand").click()
    app.run()

    assert any(
        widget.key == "admin_quick_tag_option_label_brand"
        for widget in app.text_input
    )


def test_customer_config_quick_tag_add_does_not_raise_session_state_error(
    tmp_path, monkeypatch
):
    app = _build_logged_in_admin_app(tmp_path, monkeypatch)

    app.button(key="admin_summary_focus_tag_customer_level").click()
    app.run()

    app.text_input(key="admin_quick_tag_option_label_customer_level").input("VIP")
    next(
        button
        for button in app.button
        if button.key == "FormSubmitter:admin_quick_tag_form_customer_level-新增选项"
    ).click()
    app.run()

    assert len(app.exception) == 0
    assert any("VIP" in widget.value for widget in app.markdown)


def test_customer_config_field_section_shows_examples_and_opens_field_quick_edit(
    tmp_path, monkeypatch
):
    database_path = tmp_path / "admin-field-quick-edit.db"
    database_url = f"sqlite:///{database_path.as_posix()}"
    engine = make_engine(database_url)
    create_schema(engine)
    session_factory = make_session_factory(engine)
    with session_factory() as session:
        seed_default_metadata(session)
        create_admin_user(
            session,
            username="hr-admin",
            display_name="HR",
            password="admin-pass",
        )
        create_custom_field(
            session,
            name="采购周期",
            field_type="text",
            is_required=False,
        )

    monkeypatch.setenv("DATABASE_URL", database_url)
    monkeypatch.setenv("APP_SECRET_KEY", "dev-secret")

    app = AppTest.from_file(str(Path(__file__).resolve().parents[2] / "app.py"))
    app.run()
    app.text_input(key="admin_username").input("hr-admin")
    app.text_input(key="admin_password").input("admin-pass")
    next(button for button in app.button if button.label == "管理员登录").click()
    app.run()

    markdown_values = [widget.value for widget in app.markdown]
    assert any("字段用于补充客户资料" in value for value in markdown_values)
    assert any("采购周期" in value for value in markdown_values)

    app.button(key="admin_summary_focus_field_custom_field").click()
    app.run()

    assert any(
        widget.key == "admin_quick_field_name_custom_field"
        for widget in app.text_input
    )


def test_customer_config_shows_delete_buttons_for_unused_metadata(
    tmp_path, monkeypatch
):
    database_path = tmp_path / "admin-unused-delete.db"
    database_url = f"sqlite:///{database_path.as_posix()}"
    engine = make_engine(database_url)
    create_schema(engine)
    session_factory = make_session_factory(engine)
    with session_factory() as session:
        seed_default_metadata(session)
        create_admin_user(
            session,
            username="hr-admin",
            display_name="HR",
            password="admin-pass",
        )
        field = create_custom_field(
            session,
            name="采购周期",
            field_type="select",
            is_required=False,
        )
        create_custom_field_option(
            session,
            field_id=field.id,
            label="月结",
        )

    monkeypatch.setenv("DATABASE_URL", database_url)
    monkeypatch.setenv("APP_SECRET_KEY", "dev-secret")

    app = AppTest.from_file(str(Path(__file__).resolve().parents[2] / "app.py"))
    app.run()
    app.text_input(key="admin_username").input("hr-admin")
    app.text_input(key="admin_password").input("admin-pass")
    next(button for button in app.button if button.label == "管理员登录").click()
    app.run()

    assert any(button.key == "admin_delete_tag_group_button" for button in app.button)
    assert any(button.key == "admin_delete_tag_option_button" for button in app.button)
    assert any(button.key == "admin_delete_custom_field_button" for button in app.button)
    assert any(
        button.key == "admin_delete_custom_field_option_button"
        for button in app.button
    )


def test_customer_config_can_delete_tag_options_consecutively(
    tmp_path, monkeypatch
):
    app = _build_logged_in_admin_app(tmp_path, monkeypatch)

    selector = app.selectbox(key="admin_customer_config_toggle_tag_option")
    assert len(selector.options) > 2

    selector.select_index(1)
    app.run()
    deleted_label = app.selectbox(
        key="admin_customer_config_toggle_tag_option"
    ).options[1]

    app.button(key="admin_delete_tag_option_button").click()
    app.run()

    selector = app.selectbox(key="admin_customer_config_toggle_tag_option")
    assert len(app.exception) == 0
    assert deleted_label not in selector.options
    assert selector.index == 1

    next_deleted_label = selector.options[1]
    app.button(key="admin_delete_tag_option_button").click()
    app.run()

    selector = app.selectbox(key="admin_customer_config_toggle_tag_option")
    assert len(app.exception) == 0
    assert next_deleted_label not in selector.options


def test_customer_config_hides_delete_buttons_for_used_metadata(
    tmp_path, monkeypatch
):
    database_path = tmp_path / "admin-used-delete.db"
    database_url = f"sqlite:///{database_path.as_posix()}"
    engine = make_engine(database_url)
    create_schema(engine)
    session_factory = make_session_factory(engine)
    with session_factory() as session:
        seed_default_metadata(session)
        create_admin_user(
            session,
            username="hr-admin",
            display_name="HR",
            password="admin-pass",
        )
        field = create_custom_field(
            session,
            name="采购周期",
            field_type="select",
            is_required=False,
        )
        used_field_option = create_custom_field_option(
            session,
            field_id=field.id,
            label="月结",
        )
        used_tag_option = (
            session.query(TagOption)
            .filter(TagOption.value == "general")
            .one()
        )
        session.add(
            RecordTag(
                record_id=1,
                group_id=used_tag_option.group_id,
                option_id=used_tag_option.id,
            )
        )
        session.add(
            RecordFieldValue(
                record_id=1,
                field_id=field.id,
                value_text=used_field_option.value,
            )
        )
        session.commit()

    monkeypatch.setenv("DATABASE_URL", database_url)
    monkeypatch.setenv("APP_SECRET_KEY", "dev-secret")

    app = AppTest.from_file(str(Path(__file__).resolve().parents[2] / "app.py"))
    app.run()
    app.text_input(key="admin_username").input("hr-admin")
    app.text_input(key="admin_password").input("admin-pass")
    next(button for button in app.button if button.label == "管理员登录").click()
    app.run()

    assert not any(button.key == "admin_delete_tag_group_button" for button in app.button)
    assert not any(button.key == "admin_delete_tag_option_button" for button in app.button)
    assert not any(button.key == "admin_delete_custom_field_button" for button in app.button)
    assert not any(
        button.key == "admin_delete_custom_field_option_button"
        for button in app.button
    )


def test_admin_user_can_change_password_from_workspace(tmp_path, monkeypatch):
    database_path = tmp_path / "admin-change-password.db"
    database_url = f"sqlite:///{database_path.as_posix()}"
    engine = make_engine(database_url)
    create_schema(engine)
    session_factory = make_session_factory(engine)
    with session_factory() as session:
        seed_default_metadata(session)
        create_admin_user(
            session,
            username="hr-admin",
            display_name="HR",
            password="admin-pass",
        )

    monkeypatch.setenv("DATABASE_URL", database_url)
    monkeypatch.setenv("APP_SECRET_KEY", "dev-secret")

    app = AppTest.from_file(str(Path(__file__).resolve().parents[2] / "app.py"))
    app.run()
    app.text_input(key="admin_username").input("hr-admin")
    app.text_input(key="admin_password").input("admin-pass")
    next(button for button in app.button if button.label == "管理员登录").click()
    app.run()

    assert any(button.label == "修改密码" for button in app.button)

    next(button for button in app.button if button.label == "修改密码").click()
    app.run()

    app.text_input(key="admin_self_old_password").input("admin-pass")
    app.text_input(key="admin_self_new_password").input("updated-pass")
    app.text_input(key="admin_self_confirm_password").input("updated-pass")
    next(button for button in app.button if button.label == "保存新密码").click()
    app.run()

    assert len(app.exception) == 0
    assert any(button.label == "退出管理员登录" for button in app.button)

    with session_factory() as session:
        assert authenticate_admin_user(session, "hr-admin", "updated-pass") is not None


def test_admin_management_can_delete_other_admin_user(tmp_path, monkeypatch):
    database_path = tmp_path / "admin-delete-user.db"
    database_url = f"sqlite:///{database_path.as_posix()}"
    engine = make_engine(database_url)
    create_schema(engine)
    session_factory = make_session_factory(engine)
    with session_factory() as session:
        seed_default_metadata(session)
        create_admin_user(
            session,
            username="admin",
            display_name="Admin",
            password="admin-pass",
        )
        removable_admin = create_admin_user(
            session,
            username="ops-admin",
            display_name="OPS",
            password="ops-pass",
        )

    monkeypatch.setenv("DATABASE_URL", database_url)
    monkeypatch.setenv("APP_SECRET_KEY", "dev-secret")

    app = AppTest.from_file(str(Path(__file__).resolve().parents[2] / "app.py"))
    app.run()
    app.text_input(key="admin_username").input("admin")
    app.text_input(key="admin_password").input("admin-pass")
    next(button for button in app.button if button.label == "管理员登录").click()
    app.run()

    app.radio(key="admin_workspace_page").set_value("管理员")
    app.run()

    assert any(button.key == "admin_delete_admin_user_button" for button in app.button)

    app.button(key="admin_delete_admin_user_button").click()
    app.run()

    assert len(app.exception) == 0

    with session_factory() as session:
        assert get_admin_user_by_id(session, removable_admin.id) is None
        assert authenticate_admin_user(session, "ops-admin", "ops-pass") is None


def test_core_admin_can_access_admin_management_page(tmp_path, monkeypatch):
    database_path = tmp_path / "admin-protected-user.db"
    database_url = f"sqlite:///{database_path.as_posix()}"
    engine = make_engine(database_url)
    create_schema(engine)
    session_factory = make_session_factory(engine)
    with session_factory() as session:
        seed_default_metadata(session)
        create_admin_user(
            session,
            username="admin",
            display_name="Admin",
            password="core-pass",
        )
        create_admin_user(
            session,
            username="hr-admin",
            display_name="HR",
            password="admin-pass",
        )
        create_admin_user(
            session,
            username="ops-admin",
            display_name="OPS",
            password="ops-pass",
        )

    monkeypatch.setenv("DATABASE_URL", database_url)
    monkeypatch.setenv("APP_SECRET_KEY", "dev-secret")

    app = AppTest.from_file(str(Path(__file__).resolve().parents[2] / "app.py"))
    app.run()
    app.text_input(key="admin_username").input("admin")
    app.text_input(key="admin_password").input("core-pass")
    next(button for button in app.button if button.label == "管理员登录").click()
    app.run()

    app.radio(key="admin_workspace_page").set_value("管理员")
    app.run()

    assert any(button.key == "admin_delete_admin_user_button" for button in app.button)
    assert any(button.key == "admin_toggle_admin_user_button" for button in app.button)


def test_admin_can_mark_sales_user_as_test_user(tmp_path, monkeypatch):
    database_path = tmp_path / "admin-mark-test-sales-user.db"
    database_url = f"sqlite:///{database_path.as_posix()}"
    engine = make_engine(database_url)
    create_schema(engine)
    session_factory = make_session_factory(engine)
    with session_factory() as session:
        seed_default_metadata(session)
        create_admin_user(
            session,
            username="admin",
            display_name="Admin",
            password="admin-pass",
        )
        sales_user = create_sales_user(
            session,
            name="Alice",
            password="sales-pass",
            must_change_password=False,
        )

    monkeypatch.setenv("DATABASE_URL", database_url)
    monkeypatch.setenv("APP_SECRET_KEY", "dev-secret")
    app = AppTest.from_file(str(Path(__file__).resolve().parents[2] / "app.py"))
    app.run()
    app.text_input(key="admin_username").input("admin")
    app.text_input(key="admin_password").input("admin-pass")
    next(button for button in app.button if button.label == "管理员登录").click()
    app.run()

    app.radio(key="admin_workspace_page").set_value("销售人员")
    app.run()

    assert any(button.key == "admin_toggle_test_sales_user_button" for button in app.button)

    app.button(key="admin_toggle_test_sales_user_button").click()
    app.run()

    with session_factory() as session:
        assert get_sales_user_by_id(session, sales_user.id).is_test_user is True


def test_admin_sales_management_can_switch_between_production_and_test_data(
    tmp_path, monkeypatch
):
    database_path = tmp_path / "admin-production-sales-filter.db"
    database_url = f"sqlite:///{database_path.as_posix()}"
    engine = make_engine(database_url)
    create_schema(engine)
    session_factory = make_session_factory(engine)
    with session_factory() as session:
        seed_default_metadata(session)
        create_admin_user(
            session,
            username="admin",
            display_name="Admin",
            password="admin-pass",
        )
        create_sales_user(
            session,
            name="Alice",
            password="alice-pass",
            must_change_password=False,
        )
        create_sales_user(
            session,
            name="Tester",
            password="tester-pass",
            must_change_password=False,
            is_test_user=True,
        )

    monkeypatch.setenv("DATABASE_URL", database_url)
    monkeypatch.setenv("APP_SECRET_KEY", "dev-secret")
    app = AppTest.from_file(str(Path(__file__).resolve().parents[2] / "app.py"))
    app.run()
    app.text_input(key="admin_username").input("admin")
    app.text_input(key="admin_password").input("admin-pass")
    next(button for button in app.button if button.label == "管理员登录").click()
    app.run()

    app.radio(key="admin_workspace_page").set_value("销售人员")
    app.run()

    assert "Alice" in app.dataframe[0].value.to_string()
    assert "Tester" not in app.dataframe[0].value.to_string()

    app.radio(key="admin_data_view_mode").set_value("测试数据")
    app.run()

    assert "Tester" in app.dataframe[0].value.to_string()
    assert "Alice" not in app.dataframe[0].value.to_string()


def test_admin_test_entry_can_open_test_sales_workspace_and_create_record(
    tmp_path, monkeypatch
):
    database_path = tmp_path / "admin-test-entry.db"
    database_url = f"sqlite:///{database_path.as_posix()}"
    engine = make_engine(database_url)
    create_schema(engine)
    session_factory = make_session_factory(engine)
    with session_factory() as session:
        seed_default_metadata(session)
        create_admin_user(
            session,
            username="admin",
            display_name="Admin",
            password="admin-pass",
        )
        create_sales_user(
            session,
            name="Alice",
            password="alice-pass",
            must_change_password=False,
        )
        tester = create_sales_user(
            session,
            name="Tester",
            password="tester-pass",
            must_change_password=False,
            is_test_user=True,
        )

    monkeypatch.setenv("DATABASE_URL", database_url)
    monkeypatch.setenv("APP_SECRET_KEY", "dev-secret")

    app = AppTest.from_file(str(Path(__file__).resolve().parents[2] / "app.py"))
    app.run()
    app.text_input(key="admin_username").input("admin")
    app.text_input(key="admin_password").input("admin-pass")
    next(button for button in app.button if button.label == "管理员登录").click()
    app.run()

    app.radio(key="admin_workspace_page").set_value("测试入口")
    app.run()

    assert "Tester" in app.selectbox(key="admin_test_entry_user").options
    assert "Alice" not in app.selectbox(key="admin_test_entry_user").options

    app.selectbox(key="admin_test_entry_user").select("Tester")
    app.button(key="admin_open_test_entry_button").click()
    app.run()

    assert any("当前测试账号: Tester" in widget.value for widget in app.caption)

    app.text_input(key="customer_name").input("Test Customer")
    app.text_input(key="contact_name").input("Mock User")
    app.text_input(key="phone").input("13800138000")
    next(button for button in app.button if button.label == "保存记录").click()
    app.run()

    with session_factory() as session:
        records = session.query(CustomerRecord).filter_by(sales_user_id=tester.id).all()
        assert len(records) == 1
        assert records[0].customer_name == "Test Customer"


def test_non_core_admin_cannot_see_test_capabilities(tmp_path, monkeypatch):
    database_path = tmp_path / "admin-non-core-test-capabilities.db"
    database_url = f"sqlite:///{database_path.as_posix()}"
    engine = make_engine(database_url)
    create_schema(engine)
    session_factory = make_session_factory(engine)
    with session_factory() as session:
        seed_default_metadata(session)
        create_admin_user(
            session,
            username="hr-admin",
            display_name="HR",
            password="admin-pass",
        )
        create_sales_user(
            session,
            name="Tester",
            password="tester-pass",
            must_change_password=False,
            is_test_user=True,
        )

    monkeypatch.setenv("DATABASE_URL", database_url)
    monkeypatch.setenv("APP_SECRET_KEY", "dev-secret")

    app = AppTest.from_file(str(Path(__file__).resolve().parents[2] / "app.py"))
    app.run()
    app.text_input(key="admin_username").input("hr-admin")
    app.text_input(key="admin_password").input("admin-pass")
    next(button for button in app.button if button.label == "管理员登录").click()
    app.run()

    assert not any(widget.key == "admin_data_view_mode" for widget in app.radio)
    assert "测试入口" not in app.radio(key="admin_workspace_page").options
    assert "管理员" not in app.radio(key="admin_workspace_page").options

    app.radio(key="admin_workspace_page").set_value("销售人员")
    app.run()

    assert not any(widget.key == "admin_new_sales_is_test_user" for widget in app.checkbox)
    assert not any(button.key == "admin_toggle_test_sales_user_button" for button in app.button)
