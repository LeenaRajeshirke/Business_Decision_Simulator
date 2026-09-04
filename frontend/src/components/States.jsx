import { Loader2, Inbox, AlertTriangle } from "lucide-react";

export function LoadingState({ label = "Loading..." }) {
  return (
    <div className="flex items-center gap-2 text-gray-400 py-10 justify-center">
      <Loader2 className="animate-spin" size={18} />
      <span>{label}</span>
    </div>
  );
}

export function ErrorState({ message = "Something went wrong." }) {
  return (
    <div className="flex flex-col items-center gap-2 text-gray-400 py-10">
      <AlertTriangle className="text-accent-500" size={28} />
      <p>{message}</p>
    </div>
  );
}

export function EmptyState({ title, description, ctaLabel, onCta, secondaryLabel, onSecondary }) {
  return (
    <div className="flex flex-col items-center text-center gap-3 py-14 border border-dashed border-base-600 rounded-xl bg-base-900/40">
      <Inbox className="text-gray-500" size={30} />
      <h3 className="text-gray-200 font-medium">{title}</h3>
      {description && <p className="text-gray-500 text-sm max-w-sm">{description}</p>}
      <div className="flex gap-3 mt-2">
        {ctaLabel && (
          <button
            onClick={onCta}
            className="px-4 py-2 rounded-lg bg-accent-500 text-base-950 font-medium hover:bg-accent-400 transition"
          >
            {ctaLabel}
          </button>
        )}
        {secondaryLabel && (
          <button
            onClick={onSecondary}
            className="px-4 py-2 rounded-lg border border-base-600 text-gray-300 hover:bg-base-800 transition"
          >
            {secondaryLabel}
          </button>
        )}
      </div>
    </div>
  );
}
