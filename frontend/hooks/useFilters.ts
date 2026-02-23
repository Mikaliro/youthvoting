"use client";

import { create } from "zustand";

export interface FilterState {
  // Live slider values
  district: number | null;
  youthMin: number;
  marginFloor: number;
  setDistrict: (d: number | null) => void;
  setYouthMin: (v: number) => void;
  setMarginFloor: (v: number) => void;

  // Applied values — only update on "Apply Filters"
  appliedDistrict: number | null;
  appliedYouthMin: number;
  appliedMarginFloor: number;
  applyFilters: () => void;
}

export const useFilters = create<FilterState>((set, get) => ({
  district: null,
  youthMin: 0.15,
  marginFloor: 0.0,
  setDistrict: (district) => set({ district }),
  setYouthMin: (youthMin) => set({ youthMin }),
  setMarginFloor: (marginFloor) => set({ marginFloor }),

  appliedDistrict: null,
  appliedYouthMin: 0.15,
  appliedMarginFloor: 0.0,
  applyFilters: () => {
    const { district, youthMin, marginFloor } = get();
    set({ appliedDistrict: district, appliedYouthMin: youthMin, appliedMarginFloor: marginFloor });
  },
}));

export function buildFilterParams(state: Pick<FilterState, "appliedDistrict" | "appliedYouthMin" | "appliedMarginFloor">): string {
  const params = new URLSearchParams({
    youth_min: state.appliedYouthMin.toString(),
    margin_floor: state.appliedMarginFloor.toString(),
  });
  if (state.appliedDistrict !== null) {
    params.set("district", state.appliedDistrict.toString());
  }
  return params.toString();
}
