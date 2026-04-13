from pathlib import Path

from streamlit.testing.v1 import AppTest


def test_admin_login_page_shows_username_and_password(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite://")
    monkeypatch.setenv("APP_SECRET_KEY", "dev-secret")

    app = AppTest.from_file(str(Path(__file__).resolve().parents[2] / "app.py"))
    app.run()

    assert any(widget.label == "管理员用户名" for widget in app.text_input)
