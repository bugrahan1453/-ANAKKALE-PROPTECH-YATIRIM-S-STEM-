"use client";
import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { formatPrice } from "@/lib/utils";
import { Calculator, TrendingUp } from "lucide-react";
import { cn } from "@/lib/utils";

export default function ValuationPage() {
  const [form, setForm] = useState({
    price: "", area_m2: "", neighborhood: "Çanakkale Merkez", room_count: "3+1",
  });

  const barometerMutation = useMutation({
    mutationFn: (data: any) =>
      api.post(`${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8002"}/ai/valuation/barometer`, data).then((r) => r.data),
  });

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    barometerMutation.mutate({
      listing_id: "manual",
      price: Number(form.price),
      area_m2: Number(form.area_m2),
      neighborhood: form.neighborhood,
      room_count: form.room_count,
    });
  }

  const result = barometerMutation.data;

  return (
    <div className="space-y-6 max-w-3xl">
      <h1 className="text-2xl font-bold text-gray-900">Emsal Değerleme</h1>

      <form onSubmit={handleSubmit} className="bg-white rounded-xl border p-6 space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Fiyat (TL)</label>
            <input type="number" value={form.price} onChange={(e) => setForm({ ...form, price: e.target.value })} className="w-full px-4 py-2 border rounded-lg text-sm" required />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Alan (m²)</label>
            <input type="number" value={form.area_m2} onChange={(e) => setForm({ ...form, area_m2: e.target.value })} className="w-full px-4 py-2 border rounded-lg text-sm" required />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Mahalle</label>
            <select value={form.neighborhood} onChange={(e) => setForm({ ...form, neighborhood: e.target.value })} className="w-full px-4 py-2 border rounded-lg text-sm">
              {["Kepez", "Barbaros", "Güzelyalı", "Çanakkale Merkez", "Çan", "Biga"].map((n) => (
                <option key={n}>{n}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Oda</label>
            <select value={form.room_count} onChange={(e) => setForm({ ...form, room_count: e.target.value })} className="w-full px-4 py-2 border rounded-lg text-sm">
              {["1+1", "2+1", "3+1", "4+1"].map((r) => <option key={r}>{r}</option>)}
            </select>
          </div>
        </div>
        <button type="submit" className="flex items-center gap-2 px-6 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700">
          <Calculator className="w-4 h-4" /> Değerle
        </button>
      </form>

      {result && (
        <div className={cn(
          "rounded-xl border-2 p-6",
          result.signal === "green" ? "border-green-300 bg-green-50" :
          result.signal === "red" ? "border-red-300 bg-red-50" :
          "border-yellow-300 bg-yellow-50"
        )}>
          <div className="flex items-center gap-3 mb-4">
            <TrendingUp className="w-6 h-6" />
            <div>
              <h3 className="font-bold text-lg text-gray-900">{result.label}</h3>
              <p className="text-sm text-gray-600">Sapma: {result.deviation_pct > 0 ? "+" : ""}{result.deviation_pct}%</p>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <p className="text-gray-500">Girilen m² Fiyat</p>
              <p className="text-xl font-bold">{formatPrice(result.price_per_m2)}/m²</p>
            </div>
            <div>
              <p className="text-gray-500">Mahalle Ortalaması</p>
              <p className="text-xl font-bold">{formatPrice(result.neighborhood_avg_per_m2)}/m²</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
