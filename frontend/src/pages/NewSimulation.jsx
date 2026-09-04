import { useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../services/api";
import { useBusiness } from "../context/BusinessContext";
import { EmptyState } from "../components/States";

const SUGGESTIONS = [
  "What if I increase my product price by 10%?",
  "What if I increase marketing spending by 20%?",
  "What if I hire one additional employee?",
  "What if I open another branch?",
  "What if I reduce my product price by 5%?",
];

const LOADING_STEPS = [
  "Analyzing business data...",
  "Estimating relationships...",
  "Running simulations...",
  "Testing possible outcomes...",
  "Calculating risk...",
];

export default function NewSimulation() {
  const { activeBusiness } = useBusiness();
  const navigate = useNavigate();
  const [step, setStep] = useState(1);
  const [decisionText, setDecisionText] = useState("");
  const [parsed, setParsed] = useState(null); // { decision_type, decision_params, parsed_by, note }
  const [timeHorizon, setTimeHorizon] = useState(3);
  const [error, setError] = useState(null);
  const [busy, setBusy] = useState(false);
  const [loadingStepIdx, setLoadingStepIdx] = useState(0);

  if (!activeBusiness) {
    return (
      <EmptyState
        title="Set up a business first"
        description="You need a business profile before you can run a simulation."
        ctaLabel="Set up business"
        onCta={() => navigate("/onboarding")}
      />
    );
  }

  const parseDecision = async () => {
    setError(null);
    setBusy(true);
    try {
      const res = await api.post("/simulations/parse-decision", { decision_text: decisionText });
      setParsed(res.data);
      setStep(2);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  const updateParam = (key, value) => {
    setParsed((p) => ({ ...p, decision_params: { ...p.decision_params, [key]: value } }));
  };

  const runSimulation = async () => {
    setError(null);
    setBusy(true);
    setStep(4);
    let idx = 0;
    const interval = setInterval(() => {
      idx = (idx + 1) % LOADING_STEPS.length;
      setLoadingStepIdx(idx);
    }, 700);
    try {
      const createRes = await api.post("/simulations", {
        business_id: activeBusiness.id,
        title: decisionText,
        decision_text: decisionText,
        decision_type: parsed.decision_type,
        decision_params: parsed.decision_params,
        time_horizon: Number(timeHorizon),
      });
      const simId = createRes.data.id;
      await api.post(`/simulations/${simId}/run`);
      clearInterval(interval);
      navigate(`/simulation/${simId}/results`);
    } catch (err) {
      clearInterval(interval);
      setError(err.message);
      setStep(3);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <h1 className="text-2xl font-semibold text-gray-100">New Simulation</h1>
      {error && <p className="text-red-400 text-sm">{error}</p>}

      {step === 1 && (
        <div className="rounded-xl border border-base-600 bg-base-900 p-6 space-y-4">
          <label className="text-sm text-gray-300">What decision are you considering?</label>
          <textarea
            value={decisionText}
            onChange={(e) => setDecisionText(e.target.value)}
            rows={3}
            placeholder="e.g. What if I increase my product price by 10%?"
            className="w-full px-3 py-2 rounded-lg bg-base-800 border border-base-600 text-gray-100 focus:outline-none focus:border-accent-500"
          />
          <div className="flex flex-wrap gap-2">
            {SUGGESTIONS.map((s) => (
              <button
                key={s}
                onClick={() => setDecisionText(s)}
                className="text-xs px-3 py-1.5 rounded-full border border-base-600 text-gray-400 hover:border-accent-500 hover:text-accent-400"
              >
                {s}
              </button>
            ))}
          </div>
          <button
            disabled={!decisionText.trim() || busy}
            onClick={parseDecision}
            className="px-4 py-2 rounded-lg bg-accent-500 text-base-950 font-medium hover:bg-accent-400 disabled:opacity-50"
          >
            {busy ? "Analyzing..." : "Continue"}
          </button>
        </div>
      )}

      {step === 2 && parsed && (
        <div className="rounded-xl border border-base-600 bg-base-900 p-6 space-y-4">
          <p className="text-sm text-gray-400">
            {parsed.note || "Parameters extracted from your decision:"}
          </p>
          <div className="space-y-3">
            <div>
              <label className="text-xs text-gray-500">Decision type</label>
              <select
                value={parsed.decision_type}
                onChange={(e) => setParsed((p) => ({ ...p, decision_type: e.target.value }))}
                className="w-full mt-1 px-3 py-2 rounded-lg bg-base-800 border border-base-600 text-gray-100"
              >
                {["pricing", "marketing", "hiring", "expansion", "product_launch", "cost_reduction", "other"].map((t) => (
                  <option key={t} value={t}>{t}</option>
                ))}
              </select>
            </div>
            {Object.entries(parsed.decision_params).map(([key, val]) => (
              <div key={key}>
                <label className="text-xs text-gray-500">{key}</label>
                <input
                  type={typeof val === "number" ? "number" : "text"}
                  step="any"
                  value={val}
                  onChange={(e) => updateParam(key, typeof val === "number" ? Number(e.target.value) : e.target.value)}
                  className="w-full mt-1 px-3 py-2 rounded-lg bg-base-800 border border-base-600 text-gray-100"
                />
              </div>
            ))}
          </div>
          <p className="text-xs text-gray-500">
            These extracted parameters are editable — review them before running the simulation.
          </p>
          <div className="flex gap-3">
            <button onClick={() => setStep(1)} className="px-4 py-2 rounded-lg border border-base-600 text-gray-300">Back</button>
            <button onClick={() => setStep(3)} className="px-4 py-2 rounded-lg bg-accent-500 text-base-950 font-medium hover:bg-accent-400">
              Continue
            </button>
          </div>
        </div>
      )}

      {step === 3 && (
        <div className="rounded-xl border border-base-600 bg-base-900 p-6 space-y-4">
          <label className="text-xs text-gray-500">Time horizon (months)</label>
          <input
            type="number" min={1} max={24} value={timeHorizon}
            onChange={(e) => setTimeHorizon(e.target.value)}
            className="w-full px-3 py-2 rounded-lg bg-base-800 border border-base-600 text-gray-100"
          />
          <p className="text-xs text-gray-500">
            The simulation engine will run 10,000 Monte Carlo iterations using your business's
            historical data (or estimated assumptions in New Business Mode).
          </p>
          <div className="flex gap-3">
            <button onClick={() => setStep(2)} className="px-4 py-2 rounded-lg border border-base-600 text-gray-300">Back</button>
            <button onClick={runSimulation} className="px-4 py-2 rounded-lg bg-accent-500 text-base-950 font-medium hover:bg-accent-400">
              Run Simulation
            </button>
          </div>
        </div>
      )}

      {step === 4 && (
        <div className="rounded-xl border border-base-600 bg-base-900 p-10 text-center">
          <div className="animate-pulse text-accent-400 font-medium">{LOADING_STEPS[loadingStepIdx]}</div>
        </div>
      )}
    </div>
  );
}
