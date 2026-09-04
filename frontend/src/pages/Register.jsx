import { useState, useMemo } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { validatePasswordLength, passwordByteLength, MAX_PASSWORD_BYTES } from "../utils/validation";

export default function Register() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  const passwordError = useMemo(() => validatePasswordLength(password), [password]);
  const byteLength = useMemo(() => passwordByteLength(password), [password]);

  const submit = async (e) => {
    e.preventDefault();
    setError(null);

    // Client-side check before we even hit the network — mirrors the
    // backend's byte-length validation so the user gets instant feedback.
    const lengthError = validatePasswordLength(password);
    if (lengthError) {
      setError(lengthError);
      return;
    }

    setLoading(true);
    try {
      await register(name, email, password);
      navigate("/onboarding");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-base-950">
      <form onSubmit={submit} className="w-full max-w-sm bg-base-900 border border-base-700 rounded-xl p-8">
        <h1 className="text-xl font-semibold text-gray-100 mb-6">Create your account</h1>
        {error && <p className="text-red-400 text-sm mb-4">{error}</p>}
        <label className="text-xs text-gray-500">Name</label>
        <input
          required value={name} onChange={(e) => setName(e.target.value)}
          className="w-full mb-4 mt-1 px-3 py-2 rounded-lg bg-base-800 border border-base-600 text-gray-100 focus:outline-none focus:border-accent-500"
        />
        <label className="text-xs text-gray-500">Email</label>
        <input
          type="email" required value={email} onChange={(e) => setEmail(e.target.value)}
          className="w-full mb-4 mt-1 px-3 py-2 rounded-lg bg-base-800 border border-base-600 text-gray-100 focus:outline-none focus:border-accent-500"
        />
        <label className="text-xs text-gray-500">Password (min 8 characters)</label>
        <input
          type="password" required minLength={8} value={password} onChange={(e) => setPassword(e.target.value)}
          aria-invalid={!!passwordError}
          className={`w-full mt-1 px-3 py-2 rounded-lg bg-base-800 border text-gray-100 focus:outline-none ${
            passwordError ? "border-red-500 focus:border-red-500" : "border-base-600 focus:border-accent-500"
          }`}
        />
        <div className="flex justify-between mt-1 mb-6">
          {passwordError ? (
            <p className="text-red-400 text-xs">{passwordError}</p>
          ) : (
            <span />
          )}
          <span className={`text-xs ${byteLength > MAX_PASSWORD_BYTES ? "text-red-400" : "text-gray-600"}`}>
            {byteLength}/{MAX_PASSWORD_BYTES} bytes
          </span>
        </div>
        <button
          disabled={loading || !!passwordError}
          className="w-full py-2 rounded-lg bg-accent-500 text-base-950 font-medium hover:bg-accent-400 disabled:opacity-50"
        >
          {loading ? "Creating account..." : "Create account"}
        </button>
        <p className="text-sm text-gray-500 mt-4 text-center">
          Already have an account? <Link to="/login" className="text-accent-500 hover:underline">Log in</Link>
        </p>
      </form>
    </div>
  );
}
