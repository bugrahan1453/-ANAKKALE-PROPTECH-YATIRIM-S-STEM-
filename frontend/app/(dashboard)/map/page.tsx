"use client";
import dynamic from "next/dynamic";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useState } from "react";

// Leaflet SSR uyumsuz — dynamic import
const MapView = dynamic(() => import("@/components/map/MapView"), { ssr: false });

export default function MapPage() {
  const [selectedIds, setSelectedIds] = useState<string[]>([]);

  const { data } = useQuery({
    queryKey: ["listings", "map"],
    queryFn: () => api.get("/listings/", { params: { size: 100 } }).then((r) => r.data),
  });

  const { data: routeData } = useQuery({
    queryKey: ["route", selectedIds],
    queryFn: () => api.post("/geo/optimize-route", selectedIds).then((r) => r.data),
    enabled: selectedIds.length >= 2,
  });

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Harita</h1>
        {selectedIds.length > 0 && (
          <div className="flex items-center gap-3">
            <span className="text-sm text-gray-500">{selectedIds.length} ev seçili</span>
            {routeData && (
              <span className="text-sm text-blue-600 font-medium">
                {routeData.total_distance_km} km · {routeData.total_duration_min} dk
              </span>
            )}
            <button
              onClick={() => setSelectedIds([])}
              className="text-sm text-red-500 hover:text-red-700"
            >
              Temizle
            </button>
          </div>
        )}
      </div>

      <div className="bg-white rounded-xl border overflow-hidden" style={{ height: "calc(100vh - 200px)" }}>
        <MapView
          listings={data?.items ?? []}
          selectedIds={selectedIds}
          onToggleSelect={(id: string) => {
            setSelectedIds((prev) =>
              prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
            );
          }}
        />
      </div>
    </div>
  );
}
