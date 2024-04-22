import pytest
from server.src.input_validation import is_valid_email


@pytest.mark.parametrize(
    "email, expected_result",
    [
        ("test@example.com", True),
        ("valid.email@domain.org", True),
        ("name+tag@company.net", True),
        ("invalid_email", False),
        ("@no_username.com", False),
        ("invalid_chars@!.com", False),
        ("", False),  
        ("invalid_email@domain", False),
        ("invalid_email.com", False),
        ("invalid@email@t.com", False),
        ("invalid.com@email", False),
    ],
)
def test_is_valid_email(email, expected_result):
    """Test email validation with various valid and invalid formats."""
    assert is_valid_email(email) == expected_result