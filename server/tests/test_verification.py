import pytest
from server.src import verification

def test_generate_verification_code():
    # Call the function and assert the returned value
    code = verification.generate_verification_code()
    assert code == 123123

def test_send_verification_code():
    # Call the function with sample arguments
    email = "test@example.com"
    code = "123456"
    verification.send_verification_code(email, code)
    # No assertions needed as it's a placeholder function

def test_is_valid_verification_code():
    # Test case 1: Valid code
    email = "test@example.com"
    code = "123123"
    assert verification.is_valid_verification_code(email, code) == True

    # Test case 2: Invalid code
    email = "test@example.com"
    code = "invalid_code"
    assert verification.is_valid_verification_code(email, code) == False