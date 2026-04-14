import pytest

from customer_management.security import hash_password, verify_password


def test_password_hash_round_trip():
    password_hash = hash_password("streamlit123")

    assert password_hash != "streamlit123"
    assert verify_password("streamlit123", password_hash) is True
    assert verify_password("wrong-pass", password_hash) is False


def test_hash_password_rejects_passwords_longer_than_72_bytes():
    with pytest.raises(ValueError, match="72 bytes"):
        hash_password("a" * 73)
