import { useEffect, useRef, useState } from "react";
import api from "../services/api";
import { useBusiness } from "../context/BusinessContext";
import { LoadingState, EmptyState, ErrorState } from "../components/States";

const EMPTY_FORM = {
  date: "", revenue: "", customers: "", orders: "", variable_cost: "", fixed_cost: "", marketing_spend: "", other_cost: "",
};

export default function BusinessData() {
  const { activeBusiness } = useBusiness();
  const fileInput = useRef(null);
  const [records, setRecords] = useState([]);
  const [summary, setSummary] = useState(null);
  const [activeDataset, setActiveDataset] = useState(null);
  const [state, setState] = useState("loading");
  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState(null);
  const [form, setForm] = useState(EMPTY_FORM);
  const [error, setError] = useState(null);

  const load = async () => {
    if (!activeBusiness) { setState("empty"); return; }
    setState("loading");
    try {
      const [dataRes, summaryRes, datasetRes] = await Promise.all([
        api.get("/business-data", { params: { business_id: activeBusiness.id } }),
        api.get("/business-data/summary", { params: { business_id: activeBusiness.id } }),
        api.get("/business-data/active", { params: { business_id: activeBusiness.id } }),
      ]);
      setRecords(dataRes.data);
      setSummary(summaryRes.data);
      setActiveDataset(datasetRes.data);
      setState("data");
    } catch (err) {
      setError(err.message);
      setState("error");
    }
  };

  useEffect(() => { load(); }, [activeBusiness]);

  if (!activeBusiness) return <EmptyState title="No business yet" description="Set up your business profile first." />;
  if (state === "loading") return <LoadingState label="Loading your business data..." />;
  if (state === "error") return <ErrorState message={error || "We couldn't load your business data."} />;

  const addRecord = async (e) => {
    e.preventDefault();
    setError(null);
    try {
      await api.post("/business-data", { ...form, business_id: activeBusiness.id }, { params: { business_id: activeBusiness.id } });
      setForm(EMPTY_FORM);
      await load();
    } catch (err) {
      setError(err.message);
    }
  };

  const deleteRecord = async (id) => {
    try {
      await api.delete(`/business-data/${id}`, { params: { business_id: activeBusiness.id } });
      await load();
    } catch (err) {
      setError(err.message);
    }
  };

  const uploadCsv = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    setError(null);
    setUploadResult(null);
    const fd = new FormData();
    fd.append("file", file);
    try {
      const res = await api.post("/business-data/upload", fd, {
        params: { business_id: activeBusiness.id },
        headers: { "Content-Type": "multipart/form-data" },
      });
      setUploadResult(res.data);
      await load();
    } catch (err) {
      setUploadResult({ error: err.message });
    } finally {
      setUploading(false);
      if (fileInput.current) fileInput.current.value = "";
    }
  };

  const clearDataset = async () => {
    if (!activeDataset) return;
    if (!window.confirm(`Remove ${activeDataset.filename} and its ${activeDataset.row_count.toLocaleString()} records?`)) return;
    setError(null);
    try {
      await api.delete("/business-data/active", { params: { business_id: activeBusiness.id } });
      setUploadResult(null);
      await load();
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-gray-100">Business Data</h1>
        <p className="text-sm text-gray-500 mt-1">Your active dataset powers the dashboard, insights, and simulations.</p>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <SummaryChip label="Records" value={summary.n_records} />
        <SummaryChip label="Date range (days)" value={summary.date_range_days ?? "—"} />
        <SummaryChip label="Data quality" value={`${summary.data_quality_score}/100`} />
        <SummaryChip label="Missing fields" value={summary.missing_fields.length ? summary.missing_fields.join(", ") : "None"} />
      </div>

      <div className="rounded-xl border border-base-600 bg-base-900 p-5">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <h3 className="text-gray-100 font-medium">Active dataset</h3>
            {activeDataset ? (
              <div className="mt-2">
                <p className="text-gray-200 text-sm font-medium break-all">{activeDataset.filename}</p>
                <p className="text-xs text-gray-500 mt-1">
                  {activeDataset.row_count.toLocaleString()} records · uploaded {new Date(activeDataset.created_at).toLocaleString()}
                </p>
              </div>
            ) : (
              <p className="text-sm text-gray-500 mt-2">No CSV dataset is active. Upload one to power data-driven analysis.</p>
            )}
          </div>
          {activeDataset && (
            <button onClick={clearDataset} className="text-sm text-red-400 hover:text-red-300 border border-red-500/30 rounded-lg px-3 py-2">
              Remove dataset
            </button>
          )}
        </div>

        <div className="mt-4 border-t border-base-700 pt-4">
          <p className="text-xs text-gray-500 mb-3">Required: date, revenue, customers. Optional: orders, variable_cost, fixed_cost, marketing_spend, other_cost.</p>
          <label className={`inline-flex items-center px-4 py-2 rounded-lg bg-accent-500 text-base-950 font-medium cursor-pointer ${uploading ? "opacity-60 pointer-events-none" : "hover:bg-accent-400"}`}>
            {uploading ? "Processing CSV…" : activeDataset ? "Replace CSV dataset" : "Choose CSV file"}
            <input ref={fileInput} type="file" accept=".csv,text/csv" onChange={uploadCsv} disabled={uploading} className="hidden" />
          </label>
        </div>

        {uploadResult && (
          <div className="mt-3 text-sm">
            {uploadResult.error ? (
              <p className="text-red-400">{uploadResult.error}</p>
            ) : (
              <p className="text-emerald-400">
                Dataset active: {uploadResult.dataset?.filename}. Imported {uploadResult.inserted.toLocaleString()} records, rejected {uploadResult.rejected}.
                {uploadResult.errors?.length > 0 && (
                  <span className="block text-gray-500 mt-1">{uploadResult.errors.slice(0, 5).join("; ")}</span>
                )}
              </p>
            )}
          </div>
        )}
      </div>

      <form onSubmit={addRecord} className="rounded-xl border border-base-600 bg-base-900 p-5 grid grid-cols-4 gap-3">
        <h3 className="col-span-4 text-gray-100 font-medium mb-1">Add data manually</h3>
        {Object.keys(EMPTY_FORM).map((f) => (
          <div key={f}>
            <label className="text-xs text-gray-500">{f}</label>
            <input
              type={f === "date" ? "date" : "number"} required={["date", "revenue", "customers"].includes(f)}
              value={form[f]} onChange={(e) => setForm((s) => ({ ...s, [f]: e.target.value }))}
              className="w-full mt-1 px-2 py-1.5 rounded-lg bg-base-800 border border-base-600 text-gray-100 text-sm"
            />
          </div>
        ))}
        <button className="col-span-4 mt-2 px-4 py-2 rounded-lg bg-accent-500 text-base-950 font-medium hover:bg-accent-400 w-fit">
          Add record
        </button>
        {error && <p className="col-span-4 text-red-400 text-sm">{error}</p>}
      </form>

      {records.length === 0 ? (
        <EmptyState title="No records in the active dataset" description="Upload a CSV or add data manually to get started." />
      ) : (
        <div className="rounded-xl border border-base-600 overflow-x-auto">
          <table className="w-full text-sm text-left min-w-[700px]">
            <thead className="text-gray-500 text-xs uppercase bg-base-900">
              <tr>{["Date", "Revenue", "Customers", "Variable", "Fixed", "Marketing", ""].map((h) => <th key={h} className="py-2 px-3">{h}</th>)}</tr>
            </thead>
            <tbody>
              {records.map((r) => (
                <tr key={r.id} className="border-t border-base-700 text-gray-300">
                  <td className="py-2 px-3">{r.date}</td>
                  <td className="px-3">{r.revenue.toLocaleString()}</td>
                  <td className="px-3">{r.customers.toLocaleString()}</td>
                  <td className="px-3">{r.variable_cost.toLocaleString()}</td>
                  <td className="px-3">{r.fixed_cost.toLocaleString()}</td>
                  <td className="px-3">{r.marketing_spend.toLocaleString()}</td>
                  <td className="px-3"><button onClick={() => deleteRecord(r.id)} className="text-red-400 text-xs hover:underline">Delete</button></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

function SummaryChip({ label, value }) {
  return (
    <div className="rounded-xl border border-base-600 bg-base-900 p-4">
      <p className="text-xs text-gray-500 uppercase">{label}</p>
      <p className="text-gray-100 font-medium truncate">{value}</p>
    </div>
  );
}
