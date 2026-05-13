from auth.auth_utils import hash_password, verify_password
from models.auth_models import UserOut


def test_hash_password_uses_random_salt_and_verifies():
    password = "StrongPass123!"

    first_hash = hash_password(password)
    second_hash = hash_password(password)

    assert first_hash != second_hash
    assert verify_password(password, first_hash)
    assert verify_password(password, second_hash)
    assert int(first_hash.split("$")[2]) >= 12
    assert int(second_hash.split("$")[2]) >= 12


def test_user_out_has_no_password_field():
    assert "password" not in UserOut.model_fields
    assert "hashed_password" not in UserOut.model_fields
