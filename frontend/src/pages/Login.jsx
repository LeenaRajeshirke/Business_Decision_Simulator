import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { validatePasswordLength } from "../utils/validation";

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    setError(null);

    const lengthError = validatePasswordLength(password);
    if (lengthError) {
      setError(lengthError);
      return;
    }

    setLoading(true);
    try {
      await login(email, password);
      navigate("/dashboard");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-base-950">
      <form onSubmit={submit} className="w-full max-w-sm bg-base-900 border border-base-700 rounded-xl p-8">
        <h1 className="text-xl font-semibold text-gray-100 mb-6">Log in</h1>
        {error && <p className="text-red-400 text-sm mb-4">{error}</p>}
        <label className="text-xs text-gray-500">Email</label>
        <input
          type="email" required value={email} onChange={(e) => setEmail(e.target.value)}
          className="w-full mb-4 mt-1 px-3 py-2 rounded-lg bg-base-800 border border-base-600 text-gray-100 focus:outline-none focus:border-accent-500"
        />
        <label className="text-xs text-gray-500">Password</label>
        <input
          type="password" required value={password} onChange={(e) => setPassword(e.target.value)}
          className="w-full mb-6 mt-1 px-3 py-2 rounded-lg bg-base-800 border border-base-600 text-gray-100 focus:outline-none focus:border-accent-500"
        />
        <button
          disabled={loading}
          className="w-full py-2 rounded-lg bg-accent-500 text-base-950 font-medium hover:bg-accent-400 disabled:opacity-50"
        >
          {loading ? "Logging in..." : "Log in"}
        </button>
        <p className="text-sm text-gray-500 mt-4 text-center">
          No account? <Link to="/register" className="text-accent-500 hover:underline">Register</Link>
        </p>
      </form>
    </div>
  );
}
