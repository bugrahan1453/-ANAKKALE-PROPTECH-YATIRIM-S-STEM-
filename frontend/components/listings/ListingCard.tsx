"use client";
import { cn } from "@/lib/utils";
import { formatPrice } from "@/lib/utils";
import { Building2, MapPin, Clock, TrendingDown, Eye } from "lucide-react";
import Link from "next/link";

const SIGNAL_STYLES = {
  green: { bg: "bg-green-100", text: "text-green-700", label: "Fırsat" },
  yellow: { bg: "bg-yellow-100", text: "text-yellow-700", label: "Normal" },
  red: { bg: "bg-red-100", text: "text-red-700", label: "Şişirilmiş" },
};

export function ListingCard({ listing }: { listing: any }) {
  const signal = SIGNAL_STYLES[listing.price_signal as keyof typeof SIGNAL_STYLES];

  return (
    <Link href={`/listings/${listing.id}`}>
      <div className="bg-white rounded-xl border border-gray-200 hover:border-blue-300 hover:shadow-md transition-all p-5 cursor-pointer">
        {/* Üst Etiketler */}
        <div className="flex items-center gap-2 mb-3">
          {listing.is_fsbo && (
            <span className="px-2 py-0.5 bg-blue-100 text-blue-700 text-xs font-medium rounded-full">
              Sahibinden
            </span>
          )}
          {listing.is_hidden_gem && (
            <span className="px-2 py-0.5 bg-purple-100 text-purple-700 text-xs font-medium rounded-full">
              Gizli Cevher
            </span>
          )}
          {signal && (
            <span className={cn("px-2 py-0.5 text-xs font-medium rounded-full", signal.bg, signal.text)}>
              {signal.label}
            </span>
          )}
        </div>

        {/* Başlık */}
        <h3 className="font-semibold text-gray-900 text-sm line-clamp-2 mb-2">{listing.title}</h3>

        {/* Fiyat */}
        <p className="text-xl font-bold text-blue-600 mb-3">{formatPrice(listing.price)}</p>

        {/* Detaylar */}
        <div className="grid grid-cols-2 gap-2 text-xs text-gray-500">
          <div className="flex items-center gap-1">
            <MapPin className="w-3 h-3" />
            {listing.district || "—"}
          </div>
          <div className="flex items-center gap-1">
            <Building2 className="w-3 h-3" />
            {listing.room_count || "—"} · {listing.area_m2 ? `${listing.area_m2} m²` : "—"}
          </div>
          <div className="flex items-center gap-1">
            <Clock className="w-3 h-3" />
            {listing.real_days_on_market} gün
          </div>
          {listing.motivation_score && listing.motivation_score > 30 && (
            <div className="flex items-center gap-1 text-orange-600 font-medium">
              <TrendingDown className="w-3 h-3" />
              Motivasyon: {listing.motivation_score}
            </div>
          )}
        </div>

        {/* Alt Bilgi */}
        <div className="flex items-center justify-between mt-3 pt-3 border-t border-gray-100">
          <span className="text-xs text-gray-400">{listing.source_site}</span>
          {listing.roi_years && (
            <span className={cn(
              "text-xs font-medium",
              listing.roi_years <= 15 ? "text-green-600" : "text-gray-400"
            )}>
              ROI: {listing.roi_years} yıl
            </span>
          )}
        </div>
      </div>
    </Link>
  );
}
