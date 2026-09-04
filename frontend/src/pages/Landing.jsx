import { Link } from "react-router-dom";
import { TrendingUp, ShieldCheck, Sparkles } from "lucide-react";

export default function Landing() {
  return (
    <div className="min-h-screen bg-base-950 text-gray-200">
      <header className="flex justify-between items-center px-8 py-5 border-b border-base-700">
        <span className="font-semibold text-accent-500">Decision Simulator</span>
        <div className="flex gap-3">
          <Link to="/login" className="px-4 py-2 text-sm text-gray-300 hover:text-white">Login</Link>
          <Link to="/register" className="px-4 py-2 text-sm rounded-lg bg-accent-500 text-base-950 font-medium hover:bg-accent-400">
            Get Started
          </Link>
        </div>
      </header>

      <section className="max-w-4xl mx-auto text-center py-24 px-6">
        <p className="text-accent-500 text-sm tracking-widest mb-4">SIMULATE. UNDERSTAND. DECIDE.</p>
        <h1 className="text-4xl md:text-5xl font-semibold text-gray-50 leading-tight">
          Make your next business decision<br />before you make it.
        </h1>
        <p className="mt-6 text-gray-400 max-w-2xl mx-auto">
          Decision Simulator runs your pricing, marketing, hiring, and expansion decisions
          through a real statistical simulation engine — grounded in your own business data —
          before you commit to them.
        </p>
        <div className="mt-8 flex justify-center gap-4">
          <Link to="/register" className="px-6 py-3 rounded-lg bg-accent-500 text-base-950 font-medium hover:bg-accent-400">
            Simulate your first decision
          </Link>
        </div>
      </section>

      <section className="max-w-5xl mx-auto grid grid-cols-1 md:grid-cols-3 gap-6 px-6 pb-24">
        {[
          { label: "Conservative", desc: "10th-percentile outcome across thousands of simulated scenarios.", Icon: ShieldCheck },
          { label: "Expected", desc: "Median outcome — the single most likely result.", Icon: TrendingUp },
          { label: "Optimistic", desc: "90th-percentile outcome if conditions favor you.", Icon: Sparkles },
        ].map(({ label, desc, Icon }) => (
          <div key={label} className="rounded-xl border border-base-600 bg-base-900 p-6">
            <Icon className="text-accent-500 mb-3" size={22} />
            <h3 className="font-medium text-gray-100 mb-1">{label}</h3>
            <p className="text-sm text-gray-500">{desc}</p>
          </div>
        ))}
      </section>

      <footer className="text-center text-gray-600 text-xs pb-10">
        Chatbots give opinions. Decision Simulator gives simulation-backed decision support.
      </footer>
    </div>
  );
}
