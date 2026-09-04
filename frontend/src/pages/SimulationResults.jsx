import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from "recharts";
import api from "../services/api";
import { LoadingState, ErrorState } from "../components/States";

const SCENARIO_LABELS = { conservative: "Conservative", expected: "Expected", optimistic: "Optimistic" };

export default function SimulationResults() {
  const { id } = useParams();
  const [results, setResults] = useState(null);
  const [state, setState] = useState("loading");
  const [errorMsg, setErrorMsg] = useState(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      setState("loading");
      try {
        const res = await api.get(`/simulations/${id}/results`);
        if (!cancelled) {
          setResults(res.data);
          setState("data");
        }
      } catch (err) {
        if (!cancelled) {
          setErrorMsg(err.message);
          setState("error");
        }
      }
    })();
    return () => { cancelled = true; };
  }, [id]);

  if (state === "loading") return <LoadingState label="Loading simulation results..." />;
  if (state === "error") return <ErrorState message={errorMsg} />;

  const { simulation, scenarios, risk_level, confidence_level, confidence_reasons,
    positive_factors, negative_factors, uncertain_factors, recommendation,
    recommendation_reason, methodology, data_source_note, assumptions } = results;

  const chartData = scenarios.map((s) => ({
    name: SCENARIO_LABELS[s.scenario], Revenue: Math.round(s.revenue), Profit: Math.round(s.profit),
  }));

  return (
    <div className="space-y-8 max-w-5xl mx-auto">
      <div>
        <p className="text-xs text-gray-500 uppercase tracking-wide">Decision</p>
        <h1 className="text-2xl font-semibold text-gray-100">{simulation.decision_text}</h1>
        <p className="text-gray-500 text-sm mt-1">{data_source_note}</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {scenarios.map((s) => (
          <div
            key={s.scenario}
            className={`rounded-xl border p-5 ${
              s.scenario === "expected" ? "border-accent-500 bg-accent-500/5" : "border-base-600 bg-base-900"
            }`}
          >
            <p className="text-xs uppercase tracking-wide text-gray-500 mb-2">{SCENARIO_LABELS[s.scenario]}</p>
            <p className="text-xl font-semibold text-gray-100">₹{Math.round(s.revenue).toLocaleString()}</p>
            <p className="text-xs text-gray-500 mb-3">Revenue</p>
            <p className={`text-lg font-medium ${s.profit >= 0 ? "text-emerald-400" : "text-red-400"}`}>
              ₹{Math.round(s.profit).toLocaleString()}
            </p>
            <p className="text-xs text-gray-500 mb-3">Profit</p>
            <p className="text-sm text-gray-400">Growth: {s.growth_pct.toFixed(1)}%</p>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatChip label="Risk" value={risk_level} tone={risk_level === "Low" ? "good" : risk_level === "High" ? "bad" : "warn"} />
        <StatChip label="Confidence" value={confidence_level} tone={confidence_level === "High" ? "good" : confidence_level === "Low" ? "bad" : "warn"} />
        <StatChip label="Time Horizon" value={`${simulation.time_horizon} mo`} />
        <StatChip label="Status" value={simulation.status} />
      </div>

      <div className="rounded-xl border border-base-600 bg-base-900 p-5">
        <h3 className="text-gray-100 font-medium mb-4">Scenario comparison</h3>
        <ResponsiveContainer width="100%" height={280}>
          <BarChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#22262e" />
            <XAxis dataKey="name" stroke="#6b7280" />
            <YAxis stroke="#6b7280" />
            <Tooltip contentStyle={{ background: "#181b21", border: "1px solid #2c313b" }} />
            <Legend />
            <Bar dataKey="Revenue" fill="#f2c14e" radius={[4, 4, 0, 0]} />
            <Bar dataKey="Profit" fill="#4ade80" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div className="rounded-xl border border-base-600 bg-base-900 p-5">
        <h3 className="text-gray-100 font-medium mb-3">Why this result?</h3>
        <FactorList label="Positive factors" items={positive_factors} tone="good" />
        <FactorList label="Negative factors" items={negative_factors} tone="bad" />
        <FactorList label="Uncertain factors" items={uncertain_factors} tone="warn" />
      </div>

      <div className="rounded-xl border border-accent-500/40 bg-accent-500/5 p-5">
        <h3 className="text-accent-400 font-medium mb-1">Recommendation: {recommendation}</h3>
        <p className="text-sm text-gray-300">{recommendation_reason}</p>
      </div>

      <div className="rounded-xl border border-base-600 bg-base-900 p-5">
        <h3 className="text-gray-100 font-medium mb-2">Confidence reasoning</h3>
        <ul className="text-sm text-gray-400 list-disc pl-5 space-y-1">
          {confidence_reasons.map((r, i) => <li key={i}>{r}</li>)}
        </ul>
      </div>

      <div className="rounded-xl border border-base-600 bg-base-900 p-5">
        <h3 className="text-gray-100 font-medium mb-2">Assumptions used</h3>
        <table className="w-full text-sm text-left">
          <thead className="text-gray-500 text-xs uppercase">
            <tr><th className="py-1">Parameter</th><th>Value</th><th>Source</th><th>Confidence</th></tr>
          </thead>
          <tbody>
            {assumptions.map((a) => (
              <tr key={a.parameter} className="border-t border-base-700 text-gray-300">
                <td className="py-1.5">{a.parameter}</td>
                <td>{a.value.toLocaleString()}</td>
                <td className="capitalize">{a.source}</td>
                <td className="capitalize">{a.confidence}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <p className="text-xs text-gray-600 italic">{methodology}</p>
    </div>
  );
}

function StatChip({ label, value, tone = "default" }) {
  const toneClass = { default: "text-gray-200", good: "text-emerald-400", warn: "text-amber-400", bad: "text-red-400" }[tone];
  return (
    <div className="rounded-xl border border-base-600 bg-base-900 p-4">
      <p className="text-xs text-gray-500 uppercase tracking-wide">{label}</p>
      <p className={`text-lg font-medium capitalize ${toneClass}`}>{value}</p>
    </div>
  );
}

function FactorList({ label, items, tone }) {
  if (!items || items.length === 0) return null;
  const toneClass = { good: "text-emerald-400", bad: "text-red-400", warn: "text-amber-400" }[tone];
  return (
    <div className="mb-3">
      <p className={`text-xs font-medium mb-1 ${toneClass}`}>{label}</p>
      <ul className="text-sm text-gray-400 list-disc pl-5 space-y-1">
        {items.map((it, i) => <li key={i}>{it}</li>)}
      </ul>
    </div>
  );
}
