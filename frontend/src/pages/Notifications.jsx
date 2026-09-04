import { useEffect, useState } from "react";
import api from "../services/api";
import { LoadingState, ErrorState, EmptyState } from "../components/States";

export default function Notifications() {
  const [items, setItems] = useState([]);
  const [state, setState] = useState("loading");

  const load = async () => {
    setState("loading");
    try {
      const res = await api.get("/notifications");
      setItems(res.data);
      setState(res.data.length ? "data" : "empty");
    } catch {
      setState("error");
    }
  };

  useEffect(() => { load(); }, []);

  const markRead = async (id) => {
    await api.put(`/notifications/${id}/read`);
    setItems((prev) => prev.map((n) => (n.id === id ? { ...n, read: true } : n)));
  };

  if (state === "loading") return <LoadingState label="Loading notifications..." />;
  if (state === "error") return <ErrorState message="We couldn't load your notifications." />;

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold text-gray-100">Notifications</h1>
      {state === "empty" ? (
        <EmptyState title="No notifications yet" description="You'll see updates about simulations and data here." />
      ) : (
        <div className="border border-base-600 rounded-xl divide-y divide-base-700 overflow-hidden">
          {items.map((n) => (
            <div key={n.id} className={`px-4 py-3 flex justify-between items-center ${n.read ? "opacity-60" : ""}`}>
              <div>
                <p className="text-gray-200 text-sm">{n.title}</p>
                <p className="text-gray-500 text-xs">{n.message}</p>
              </div>
              {!n.read && (
                <button onClick={() => markRead(n.id)} className="text-xs text-accent-400 hover:underline">
                  Mark read
                </button>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
