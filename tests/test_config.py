from customer_management.config import Settings


def test_settings_reads_required_database_values(monkeypatch):
    monkeypatch.setenv(
        "DATABASE_URL", "postgresql://streamlit:streamlit@localhost:5432/customer"
    )
    monkeypatch.setenv("APP_SECRET_KEY", "dev-secret")

    settings = Settings.from_env()

    assert settings.database_url.endswith("/customer")
    assert settings.app_secret_key == "dev-secret"
