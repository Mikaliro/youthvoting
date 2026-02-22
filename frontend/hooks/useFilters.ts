"use client";

import { create } from "zustand";

export interface FilterState {
  district: number | null;
  youthMin: number;
  marginFloor: number;
  setDistrict: (d: number | null) => void;
  setYouthMin: (v: number) => void;
  setMarginFloor: (v: number) => void;
}

export const useFilters = create<FilterState>((set) => ({
  district: null,
  youthMin: 0.0,
  marginFloor: -1.0,
  setDistrict: (district) => set({ district }),
  setYouthMin: (youthMin) => set({ youthMin }),
  setMarginFloor: (marginFloor) => set({ marginFloor }),
}));

/** Build query string from current filter state */
export function buildFilterParams(state: Pick<FilterState, "district" | "youthMin" | "marginFloor">): string {
  const params = new URLSearchParams({
    youth_min: state.youthMin.toString(),
    margin_floor: state.marginFloor.toString(),
  });
  if (state.district !== null) {
    params.set("district", state.district.toString());
  }
  return params.toString();
}
