"use client";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useState } from "react";
import { ListingCard } from "@/components/listings/ListingCard";
import { ListingFilters } from "@/components/listings/ListingFilters";

export default function ListingsPage() {
  const [filters, setFilters] = useState({
    district: "",
    min_price: "",
    max_price: "",
    rooms: "",
    is_fsbo: undefined as boolean | undefined,
    price_signal: "",
    is_hidden_gem: undefined as boolean | undefined,
    min_motivation_score: "",
    page: 1,
  });

  const params = Object.fromEntries(
    Object.entries(filters).filter(([_, v]) => v !== "" && v !== undefined)
  );

  const { data, isLoading } = useQuery({
    queryKey: ["listings", params],
    queryFn: () => api.get("/listings/", { params }).then((r) => r.data),
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">İlan Havuzu</h1>
        <span className="text-sm text-gray-500">{data?.total ?? 0} ilan bulundu</span>
      </div>

      <ListingFilters filters={filters} onChange={setFilters} />

      {isLoading ? (
        <div className="text-center py-12 text-gray-400">Yükleniyor...</div>
      ) : (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
            {data?.items?.map((listing: any) => (
              <ListingCard key={listing.id} listing={listing} />
            ))}
          </div>

          {/* Sayfalama */}
          {data?.total > (data?.size ?? 20) && (
            <div className="flex justify-center gap-2">
              <button
                onClick={() => setFilters((f) => ({ ...f, page: Math.max(1, f.page - 1) }))}
                disabled={filters.page === 1}
                className="px-4 py-2 border rounded-lg text-sm disabled:opacity-30"
              >
                Önceki
              </button>
              <span className="px-4 py-2 text-sm text-gray-500">
                Sayfa {filters.page} / {Math.ceil(data.total / data.size)}
              </span>
              <button
                onClick={() => setFilters((f) => ({ ...f, page: f.page + 1 }))}
                disabled={filters.page * (data?.size ?? 20) >= (data?.total ?? 0)}
                className="px-4 py-2 border rounded-lg text-sm disabled:opacity-30"
              >
                Sonraki
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
