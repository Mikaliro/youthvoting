"use client";

import { useEffect, useState } from "react";
import { useFilters } from "@/hooks/useFilters";

interface DistrictStats {
  cd_number: number;
  precinct_count: number;
  priority_count: number;
  target_count: number;
}

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export default function DistrictSelector() {
  const { district, setDistrict } = useFilters();
  const [stats, setStats] = useState<DistrictStats[]>([]);

  useEffect(() => {
    fetch(`${API_URL}/api/districts`)
      .then((r) => r.json())
      .then(setStats)
      .catch(console.error);
  }, []);

  const handleChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const val = e.target.value;
    setDistrict(val === "" ? null : parseInt(val, 10));
  };

  const getLabel = (s: DistrictStats) =>
    `CA-${String(s.cd_number).padStart(2, "0")} — ${s.priority_count}P / ${s.target_count}T`;

  return (
    <select
      value={district ?? ""}
      onChange={handleChange}
      className="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
    >
      <option value="">All districts</option>
      {stats.map((s) => (
        <option key={s.cd_number} value={s.cd_number}>
          {getLabel(s)}
        </option>
      ))}
    </select>
  );
}
