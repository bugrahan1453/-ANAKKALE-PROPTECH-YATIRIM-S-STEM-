"use client";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { formatPrice } from "@/lib/utils";
import { BloodyMarketAlert } from "@/components/dashboard/BloodyMarketAlert";
import { AlertTriangle, TrendingDown, Wallet, Home } from "lucide-react";

export default function RadarPage() {
  const { data: cashCows } = useQuery({
    queryKey: ["cash-cows"],
    queryFn: () => api.get("/investor/cash-cows", { params: { max_roi_years: 15 } }).then((r) => r.data),
  });

  const { data: rentalToSale } = useQuery({
    queryKey: ["rental-to-sale"],
    queryFn: () => api.get("/investor/rental-to-sale").then((r) => r.data),
  });

  const { data: macroAlerts } = useQuery({
    queryKey: ["macro-alerts"],
    queryFn: () => api.get("/investor/macro-alerts").then((r) => r.data),
  });

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">Yatırım Radarı</h1>

      {/* Makro Tetikleyiciler */}
      {macroAlerts?.length > 0 && (
        <div className="bg-amber-50 border-2 border-amber-300 rounded-xl p-5">
          <div className="flex items-center gap-2 mb-3">
            <AlertTriangle className="w-5 h-5 text-amber-600" />
            <h3 className="font-bold text-gray-900">Makro Tetikleyiciler</h3>
          </div>
          {macroAlerts.map((alert: any, i: number) => (
            <div key={i} className="bg-white rounded-lg p-4 mb-2">
              <p className="font-medium text-gray-900">{alert.message}</p>
              <p className="text-sm text-blue-600 mt-1 font-medium">{alert.action}</p>
            </div>
          ))}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Kanlı Piyasa */}
        <BloodyMarketAlert />

        {/* Cash Cow'lar */}
        <div className="bg-white rounded-xl border p-5">
          <div className="flex items-center gap-2 mb-4">
            <Wallet className="w-5 h-5 text-green-600" />
            <h3 className="font-bold text-gray-900">Nakit İnekleri (ROI ≤ 15 yıl)</h3>
          </div>
          <div className="space-y-3">
            {cashCows?.slice(0, 8).map((item: any) => (
              <div key={item.id} className="flex items-center justify-between bg-green-50 rounded-lg p-3">
                <div>
                  <p className="text-sm font-medium text-gray-900 truncate max-w-xs">{item.title}</p>
                  <p className="text-xs text-gray-500">{item.district}</p>
                </div>
                <div className="text-right">
                  <p className="text-sm font-bold text-green-700">{item.roi_years} yıl</p>
                  <p className="text-xs text-gray-500">{formatPrice(item.price)}</p>
                </div>
              </div>
            ))}
            {(!cashCows || cashCows.length === 0) && (
              <p className="text-sm text-gray-400 text-center py-4">Cash-cow bulunamadı</p>
            )}
          </div>
        </div>
      </div>

      {/* Kiralıktan Satılığa */}
      <div className="bg-white rounded-xl border p-5">
        <div className="flex items-center gap-2 mb-4">
          <Home className="w-5 h-5 text-orange-600" />
          <h3 className="font-bold text-gray-900">
            Kiralıktan Satılığa Dönüştürme ({rentalToSale?.count ?? 0} mülk)
          </h3>
          <span className="text-xs text-gray-500">45+ gündür boş</span>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {rentalToSale?.items?.slice(0, 9).map((item: any) => (
            <div key={item.id} className="bg-orange-50 rounded-lg p-3">
              <p className="text-sm font-medium text-gray-900 truncate">{item.title}</p>
              <p className="text-xs text-gray-500">{item.district} · {item.days_on_market} gün boş</p>
              <p className="text-sm text-orange-700 font-bold mt-1">{formatPrice(item.price)}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
