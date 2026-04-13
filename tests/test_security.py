from customer_management.security import hash_password, verify_password


def test_password_hash_round_trip():
    password_hash = hash_password("streamlit123")

    assert password_hash != "streamlit123"
    assert verify_password("streamlit123", password_hash) is True
    assert verify_password("wrong-pass", password_hash) is False
