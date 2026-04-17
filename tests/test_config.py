from customer_management.config import Settings


def test_settings_reads_required_database_values(monkeypatch):
    monkeypatch.setenv(
        "DATABASE_URL", "postgresql://streamlit:streamlit@localhost:5432/customer"
    )

    settings = Settings.from_env()

    assert settings.database_url.endswith("/customer")
    assert not hasattr(settings, "app_secret_key")
    assert not hasattr(settings, "bootstrap_on_startup")


def test_settings_prefers_environment_over_streamlit_secrets(monkeypatch):
    monkeypatch.setenv(
        "DATABASE_URL", "postgresql://env-user:env-pass@localhost:5432/customer"
    )

    settings = Settings.from_sources(
        secrets={
            "DATABASE_URL": "postgresql://secret-user:secret-pass@db:5432/customer",
        }
    )

    assert settings.database_url == "postgresql://env-user:env-pass@localhost:5432/customer"


def test_settings_falls_back_to_environment_when_streamlit_secrets_are_missing(
    monkeypatch,
):
    monkeypatch.setenv(
        "DATABASE_URL", "postgresql://streamlit:streamlit@localhost:5432/customer"
    )

    class MissingSecrets:
        def __contains__(self, key):
            raise RuntimeError("secrets unavailable")

    settings = Settings.from_sources(secrets=MissingSecrets())

    assert settings.database_url.endswith("/customer")
