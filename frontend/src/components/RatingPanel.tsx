interface RatingPanelProps {
  ratingSummary: Record<string, number>;
}

export function RatingPanel({ ratingSummary }: RatingPanelProps) {
  const entries = Object.entries(ratingSummary);

  if (entries.length === 0) {
    return (
      <div className="rounded-xl border border-brand-600/30 bg-base-900/80 p-4 text-sm text-slate-400 shadow-md">
        <p className="font-medium text-brand-400">Live Rating</p>
        <p className="mt-1 text-xs">Answer questions to see your per-skill score build in real time.</p>
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-brand-600/30 bg-base-900/80 p-4 text-sm text-slate-200 shadow-md">
      <p className="font-medium text-brand-400">Live Rating</p>
      <div className="mt-3 space-y-2">
        {entries.map(([skill, score]) => (
          <div key={skill} className="flex items-center justify-between gap-3">
            <span className="text-xs uppercase tracking-wide text-slate-400">{skill.replace(/_/g, " ")}</span>
            <div className="flex-1 mx-3 h-2 rounded-full bg-brand-600/20">
              <div
                className="h-2 rounded-full bg-brand-500"
                style={{ width: `${Math.min(100, Math.max(0, score))}%` }}
              />
            </div>
            <span className="text-sm font-semibold text-brand-400">{Math.round(score)}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
