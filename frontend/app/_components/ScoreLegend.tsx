"use client";

const TIERS = [
  { label: "Priority",  description: "Score ≥ 70%", color: "#1a237e" },
  { label: "Target",    description: "Score ≥ 50%", color: "#3949ab" },
  { label: "Watchlist", description: "Score ≥ 30%", color: "#7986cb" },
  { label: "Low",       description: "Score < 30%",  color: "#c5cae9" },
];

export default function ScoreLegend() {
  return (
    <div className="space-y-1.5">
      {TIERS.map((t) => (
        <div key={t.label} className="flex items-center gap-2">
          <span
            className="inline-block w-4 h-4 rounded-sm flex-shrink-0"
            style={{ backgroundColor: t.color }}
          />
          <span className="text-sm text-gray-800 font-medium w-20">{t.label}</span>
          <span className="text-xs text-gray-500">{t.description}</span>
        </div>
      ))}
      <p className="text-xs text-gray-400 mt-2 leading-tight">
        Score = 60% youth share + 40% Dem margin (normalized)
      </p>
    </div>
  );
}
