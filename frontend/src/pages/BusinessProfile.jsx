import { useEffect, useState } from "react";
import api from "../services/api";
import { useBusiness } from "../context/BusinessContext";
import { LoadingState, EmptyState } from "../components/States";

export default function BusinessProfile() {
  const { activeBusiness, refresh } = useBusiness();
  const [form, setForm] = useState(null);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (activeBusiness) setForm({ ...activeBusiness });
  }, [activeBusiness]);

  if (!activeBusiness) {
    return <EmptyState title="No business yet" description="Set up your business profile first." />;
  }
  if (!form) return <LoadingState />;

  const update = (k, v) => setForm((f) => ({ ...f, [k]: v }));

  const save = async (e) => {
    e.preventDefault();
    setError(null);
    setSaved(false);
    try {
      await api.put(`/business/${activeBusiness.id}`, form);
      await refresh();
      setSaved(true);
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <form onSubmit={save} className="max-w-2xl space-y-5">
      <h1 className="text-2xl font-semibold text-gray-100">Business Profile</h1>
      {error && <p className="text-red-400 text-sm">{error}</p>}
      {saved && <p className="text-emerald-400 text-sm">Saved.</p>}

      <div className="grid grid-cols-2 gap-4 rounded-xl border border-base-600 bg-base-900 p-6">
        <Field label="Business name" value={form.name} onChange={(v) => update("name", v)} span2 />
        <Field label="Industry" value={form.industry || ""} onChange={(v) => update("industry", v)} />
        <Field label="Business type" value={form.business_type || ""} onChange={(v) => update("business_type", v)} />
        <Field label="Location" value={form.location || ""} onChange={(v) => update("location", v)} />
        <Field label="Currency" value={form.currency || ""} onChange={(v) => update("currency", v)} />
      </div>

      {form.is_new_business && (
        <div className="grid grid-cols-2 gap-4 rounded-xl border border-amber-500/30 bg-amber-500/5 p-6">
          <p className="col-span-2 text-xs text-amber-400 -mb-2">Estimated assumptions (New Business Mode)</p>
          <Field label="Expected price" type="number" value={form.expected_price ?? ""} onChange={(v) => update("expected_price", Number(v))} />
          <Field label="Expected monthly customers" type="number" value={form.expected_monthly_customers ?? ""} onChange={(v) => update("expected_monthly_customers", Number(v))} />
          <Field label="Est. variable cost / customer" type="number" value={form.estimated_variable_cost_per_customer ?? ""} onChange={(v) => update("estimated_variable_cost_per_customer", Number(v))} />
          <Field label="Est. fixed cost" type="number" value={form.estimated_fixed_cost ?? ""} onChange={(v) => update("estimated_fixed_cost", Number(v))} />
          <Field label="Est. marketing spend" type="number" value={form.estimated_marketing_spend ?? ""} onChange={(v) => update("estimated_marketing_spend", Number(v))} />
        </div>
      )}

      <button className="px-4 py-2 rounded-lg bg-accent-500 text-base-950 font-medium hover:bg-accent-400">Save changes</button>
    </form>
  );
}

function Field({ label, value, onChange, type = "text", span2 }) {
  return (
    <div className={span2 ? "col-span-2" : ""}>
      <label className="text-xs text-gray-500">{label}</label>
      <input
        type={type} value={value} onChange={(e) => onChange(e.target.value)}
        className="w-full mt-1 px-3 py-2 rounded-lg bg-base-800 border border-base-600 text-gray-100"
      />
    </div>
  );
}
