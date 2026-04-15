from pathlib import Path

from streamlit.testing.v1 import AppTest

from customer_management.bootstrap import create_schema, seed_default_metadata
from customer_management.db import make_engine, make_session_factory
from customer_management.models import TagOption
from customer_management.repositories.admin_users import create_admin_user
from customer_management.repositories.metadata import (
    create_custom_field,
    set_tag_option_active,
)


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
