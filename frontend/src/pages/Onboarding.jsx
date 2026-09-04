import { useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../services/api";
import { useBusiness } from "../context/BusinessContext";

export default function Onboarding() {
  const navigate = useNavigate();
  const { refresh } = useBusiness();
  const [mode, setMode] = useState(null); // "existing" | "new"
  const [form, setForm] = useState({
    name: "", industry: "", business_type: "", location: "", currency: "INR",
    expected_price: "", expected_monthly_customers: "",
    estimated_variable_cost_per_customer: "", estimated_fixed_cost: "", estimated_marketing_spend: "",
  });
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  const update = (k, v) => setForm((f) => ({ ...f, [k]: v }));

  const submit = async (e) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const payload = {
        name: form.name, industry: form.industry, business_type: form.business_type,
        location: form.location, currency: form.currency,
        is_new_business: mode === "new",
        expected_price: mode === "new" ? Number(form.expected_price) || null : null,
        expected_monthly_customers: mode === "new" ? Number(form.expected_monthly_customers) || null : null,
        estimated_variable_cost_per_customer: mode === "new" ? Number(form.estimated_variable_cost_per_customer) || null : null,
        estimated_fixed_cost: mode === "new" ? Number(form.estimated_fixed_cost) || null : null,
        estimated_marketing_spend: mode === "new" ? Number(form.estimated_marketing_spend) || null : null,
      };
      await api.post("/business", payload);
      await refresh();
      navigate(mode === "new" ? "/dashboard" : "/business-data");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (!mode) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-base-950 px-6">
        <div className="max-w-lg w-full text-center">
          <h1 className="text-2xl font-semibold text-gray-100 mb-2">Are you already running a business?</h1>
          <p className="text-gray-500 mb-8">This determines whether simulations use your historical data or estimated assumptions.</p>
          <div className="flex flex-col gap-3">
            <button onClick={() => setMode("existing")} className="py-4 rounded-lg border border-base-600 bg-base-900 hover:border-accent-500 text-gray-100">
              I'm already running a business
            </button>
            <button onClick={() => setMode("new")} className="py-4 rounded-lg border border-base-600 bg-base-900 hover:border-accent-500 text-gray-100">
              I'm starting a new business
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-base-950 px-6 py-10">
      <form onSubmit={submit} className="max-w-lg w-full bg-base-900 border border-base-700 rounded-xl p-8">
        <h1 className="text-xl font-semibold text-gray-100 mb-1">
          {mode === "new" ? "Tell us about your new business" : "Tell us about your business"}
        </h1>
        {mode === "new" && (
          <p className="text-amber-400 text-xs mb-5">
            New Business Mode: since there's no historical data yet, these values are used as
            <strong> estimated assumptions</strong> — you can edit them anytime.
          </p>
        )}
        {error && <p className="text-red-400 text-sm mb-4">{error}</p>}

        <div className="grid grid-cols-2 gap-3 mb-3">
          <Field label="Business name" value={form.name} onChange={(v) => update("name", v)} required span2 />
          <Field label="Industry" value={form.industry} onChange={(v) => update("industry", v)} />
          <Field label="Business type" value={form.business_type} onChange={(v) => update("business_type", v)} />
          <Field label="Location" value={form.location} onChange={(v) => update("location", v)} />
          <Field label="Currency" value={form.currency} onChange={(v) => update("currency", v)} />
        </div>

        {mode === "new" && (
          <div className="grid grid-cols-2 gap-3 border-t border-base-700 pt-4 mt-2">
            <Field label="Expected price" type="number" value={form.expected_price} onChange={(v) => update("expected_price", v)} />
            <Field label="Expected monthly customers" type="number" value={form.expected_monthly_customers} onChange={(v) => update("expected_monthly_customers", v)} />
            <Field label="Est. variable cost / customer" type="number" value={form.estimated_variable_cost_per_customer} onChange={(v) => update("estimated_variable_cost_per_customer", v)} />
            <Field label="Est. fixed cost / month" type="number" value={form.estimated_fixed_cost} onChange={(v) => update("estimated_fixed_cost", v)} />
            <Field label="Est. marketing budget / month" type="number" value={form.estimated_marketing_spend} onChange={(v) => update("estimated_marketing_spend", v)} />
          </div>
        )}

        <button disabled={loading} className="w-full mt-6 py-2 rounded-lg bg-accent-500 text-base-950 font-medium hover:bg-accent-400 disabled:opacity-50">
          {loading ? "Saving..." : "Continue"}
        </button>
      </form>
    </div>
  );
}

function Field({ label, value, onChange, type = "text", required, span2 }) {
  return (
    <div className={span2 ? "col-span-2" : ""}>
      <label className="text-xs text-gray-500">{label}</label>
      <input
        type={type} required={required} value={value} onChange={(e) => onChange(e.target.value)}
        className="w-full mt-1 px-3 py-2 rounded-lg bg-base-800 border border-base-600 text-gray-100 focus:outline-none focus:border-accent-500"
      />
    </div>
  );
}
