export default function MetricCard({ label, value, hint, tone = "default" }) {
  const hasValue = value !== null && value !== undefined;
  const toneClass = {
    default: "text-gray-100",
    good: "text-emerald-400",
    warn: "text-amber-400",
    bad: "text-red-400",
  }[tone];

  return (
    <div className="rounded-xl border border-base-600 bg-base-900 p-4 flex flex-col gap-1">
      <span className="text-xs uppercase tracking-wide text-gray-500">{label}</span>
      {hasValue ? (
        <span className={`text-2xl font-semibold ${toneClass}`}>{value}</span>
      ) : (
        <span className="text-lg text-gray-600 italic">No data yet</span>
      )}
      {hint && <span className="text-xs text-gray-500">{hint}</span>}
    </div>
  );
}
