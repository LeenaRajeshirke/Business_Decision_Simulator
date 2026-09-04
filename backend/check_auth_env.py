"""
Run this AFTER `pip install -r requirements.txt`, inside your activated
virtual environment, to confirm what is actually installed and whether the
password hashing path works end-to-end — as opposed to what requirements.txt
merely asks pip to install.

Usage (from the backend/ directory, with your venv active):
    python3 check_auth_env.py

This never prints, logs, or stores any real user password. It only ever
hashes a hardcoded, disposable diagnostic string.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print(f"Python: {sys.version.split()[0]}")
print(f"Executable: {sys.executable}")
print("-" * 60)

try:
    import bcrypt
except ImportError:
    print("bcrypt: NOT INSTALLED.")
    print("  -> Run: pip install -r requirements.txt")
    sys.exit(1)

bcrypt_version = getattr(bcrypt, "__version__", "unknown")
has_about = hasattr(bcrypt, "__about__")
print(f"bcrypt: version={bcrypt_version}")
print(f"bcrypt: has legacy __about__ submodule = {has_about}  "
      f"({'old layout, pre-4.0' if has_about else 'modern layout, this is expected for 4.0+'})")

try:
    import passlib
    print(f"passlib: STILL INSTALLED (version={getattr(passlib, '__version__', 'unknown')}).")
    print("  This project no longer imports passlib for password hashing (see")
    print("  app/utils/security.py). If you still see the 72-byte error after")
    print("  this fix, search your codebase for any other `from passlib` import")
    print("  that might be hashing passwords through a different code path.")
except ImportError:
    print("passlib: not installed (expected — this project hashes directly with bcrypt).")

print("-" * 60)

from app.utils.security import hash_password, verify_password  # noqa: E402
from app.utils.password_validation import PasswordTooLongError, MAX_PASSWORD_BYTES  # noqa: E402

DIAGNOSTIC_VALUE = "diagnostic-check-value-not-a-real-user-password"

try:
    hashed = hash_password(DIAGNOSTIC_VALUE)
    correct_matches = verify_password(DIAGNOSTIC_VALUE, hashed)
    wrong_rejected = not verify_password("a-different-value", hashed)
    print(f"hash_password() on a normal-length string: OK (produced a {len(hashed)}-char hash)")
    print(f"verify_password() with the correct value:  {'OK' if correct_matches else 'FAILED'}")
    print(f"verify_password() with a wrong value:       {'OK (correctly rejected)' if wrong_rejected else 'FAILED (accepted wrong value!)'}")
except PasswordTooLongError as e:
    print(f"UNEXPECTED: a {len(DIAGNOSTIC_VALUE.encode('utf-8'))}-byte diagnostic string was rejected as too long: {e}")
    sys.exit(1)
except Exception as e:
    print(f"hash_password()/verify_password() raised an unexpected error: {type(e).__name__}: {e}")
    sys.exit(1)

print("-" * 60)

try:
    over_limit = "a" * (MAX_PASSWORD_BYTES + 1)
    hash_password(over_limit)
    print("UNEXPECTED: a 73-byte password was accepted (should have been rejected).")
    sys.exit(1)
except PasswordTooLongError:
    print(f"An intentionally over-limit ({MAX_PASSWORD_BYTES + 1}-byte) password was correctly rejected.")

print("-" * 60)
if correct_matches and wrong_rejected:
    print("RESULT: the password hashing path is active and working correctly in this environment.")
else:
    print("RESULT: something is still wrong — see output above.")
    sys.exit(1)
