import { useAuth } from "../context/AuthContext";
import { useBusiness } from "../context/BusinessContext";

export default function Settings() {
  const { user, logout } = useAuth();
  const { activeBusiness } = useBusiness();

  return (
    <div className="max-w-2xl space-y-6">
      <h1 className="text-2xl font-semibold text-gray-100">Settings</h1>

      <Section title="Account">
        <Row label="Name" value={user?.name} />
        <Row label="Email" value={user?.email} />
      </Section>

      <Section title="Business">
        <Row label="Active business" value={activeBusiness?.name || "None"} />
        <Row label="Currency" value={activeBusiness?.currency || "—"} />
      </Section>

      <Section title="Simulation preferences">
        <Row label="Default iterations" value="10,000 (set via SIMULATION_ITERATIONS on the backend)" />
      </Section>

      <Section title="Security">
        <button onClick={logout} className="px-4 py-2 rounded-lg border border-red-500/40 text-red-400 hover:bg-red-500/10">
          Log out
        </button>
      </Section>
    </div>
  );
}

function Section({ title, children }) {
  return (
    <div className="rounded-xl border border-base-600 bg-base-900 p-5 space-y-2">
      <h3 className="text-gray-100 font-medium mb-2">{title}</h3>
      {children}
    </div>
  );
}

function Row({ label, value }) {
  return (
    <div className="flex justify-between text-sm">
      <span className="text-gray-500">{label}</span>
      <span className="text-gray-200">{value}</span>
    </div>
  );
}
