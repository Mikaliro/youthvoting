"use client";

import { useEffect, useRef, useState } from "react";
import mapboxgl from "mapbox-gl";
import "mapbox-gl/dist/mapbox-gl.css";
import { useFilters, buildFilterParams } from "@/hooks/useFilters";
import PrecinctPopup from "./PrecinctPopup";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const MAPBOX_TOKEN = process.env.NEXT_PUBLIC_MAPBOX_TOKEN ?? "";

// Tier → fill color expression (matches scripts/config.py TIERS)
const TIER_COLOR_EXPRESSION: mapboxgl.Expression = [
  "match",
  ["get", "tier"],
  "priority",  "#1a237e",
  "target",    "#3949ab",
  "watchlist", "#7986cb",
  "low",       "#c5cae9",
  "#e0e0e0", // default / null
];

interface PrecinctProperties {
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
}

export default function MapView() {
  const mapContainer = useRef<HTMLDivElement>(null);
  const map = useRef<mapboxgl.Map | null>(null);
  const [selectedPrecinct, setSelectedPrecinct] = useState<PrecinctProperties | null>(null);
  const { district, youthMin, marginFloor } = useFilters();

  // Initialize map
  useEffect(() => {
    if (!mapContainer.current || map.current) return;

    mapboxgl.accessToken = MAPBOX_TOKEN;

    map.current = new mapboxgl.Map({
      container: mapContainer.current,
      style: "mapbox://styles/mapbox/light-v11",
      center: [-119.4179, 36.7783], // California center
      zoom: 5.5,
      minZoom: 4,
      maxBounds: [
        [-128, 22],  // SW corner (covers Hawaii + contiguous US)
        [-64, 52],   // NE corner
      ],
    });

    map.current.addControl(new mapboxgl.NavigationControl(), "top-right");

    map.current.on("load", () => {
      map.current!.addSource("precincts", {
        type: "geojson",
        data: { type: "FeatureCollection", features: [] },
      });

      map.current!.addLayer({
        id: "precincts-fill",
        type: "fill",
        source: "precincts",
        paint: {
          "fill-color": TIER_COLOR_EXPRESSION,
          "fill-opacity": 0.7,
        },
      });

      map.current!.addLayer({
        id: "precincts-outline",
        type: "line",
        source: "precincts",
        paint: {
          "line-color": "#ffffff",
          "line-width": 0.5,
          "line-opacity": 0.6,
        },
      });

      // Click handler
      map.current!.on("click", "precincts-fill", (e) => {
        if (e.features && e.features.length > 0) {
          setSelectedPrecinct(e.features[0].properties as PrecinctProperties);
        }
      });

      map.current!.on("mouseenter", "precincts-fill", () => {
        map.current!.getCanvas().style.cursor = "pointer";
      });

      map.current!.on("mouseleave", "precincts-fill", () => {
        map.current!.getCanvas().style.cursor = "";
      });
    });

    return () => {
      map.current?.remove();
      map.current = null;
    };
  }, []);

  // Re-fetch GeoJSON when filters change
  useEffect(() => {
    if (!map.current) return;

    const params = buildFilterParams({ district, youthMin, marginFloor });
    const url = `${API_URL}/api/precincts?${params}`;

    fetch(url)
      .then((r) => r.json())
      .then((geojson) => {
        const source = map.current?.getSource("precincts") as mapboxgl.GeoJSONSource | undefined;
        source?.setData(geojson);
      })
      .catch(console.error);
  }, [district, youthMin, marginFloor]);

  return (
    <div className="relative w-full h-full">
      <div ref={mapContainer} className="w-full h-full" />
      {selectedPrecinct && (
        <PrecinctPopup
          properties={selectedPrecinct}
          onClose={() => setSelectedPrecinct(null)}
        />
      )}
    </div>
  );
}
