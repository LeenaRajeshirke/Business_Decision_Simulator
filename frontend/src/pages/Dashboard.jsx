import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../services/api";
import { useAuth } from "../context/AuthContext";
import { useBusiness } from "../context/BusinessContext";
import MetricCard from "../components/MetricCard";
import { LoadingState, ErrorState, EmptyState } from "../components/States";

export default function Dashboard() {
  const { user } = useAuth();
  const { activeBusiness, loading: bizLoading } = useBusiness();
  const navigate = useNavigate();

  const [summary, setSummary] = useState(null);
  const [records, setRecords] = useState([]);
  const [simulations, setSimulations] = useState([]);
  const [state, setState] = useState("loading"); // loading | data | empty | error
  const [errorMsg, setErrorMsg] = useState(null);

  useEffect(() => {
    if (bizLoading) return;
    if (!activeBusiness) {
      setState("empty");
      return;
    }
    let cancelled = false;
    (async () => {
      setState("loading");
      try {
        const [summaryRes, dataRes, simsRes] = await Promise.all([
          api.get("/business-data/summary", { params: { business_id: activeBusiness.id } }),
          api.get("/business-data", { params: { business_id: activeBusiness.id } }),
          api.get("/simulations", { params: { business_id: activeBusiness.id } }),
        ]);
        if (cancelled) return;
        setSummary(summaryRes.data);
        setRecords(dataRes.data);
        setSimulations(simsRes.data.slice(0, 5));
        setState(summaryRes.data.has_data ? "data" : "empty");
      } catch (err) {
        if (!cancelled) {
          setErrorMsg(err.message);
          setState("error");
        }
      }
    })();
    return () => { cancelled = true; };
  }, [activeBusiness, bizLoading]);

  if (bizLoading || state === "loading") return <LoadingState label="Loading your business data..." />;
  if (state === "error") return <ErrorState message={errorMsg || "We couldn't load your dashboard."} />;

  if (!activeBusiness) {
    return (
      <EmptyState
        title="No business set up yet"
        description="Create a business profile to start analyzing decisions."
        ctaLabel="Set up your business"
        onCta={() => navigate("/onboarding")}
      />
    );
  }

  const latest = records[records.length - 1];
  const first = records[0];
  const revenue = latest ? `${activeBusiness.currency} ${latest.revenue.toLocaleString()}` : null;
  const profit = latest
    ? `${activeBusiness.currency} ${(latest.revenue - latest.variable_cost - latest.fixed_cost - latest.marketing_spend - latest.other_cost).toLocaleString()}`
    : null;
  const customers = latest ? latest.customers.toLocaleString() : null;
  const growth = first && latest && first.revenue > 0
    ? `${(((latest.revenue - first.revenue) / first.revenue) * 100).toFixed(1)}%`
    : null;

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-semibold text-gray-100">Good to see you, {user?.name}</h1>
        <p className="text-gray-500">Here's what {activeBusiness.name} looks like today.</p>
      </div>

      {state === "empty" ? (
        <EmptyState
          title="No business data yet"
          description="Upload your business data to start analyzing your business."
          ctaLabel="Upload Business Data"
          onCta={() => navigate("/business-data")}
          secondaryLabel="Add Data Manually"
          onSecondary={() => navigate("/business-data")}
        />
      ) : (
        <>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <MetricCard label="Revenue (latest)" value={revenue} hint={`Based on ${summary.n_records} records`} />
            <MetricCard label="Profit (latest)" value={profit} tone={profit ? "good" : "default"} />
            <MetricCard label="Customers (latest)" value={customers} />
            <MetricCard
              label="Growth (since first record)"
              value={growth}
              tone={growth && growth.startsWith("-") ? "bad" : "good"}
            />
          </div>

          <div className="rounded-xl border border-base-600 bg-base-900 p-5 flex items-center justify-between">
            <div>
              <h3 className="text-gray-100 font-medium">Run a new simulation</h3>
              <p className="text-gray-500 text-sm">e.g. "What if I increase my product price by 10%?"</p>
            </div>
            <button
              onClick={() => navigate("/simulation/new")}
              className="px-4 py-2 rounded-lg bg-accent-500 text-base-950 font-medium hover:bg-accent-400"
            >
              New Simulation
            </button>
          </div>

          <div>
            <h3 className="text-gray-100 font-medium mb-3">Recent simulations</h3>
            {simulations.length === 0 ? (
              <EmptyState title="No simulations yet" description="Run your first simulation to see results here." />
            ) : (
              <div className="border border-base-600 rounded-xl divide-y divide-base-700 overflow-hidden">
                {simulations.map((s) => (
                  <button
                    key={s.id}
                    onClick={() => navigate(`/simulation/${s.id}/results`)}
                    className="w-full text-left px-4 py-3 flex justify-between items-center hover:bg-base-800"
                  >
                    <div>
                      <p className="text-gray-200 text-sm">{s.title}</p>
                      <p className="text-gray-500 text-xs">{new Date(s.created_at).toLocaleDateString()}</p>
                    </div>
                    <span className="text-xs text-gray-500 uppercase">{s.status}</span>
                  </button>
                ))}
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}
