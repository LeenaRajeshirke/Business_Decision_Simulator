import { useEffect, useState } from "react";
import api from "../services/api";
import { useBusiness } from "../context/BusinessContext";
import { LoadingState, ErrorState, EmptyState } from "../components/States";

const SEVERITY_TONE = { info: "border-base-600", warning: "border-amber-500/50", critical: "border-red-500/50" };

export default function Insights() {
  const { activeBusiness } = useBusiness();
  const [insights, setInsights] = useState([]);
  const [state, setState] = useState("loading");

  const load = async (refresh = false) => {
    if (!activeBusiness) { setState("empty"); return; }
    setState("loading");
    try {
      const res = await api.get("/insights", { params: { business_id: activeBusiness.id, refresh } });
      setInsights(res.data);
      setState(res.data.length ? "data" : "empty");
    } catch {
      setState("error");
    }
  };

  useEffect(() => { load(false); }, [activeBusiness]);

  if (state === "loading") return <LoadingState label="Loading insights..." />;
  if (state === "error") return <ErrorState message="We couldn't load your insights." />;

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-semibold text-gray-100">Business Insights</h1>
        {state === "data" && (
          <button onClick={() => load(true)} className="text-sm text-accent-400 hover:underline">Refresh</button>
        )}
      </div>
      {state === "empty" ? (
        <EmptyState title="No insights yet" description="Upload business data so we can analyze trends, risks, and opportunities." />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {insights.map((ins) => (
            <div key={ins.id} className={`rounded-xl border bg-base-900 p-4 ${SEVERITY_TONE[ins.severity]}`}>
              <p className="text-xs uppercase tracking-wide text-gray-500">{ins.type}</p>
              <h3 className="text-gray-100 font-medium mt-1">{ins.title}</h3>
              <p className="text-sm text-gray-400 mt-1">{ins.description}</p>
              <p className="text-xs text-gray-600 mt-2 italic">{ins.source}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
