"use client";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { AlertTriangle } from "lucide-react";

export function BloodyMarketAlert() {
  const { data } = useQuery({
    queryKey: ["radar", "bloody-market"],
    queryFn: () => api.get("/listings/radar/bloody-market").then((r) => r.data),
    refetchInterval: 60_000, // Her dakika yenile
  });

  return (
    <div className="bg-white rounded-xl border-2 border-red-200 p-5">
      <div className="flex items-center gap-2 mb-4">
        <div className="p-2 bg-red-100 rounded-lg">
          <AlertTriangle className="w-5 h-5 text-red-600" />
        </div>
        <div>
          <h3 className="font-bold text-gray-900">Kanlı Piyasa Radarı</h3>
          <p className="text-xs text-gray-500">Garantili değerin %20 altı</p>
        </div>
      </div>

      {data?.count === 0 ? (
        <p className="text-sm text-gray-400 text-center py-4">Şu an kritik ilan yok</p>
      ) : (
        <div className="space-y-2">
          {data?.items?.slice(0, 5).map((item: any) => (
            <div key={item.id} className="bg-red-50 rounded-lg p-3">
              <p className="text-sm font-medium text-gray-900 truncate">{item.title}</p>
              <p className="text-sm text-red-700 font-bold">
                {item.price?.toLocaleString("tr-TR")} TL
              </p>
              <p className="text-xs text-gray-500">{item.district} · {item.real_days_on_market} gün</p>
            </div>
          ))}
          {data?.count > 5 && (
            <p className="text-xs text-red-600 text-center font-medium">
              +{data.count - 5} ilan daha →
            </p>
          )}
        </div>
      )}
    </div>
  );
}
