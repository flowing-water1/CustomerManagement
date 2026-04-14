from pathlib import Path

from streamlit.testing.v1 import AppTest

from customer_management.bootstrap import create_schema, seed_default_metadata
from customer_management.db import make_engine, make_session_factory
from customer_management.repositories.admin_users import create_admin_user


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
