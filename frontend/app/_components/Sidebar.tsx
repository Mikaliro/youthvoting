"use client";

import DistrictSelector from "./DistrictSelector";
import FilterSliders from "./FilterSliders";
import ExportButton from "./ExportButton";
import ScoreLegend from "./ScoreLegend";

export default function Sidebar() {
  return (
    <aside className="w-80 flex-shrink-0 bg-white shadow-lg flex flex-col overflow-y-auto z-10">
      <div className="p-4 border-b border-gray-200">
        <h1 className="text-lg font-bold text-gray-900">CA Youth Voter Outreach</h1>
        <p className="text-xs text-gray-500 mt-0.5">
          18–29 population × Democratic lean by precinct
        </p>
      </div>

      <div className="flex-1 p-4 space-y-6">
        <section>
          <h2 className="text-sm font-semibold text-gray-700 mb-2">Congressional District</h2>
          <DistrictSelector />
        </section>

        <section>
          <h2 className="text-sm font-semibold text-gray-700 mb-2">Filters</h2>
          <FilterSliders />
        </section>

        <section>
          <h2 className="text-sm font-semibold text-gray-700 mb-2">Legend</h2>
          <ScoreLegend />
        </section>
      </div>

      <div className="p-4 border-t border-gray-200">
        <ExportButton />
      </div>
    </aside>
  );
}
