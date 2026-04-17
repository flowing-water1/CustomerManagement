from customer_management.db import make_engine, normalize_database_url


def test_normalize_database_url_falls_back_from_psycopg_to_psycopg2():
    database_url = "postgresql+psycopg://customer:customer@127.0.0.1:5432/customer"

    normalized = normalize_database_url(database_url)

    assert normalized == "postgresql+psycopg2://customer:customer@127.0.0.1:5432/customer"


def test_make_engine_enables_connection_health_checks_for_postgres():
    engine = make_engine("postgresql://customer:customer@127.0.0.1:5432/customer")

    assert engine.pool._pre_ping is True
    assert engine.pool._recycle == 1800
