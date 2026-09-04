"""
Tests for password byte-length validation. Pure stdlib — no FastAPI/
SQLAlchemy/passlib/bcrypt required — so these run in any plain Python 3.12
environment, including this sandbox.

Run with:  python3 backend/tests/test_password_validation.py
(or, where pytest is installed:  pytest backend/tests/test_password_validation.py -v)
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.utils.password_validation import (
    MAX_PASSWORD_BYTES,
    PasswordTooLongError,
    password_byte_length,
    validate_password_length,
)

PASS, FAIL = [], []


def check(name, cond):
    (PASS if cond else FAIL).append(name)
    print(f"{'PASS' if cond else 'FAIL'} - {name}")


def test_valid_password_under_limit():
    pw = "correct-horse-battery-staple"  # well under 72 bytes, all ASCII
    check("valid password: no exception raised", _no_raise(pw))
    check("valid password: byte length == char length for ASCII", password_byte_length(pw) == len(pw))


def test_password_exactly_at_limit():
    pw = "a" * MAX_PASSWORD_BYTES  # exactly 72 bytes (ASCII, 1 byte/char)
    check("password == 72 bytes: byte length is exactly 72", password_byte_length(pw) == 72)
    check("password == 72 bytes: accepted (not rejected)", _no_raise(pw))


def test_password_one_byte_over_limit():
    pw = "a" * (MAX_PASSWORD_BYTES + 1)  # 73 bytes
    check("password == 73 bytes: rejected", _raises(pw, PasswordTooLongError))


def test_password_way_over_limit():
    pw = "a" * 200
    check("200-char password: rejected", _raises(pw, PasswordTooLongError))


def test_multibyte_characters_counted_correctly():
    # Each 🔒 emoji is 4 bytes in UTF-8. 19 of them = 76 bytes, but only 19
    # *characters* — well under any naive character-length limit. This is
    # exactly the case a len(password) check would get wrong.
    pw = "🔒" * 19
    char_len = len(pw)
    byte_len = password_byte_length(pw)
    check("multi-byte password: char length (19) != byte length", char_len != byte_len)
    check("multi-byte password: byte length correctly computed as 76", byte_len == 76)
    check("multi-byte password: rejected because byte length > 72 despite short char length",
          _raises(pw, PasswordTooLongError))


def test_multibyte_characters_within_limit():
    # 18 emoji = 72 bytes exactly — should be accepted.
    pw = "🔒" * 18
    check("18 emoji == 72 bytes exactly", password_byte_length(pw) == 72)
    check("18 emoji: accepted", _no_raise(pw))


def test_never_truncates():
    # The function must only ever raise or pass through unchanged —
    # never return a modified/truncated string.
    pw = "a" * 100
    try:
        result = validate_password_length(pw)
        check("over-limit password: function returns None (no silent transform)", result is None)
        check("SHOULD NOT REACH HERE: no exception was raised for an over-limit password", False)
    except PasswordTooLongError:
        check("over-limit password: raises rather than truncating", True)


def _no_raise(pw):
    try:
        validate_password_length(pw)
        return True
    except PasswordTooLongError:
        return False


def _raises(pw, exc_type):
    try:
        validate_password_length(pw)
        return False
    except exc_type:
        return True


if __name__ == "__main__":
    test_valid_password_under_limit()
    test_password_exactly_at_limit()
    test_password_one_byte_over_limit()
    test_password_way_over_limit()
    test_multibyte_characters_counted_correctly()
    test_multibyte_characters_within_limit()
    test_never_truncates()
    print(f"\n{len(PASS)} passed, {len(FAIL)} failed")
    if FAIL:
        sys.exit(1)
