from customer_management.db import normalize_database_url


def test_normalize_database_url_falls_back_from_psycopg_to_psycopg2():
    database_url = "postgresql+psycopg://customer:customer@127.0.0.1:5432/customer"

    normalized = normalize_database_url(database_url)

    assert normalized == "postgresql+psycopg2://customer:customer@127.0.0.1:5432/customer"
