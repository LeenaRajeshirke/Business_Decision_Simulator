import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../services/api";
import { useBusiness } from "../context/BusinessContext";
import { LoadingState, ErrorState, EmptyState } from "../components/States";

export default function SimulationHistory() {
  const { activeBusiness } = useBusiness();
  const navigate = useNavigate();
  const [sims, setSims] = useState([]);
  const [state, setState] = useState("loading");
  const [query, setQuery] = useState("");

  useEffect(() => {
    if (!activeBusiness) { setState("empty"); return; }
    (async () => {
      setState("loading");
      try {
        const res = await api.get("/simulations", { params: { business_id: activeBusiness.id } });
        setSims(res.data);
        setState(res.data.length ? "data" : "empty");
      } catch {
        setState("error");
      }
    })();
  }, [activeBusiness]);

  if (state === "loading") return <LoadingState label="Loading your simulations..." />;
  if (state === "error") return <ErrorState message="We couldn't load your simulations." />;

  const filtered = sims.filter((s) => s.decision_text.toLowerCase().includes(query.toLowerCase()));

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold text-gray-100">Simulation History</h1>
      {state === "empty" ? (
        <EmptyState title="No simulations yet" description="Run your first simulation to see it here."
          ctaLabel="New Simulation" onCta={() => navigate("/simulation/new")} />
      ) : (
        <>
          <input
            value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search decisions..."
            className="w-full max-w-sm px-3 py-2 rounded-lg bg-base-800 border border-base-600 text-gray-100"
          />
          <div className="border border-base-600 rounded-xl divide-y divide-base-700 overflow-hidden">
            {filtered.map((s) => (
              <button
                key={s.id} onClick={() => navigate(`/simulation/${s.id}/results`)}
                className="w-full text-left px-4 py-3 flex justify-between items-center hover:bg-base-800"
              >
                <div>
                  <p className="text-gray-200 text-sm">{s.decision_text}</p>
                  <p className="text-gray-500 text-xs">{new Date(s.created_at).toLocaleString()}</p>
                </div>
                <span className="text-xs uppercase text-gray-500">{s.status}</span>
              </button>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
