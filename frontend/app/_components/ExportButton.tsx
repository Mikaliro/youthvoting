"use client";

import { useFilters, buildFilterParams } from "@/hooks/useFilters";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export default function ExportButton() {
  const { district, youthMin, marginFloor } = useFilters();

  const handleExport = () => {
    const params = buildFilterParams({ district, youthMin, marginFloor });
    window.open(`${API_URL}/api/export/csv?${params}`, "_blank");
  };

  return (
    <button
      onClick={handleExport}
      className="w-full rounded-md bg-blue-700 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-800 active:bg-blue-900 transition-colors"
    >
      Export CSV
    </button>
  );
}
