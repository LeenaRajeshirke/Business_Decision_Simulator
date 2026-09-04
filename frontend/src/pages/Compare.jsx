import { useEffect, useState } from "react";
import api from "../services/api";
import { useBusiness } from "../context/BusinessContext";
import { LoadingState, ErrorState, EmptyState } from "../components/States";

export default function Compare() {
  const { activeBusiness } = useBusiness();
  const [sims, setSims] = useState([]);
  const [selected, setSelected] = useState([]);
  const [rows, setRows] = useState(null);
  const [state, setState] = useState("loading");
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!activeBusiness) { setState("empty"); return; }
    (async () => {
      setState("loading");
      try {
        const res = await api.get("/simulations", { params: { business_id: activeBusiness.id } });
        const completed = res.data.filter((s) => s.status === "completed");
        setSims(completed);
        setState(completed.length ? "data" : "empty");
      } catch {
        setState("error");
      }
    })();
  }, [activeBusiness]);

  const toggle = (id) => {
    setSelected((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]));
  };

  const runCompare = async () => {
    setError(null);
    try {
      const res = await api.post("/compare", { simulation_ids: selected });
      setRows(res.data);
    } catch (err) {
      setError(err.message);
    }
  };

  if (state === "loading") return <LoadingState label="Loading completed simulations..." />;
  if (state === "error") return <ErrorState message="We couldn't load your simulations." />;

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold text-gray-100">Scenario Comparison</h1>
      {state === "empty" ? (
        <EmptyState title="Nothing to compare yet" description="Run at least two simulations to compare them here." />
      ) : (
        <>
          <div className="flex flex-wrap gap-2">
            {sims.map((s) => (
              <button
                key={s.id} onClick={() => toggle(s.id)}
                className={`text-sm px-3 py-1.5 rounded-full border ${
                  selected.includes(s.id) ? "border-accent-500 text-accent-400 bg-accent-500/10" : "border-base-600 text-gray-400"
                }`}
              >
                {s.title}
              </button>
            ))}
          </div>
          {error && <p className="text-red-400 text-sm">{error}</p>}
          <button
            disabled={selected.length < 2}
            onClick={runCompare}
            className="px-4 py-2 rounded-lg bg-accent-500 text-base-950 font-medium hover:bg-accent-400 disabled:opacity-50"
          >
            Compare selected ({selected.length})
          </button>

          {rows && (
            <div className="rounded-xl border border-base-600 overflow-x-auto">
              <table className="w-full text-sm text-left min-w-[700px]">
                <thead className="text-gray-500 text-xs uppercase bg-base-900">
                  <tr>
                    {["Decision", "Expected Revenue", "Expected Profit", "Growth %", "Risk", "Confidence"].map((h) => (
                      <th key={h} className="py-2 px-3">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {rows.map((r) => (
                    <tr key={r.simulation_id} className="border-t border-base-700 text-gray-300">
                      <td className="py-2 px-3">{r.decision_text}</td>
                      <td className="px-3">{r.expected_revenue?.toLocaleString() ?? "—"}</td>
                      <td className="px-3">{r.expected_profit?.toLocaleString() ?? "—"}</td>
                      <td className="px-3">{r.expected_growth_pct?.toFixed(1) ?? "—"}%</td>
                      <td className="px-3">{r.risk_score ?? "—"}</td>
                      <td className="px-3">{r.confidence_score ?? "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}
    </div>
  );
}
