"""
Tests for the real password hashing implementation in app/utils/security.py.

Unlike test_password_validation.py, these DO require the `bcrypt` package to
be installed, since they exercise actual hashing/verification. Run after
`pip install -r requirements.txt`:

    python3 backend/tests/test_password_hashing.py
    (or: pytest backend/tests/test_password_hashing.py -v)

If bcrypt isn't installed, this file reports that clearly and exits 0
(skipped) rather than failing, so it doesn't break test discovery in
environments where the full dependency set isn't set up.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

try:
    import bcrypt  # noqa: F401
except ImportError:
    print("SKIPPED — `bcrypt` is not installed in this environment.")
    print("Run `pip install -r requirements.txt` and try again.")
    sys.exit(0)

from app.utils.security import hash_password, verify_password
from app.utils.password_validation import PasswordTooLongError, MAX_PASSWORD_BYTES

PASS, FAIL = [], []


def check(name, cond):
    (PASS if cond else FAIL).append(name)
    print(f"{'PASS' if cond else 'FAIL'} - {name}")


def test_normal_password_round_trip():
    pw = "TestPassword123!"  # the exact example from the bug report
    hashed = hash_password(pw)
    check("normal password: hash produced", isinstance(hashed, str) and len(hashed) > 0)
    check("normal password: verify succeeds with the correct password", verify_password(pw, hashed))
    check("normal password: verify fails with a wrong password", not verify_password("WrongPassword456!", hashed))


def test_password_exactly_at_bcrypt_limit():
    pw = "a" * MAX_PASSWORD_BYTES  # exactly 72 bytes
    hashed = hash_password(pw)
    check("72-byte password: hashes successfully", isinstance(hashed, str))
    check("72-byte password: verifies correctly", verify_password(pw, hashed))


def test_over_limit_password_is_rejected_not_truncated():
    pw = "a" * (MAX_PASSWORD_BYTES + 1)  # 73 bytes
    try:
        hash_password(pw)
        check("73-byte password: rejected before ever reaching bcrypt", False)
    except PasswordTooLongError:
        check("73-byte password: rejected before ever reaching bcrypt", True)


def test_different_passwords_produce_different_hashes():
    h1 = hash_password("PasswordOne!!")
    h2 = hash_password("PasswordTwo!!")
    check("different passwords produce different hashes", h1 != h2)


def test_same_password_hashed_twice_differs_due_to_salt():
    h1 = hash_password("SamePassword1")
    h2 = hash_password("SamePassword1")
    check("same password hashed twice yields different hashes (random salt per call)", h1 != h2)
    check("both independently-salted hashes still verify correctly",
          verify_password("SamePassword1", h1) and verify_password("SamePassword1", h2))


def test_verify_rejects_malformed_hash_without_raising():
    check(
        "verify_password on a malformed stored hash returns False, doesn't raise",
        verify_password("whatever", "not-a-real-bcrypt-hash") is False,
    )


if __name__ == "__main__":
    test_normal_password_round_trip()
    test_password_exactly_at_bcrypt_limit()
    test_over_limit_password_is_rejected_not_truncated()
    test_different_passwords_produce_different_hashes()
    test_same_password_hashed_twice_differs_due_to_salt()
    test_verify_rejects_malformed_hash_without_raising()
    print(f"\n{len(PASS)} passed, {len(FAIL)} failed")
    if FAIL:
        sys.exit(1)
