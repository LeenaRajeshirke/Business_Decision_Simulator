// Mirrors backend/app/utils/password_validation.py — bcrypt's hard limit is
// 72 BYTES (UTF-8), not 72 characters. A password full of emoji or accented/
// non-Latin characters can look short but be long in bytes, so we must
// measure bytes, not password.length.

export const MAX_PASSWORD_BYTES = 72;

export function passwordByteLength(password) {
  return new TextEncoder().encode(password).length;
}

/**
 * Returns a user-facing error string if the password exceeds bcrypt's
 * 72-byte limit, or null if it's valid. Never truncates the password.
 */
export function validatePasswordLength(password) {
  const byteLength = passwordByteLength(password);
  if (byteLength > MAX_PASSWORD_BYTES) {
    return "Password must be 72 bytes or fewer.";
  }
  return null;
}
