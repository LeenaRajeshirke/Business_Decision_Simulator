import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../services/api";
import { useBusiness } from "../context/BusinessContext";
import { LoadingState, ErrorState, EmptyState } from "../components/States";

export default function Reports() {
  const { activeBusiness } = useBusiness();
  const navigate = useNavigate();
  const [sims, setSims] = useState([]);
  const [state, setState] = useState("loading");

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

  if (state === "loading") return <LoadingState label="Loading reports..." />;
  if (state === "error") return <ErrorState message="We couldn't load your reports." />;

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold text-gray-100">Reports</h1>
      {state === "empty" ? (
        <EmptyState title="No reports yet" description="Reports are generated from completed simulations." />
      ) : (
        <div className="border border-base-600 rounded-xl divide-y divide-base-700 overflow-hidden">
          {sims.map((s) => (
            <button
              key={s.id} onClick={() => navigate(`/simulation/${s.id}/results`)}
              className="w-full text-left px-4 py-3 flex justify-between items-center hover:bg-base-800"
            >
              <span className="text-gray-200 text-sm">{s.title}</span>
              <span className="text-xs text-gray-500">{new Date(s.created_at).toLocaleDateString()}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
