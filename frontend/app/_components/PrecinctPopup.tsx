"use client";

const TIER_COLORS: Record<string, string> = {
  priority:  "bg-[#1a237e] text-white",
  target:    "bg-[#3949ab] text-white",
  watchlist: "bg-[#7986cb] text-white",
  low:       "bg-[#c5cae9] text-gray-800",
};

interface Props {
  properties: {
    precinct_id: string;
    county_name: string;
    cd_number: number | null;
    total_pop: number | null;
    pop_18_29: number | null;
    youth_share: number | null;
    dem_margin: number | null;
    dem_pct: number | null;
    score: number | null;
    tier: string | null;
    dem_votes: number | null;
    rep_votes: number | null;
    total_votes: number | null;
  };
  onClose: () => void;
}

function fmt(v: number | null, decimals = 1): string {
  if (v === null || v === undefined) return "—";
  return (v * 100).toFixed(decimals) + "%";
}

function fmtNum(v: number | null): string {
  if (v === null || v === undefined) return "—";
  return v.toLocaleString();
}

export default function PrecinctPopup({ properties: p, onClose }: Props) {
  const tier = p.tier ?? "low";
  const tierClass = TIER_COLORS[tier] ?? "bg-gray-200 text-gray-800";

  return (
    <div className="absolute top-4 right-4 z-20 w-72 bg-white rounded-xl shadow-xl border border-gray-200 overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 bg-gray-50 border-b border-gray-200">
        <div>
          <p className="text-xs text-gray-500">{p.county_name} County</p>
          <p className="text-sm font-semibold text-gray-900 font-mono">{p.precinct_id}</p>
        </div>
        <div className="flex items-center gap-2">
          <span className={`text-xs font-bold px-2 py-0.5 rounded-full uppercase ${tierClass}`}>
            {tier}
          </span>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-700 text-lg leading-none"
            aria-label="Close"
          >
            ×
          </button>
        </div>
      </div>

      {/* Stats grid */}
      <div className="p-4 grid grid-cols-2 gap-3">
        <Stat label="Youth share (18–29)" value={fmt(p.youth_share)} />
        <Stat label="Dem margin" value={(p.dem_margin !== null ? (p.dem_margin >= 0 ? "+" : "") + fmt(p.dem_margin) : "—")} />
        <Stat label="Composite score" value={p.score !== null ? p.score.toFixed(3) : "—"} />
        <Stat label="Dem %" value={fmt(p.dem_pct)} />
        <Stat label="Total pop." value={fmtNum(p.total_pop)} />
        <Stat label="Pop. 18–29" value={fmtNum(p.pop_18_29)} />
        <Stat label="Total votes" value={fmtNum(p.total_votes)} />
        <Stat label="CD" value={p.cd_number !== null ? `CA-${String(p.cd_number).padStart(2, "0")}` : "—"} />
      </div>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-xs text-gray-500">{label}</p>
      <p className="text-sm font-semibold text-gray-900">{value}</p>
    </div>
  );
}
