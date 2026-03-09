"use client";
import { Search, Filter } from "lucide-react";

const DISTRICTS = [
  "Tümü", "Kepez", "Barbaros", "Güzelyalı", "Çanakkale Merkez",
  "Çan", "Biga", "Ezine", "Ayvacık", "Bayramiç", "Lapseki", "Gelibolu",
];

const ROOMS = ["Tümü", "1+0", "1+1", "2+1", "3+1", "4+1", "5+"];

interface Props {
  filters: Record<string, any>;
  onChange: (f: any) => void;
}

export function ListingFilters({ filters, onChange }: Props) {
  const set = (key: string, value: any) =>
    onChange({ ...filters, [key]: value, page: 1 });

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-4">
      <div className="flex items-center gap-2 mb-3">
        <Filter className="w-4 h-4 text-gray-400" />
        <span className="text-sm font-medium text-gray-700">Filtreler</span>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3">
        {/* İlçe */}
        <select
          value={filters.district}
          onChange={(e) => set("district", e.target.value || "")}
          className="px-3 py-2 border border-gray-200 rounded-lg text-sm"
        >
          {DISTRICTS.map((d) => (
            <option key={d} value={d === "Tümü" ? "" : d}>{d}</option>
          ))}
        </select>

        {/* Oda */}
        <select
          value={filters.rooms}
          onChange={(e) => set("rooms", e.target.value || "")}
          className="px-3 py-2 border border-gray-200 rounded-lg text-sm"
        >
          {ROOMS.map((r) => (
            <option key={r} value={r === "Tümü" ? "" : r}>{r}</option>
          ))}
        </select>

        {/* Min Fiyat */}
        <input
          type="number"
          placeholder="Min Fiyat"
          value={filters.min_price}
          onChange={(e) => set("min_price", e.target.value)}
          className="px-3 py-2 border border-gray-200 rounded-lg text-sm"
        />

        {/* Max Fiyat */}
        <input
          type="number"
          placeholder="Max Fiyat"
          value={filters.max_price}
          onChange={(e) => set("max_price", e.target.value)}
          className="px-3 py-2 border border-gray-200 rounded-lg text-sm"
        />

        {/* Sahibinden */}
        <select
          value={filters.is_fsbo === undefined ? "" : String(filters.is_fsbo)}
          onChange={(e) => set("is_fsbo", e.target.value === "" ? undefined : e.target.value === "true")}
          className="px-3 py-2 border border-gray-200 rounded-lg text-sm"
        >
          <option value="">Tüm İlanlar</option>
          <option value="true">Sahibinden</option>
          <option value="false">Emlakçı</option>
        </select>

        {/* Sinyal */}
        <select
          value={filters.price_signal}
          onChange={(e) => set("price_signal", e.target.value)}
          className="px-3 py-2 border border-gray-200 rounded-lg text-sm"
        >
          <option value="">Tüm Sinyaller</option>
          <option value="green">Fırsat (Yeşil)</option>
          <option value="yellow">Normal (Sarı)</option>
          <option value="red">Şişirilmiş (Kırmızı)</option>
        </select>
      </div>

      {/* Özel Filtreler */}
      <div className="flex items-center gap-4 mt-3">
        <label className="flex items-center gap-2 text-sm text-gray-600 cursor-pointer">
          <input
            type="checkbox"
            checked={filters.is_hidden_gem === true}
            onChange={(e) => set("is_hidden_gem", e.target.checked ? true : undefined)}
            className="rounded border-gray-300"
          />
          Gizli Cevherler
        </label>
        <div className="flex items-center gap-2">
          <label className="text-sm text-gray-600">Min Motivasyon:</label>
          <input
            type="number"
            min={0}
            max={100}
            value={filters.min_motivation_score}
            onChange={(e) => set("min_motivation_score", e.target.value)}
            className="w-16 px-2 py-1 border border-gray-200 rounded text-sm"
            placeholder="50"
          />
        </div>
      </div>
    </div>
  );
}
