"use client";

import { useFilters } from "@/hooks/useFilters";

function pct(v: number) {
  return `${Math.round(v * 100)}%`;
}

export default function FilterSliders() {
  const { youthMin, marginFloor, setYouthMin, setMarginFloor } = useFilters();

  return (
    <div className="space-y-4">
      <div>
        <div className="flex justify-between text-xs text-gray-600 mb-1">
          <label htmlFor="youth-min">Min. youth share (18–29)</label>
          <span className="font-mono font-medium">{pct(youthMin)}</span>
        </div>
        <input
          id="youth-min"
          type="range"
          min={0}
          max={0.5}
          step={0.01}
          value={youthMin}
          onChange={(e) => setYouthMin(parseFloat(e.target.value))}
          className="w-full accent-blue-700"
        />
        <div className="flex justify-between text-xs text-gray-400 mt-0.5">
          <span>0%</span>
          <span>50%</span>
        </div>
      </div>

      <div>
        <div className="flex justify-between text-xs text-gray-600 mb-1">
          <label htmlFor="margin-floor">Min. Dem margin</label>
          <span className="font-mono font-medium">
            {marginFloor >= 0 ? "+" : ""}
            {pct(marginFloor)}
          </span>
        </div>
        <input
          id="margin-floor"
          type="range"
          min={-0.5}
          max={0.5}
          step={0.01}
          value={marginFloor}
          onChange={(e) => setMarginFloor(parseFloat(e.target.value))}
          className="w-full accent-blue-700"
        />
        <div className="flex justify-between text-xs text-gray-400 mt-0.5">
          <span>−50%</span>
          <span>+50%</span>
        </div>
      </div>
    </div>
  );
}
