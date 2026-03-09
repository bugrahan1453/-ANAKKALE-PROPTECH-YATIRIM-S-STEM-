"use client";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";

const SIGNAL_COLORS = {
  green: "bg-green-100 border-green-300 text-green-800",
  yellow: "bg-yellow-100 border-yellow-300 text-yellow-800",
  red: "bg-red-100 border-red-300 text-red-800",
};

export function MotivationRadar() {
  const { data } = useQuery({
    queryKey: ["listings", "hot"],
    queryFn: () =>
      api.get("/listings/", { params: { min_motivation_score: 50, size: 10 } }).then((r) => r.data),
  });

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-6">
      <h3 className="font-bold text-gray-900 mb-4">Yüksek Motivasyonlu Satıcılar</h3>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-gray-500 border-b">
              <th className="pb-3 font-medium">İlan</th>
              <th className="pb-3 font-medium">Fiyat</th>
              <th className="pb-3 font-medium">Motivasyon</th>
              <th className="pb-3 font-medium">DOM</th>
              <th className="pb-3 font-medium">Sinyal</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-50">
            {data?.items?.map((item: any) => (
              <tr key={item.id} className="hover:bg-gray-50 cursor-pointer">
                <td className="py-3">
                  <p className="font-medium text-gray-900 truncate max-w-xs">{item.title}</p>
                  <p className="text-gray-400 text-xs">{item.district} · {item.source_site}</p>
                </td>
                <td className="py-3 font-semibold">{item.price?.toLocaleString("tr-TR")} TL</td>
                <td className="py-3">
                  <div className="flex items-center gap-2">
                    <div className="w-16 bg-gray-100 rounded-full h-2">
                      <div
                        className="bg-orange-500 h-2 rounded-full"
                        style={{ width: `${item.motivation_score}%` }}
                      />
                    </div>
                    <span className="text-xs font-bold text-orange-600">{item.motivation_score}</span>
                  </div>
                </td>
                <td className="py-3 text-gray-600">{item.real_days_on_market} gün</td>
                <td className="py-3">
                  <span className={cn(
                    "px-2 py-1 rounded-full text-xs font-medium border",
                    SIGNAL_COLORS[item.price_signal as keyof typeof SIGNAL_COLORS] ?? "bg-gray-100"
                  )}>
                    {item.price_signal === "green" ? "Fırsat" : item.price_signal === "red" ? "Şişirilmiş" : "Normal"}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
