"use client";
import { useQuery, useMutation } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { formatPrice } from "@/lib/utils";
import { useParams } from "next/navigation";
import { cn } from "@/lib/utils";
import {
  MapPin, Clock, Building2, TrendingDown, Shield,
  FileText, Share2, Users, AlertTriangle
} from "lucide-react";
import { toast } from "sonner";

export default function ListingDetailPage() {
  const { id } = useParams();

  const { data: listing, isLoading } = useQuery({
    queryKey: ["listing", id],
    queryFn: () => api.get(`/listings/${id}`).then((r) => r.data),
  });

  const { data: arv } = useQuery({
    queryKey: ["arv", id],
    queryFn: () => api.get(`/investor/arv/${id}`).then((r) => r.data),
    enabled: !!listing,
  });

  const { data: roi } = useQuery({
    queryKey: ["roi", id],
    queryFn: () => api.get(`/investor/roi/${id}`).then((r) => r.data),
    enabled: !!listing,
  });

  const { data: legal } = useQuery({
    queryKey: ["legal", id],
    queryFn: () => api.get(`/legal/check/${id}`).then((r) => r.data),
    enabled: !!listing,
  });

  const { data: matches } = useQuery({
    queryKey: ["buyer-match", id],
    queryFn: () => api.get(`/reports/buyer-match/${id}`).then((r) => r.data),
    enabled: !!listing,
  });

  const pdfMutation = useMutation({
    mutationFn: () => api.get(`/reports/reality-slap/${id}`, { responseType: "blob" }),
    onSuccess: (res) => {
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const a = document.createElement("a");
      a.href = url;
      a.download = `ekspertiz_${id}.pdf`;
      a.click();
      toast.success("PDF indirildi!");
    },
  });

  const socialMutation = useMutation({
    mutationFn: () => api.post(`/reports/social-media/${id}`).then((r) => r.data),
    onSuccess: (data) => {
      navigator.clipboard.writeText(data.whatsapp.message);
      toast.success("WhatsApp mesajı panoya kopyalandı!");
    },
  });

  if (isLoading) return <div className="text-center py-12 text-gray-400">Yükleniyor...</div>;
  if (!listing) return <div className="text-center py-12 text-gray-400">İlan bulunamadı</div>;

  return (
    <div className="space-y-6 max-w-5xl">
      {/* Üst Başlık */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">{listing.title}</h1>
          <p className="text-gray-500 flex items-center gap-1 mt-1">
            <MapPin className="w-4 h-4" />
            {listing.district} / {listing.neighborhood}
          </p>
        </div>
        <div className="text-right">
          <p className="text-3xl font-bold text-blue-600">{formatPrice(listing.price)}</p>
          {listing.area_m2 && (
            <p className="text-sm text-gray-500">
              {formatPrice(listing.price / listing.area_m2)} / m²
            </p>
          )}
        </div>
      </div>

      {/* Aksiyon Butonları */}
      <div className="flex flex-wrap gap-3">
        <button onClick={() => pdfMutation.mutate()} className="flex items-center gap-2 px-4 py-2 bg-red-600 text-white rounded-lg text-sm font-medium hover:bg-red-700">
          <FileText className="w-4 h-4" /> Gerçeklik Tokadı PDF
        </button>
        <button onClick={() => socialMutation.mutate()} className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg text-sm font-medium hover:bg-green-700">
          <Share2 className="w-4 h-4" /> Sosyal Medya Paylaş
        </button>
        <a href={listing.source_url} target="_blank" className="flex items-center gap-2 px-4 py-2 border border-gray-200 rounded-lg text-sm font-medium hover:bg-gray-50">
          Orijinal İlan →
        </a>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Sol — Detaylar */}
        <div className="lg:col-span-2 space-y-4">
          {/* Özellikler */}
          <div className="bg-white rounded-xl border p-5">
            <h3 className="font-bold text-gray-900 mb-3">Mülk Bilgileri</h3>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4 text-sm">
              <InfoRow icon={Building2} label="Oda" value={listing.room_count} />
              <InfoRow icon={Building2} label="Alan" value={listing.area_m2 ? `${listing.area_m2} m²` : "—"} />
              <InfoRow icon={Clock} label="Piyasada" value={`${listing.real_days_on_market} gün`} />
              <InfoRow icon={Clock} label="Kaynak" value={listing.source_site} />
              <InfoRow icon={Clock} label="FSBO" value={listing.is_fsbo ? "Sahibinden" : "Emlakçı"} />
              <InfoRow icon={TrendingDown} label="Motivasyon" value={listing.motivation_score ? `${listing.motivation_score}/100` : "—"} />
            </div>
          </div>

          {/* ARV Hesabı */}
          {arv && arv.arv > 0 && (
            <div className="bg-white rounded-xl border p-5">
              <h3 className="font-bold text-gray-900 mb-3">Flipping (ARV) Hesabı</h3>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div><span className="text-gray-500">Mevcut Fiyat:</span> <strong>{formatPrice(arv.current_price)}</strong></div>
                <div><span className="text-gray-500">Tadilat Sonrası Değer:</span> <strong className="text-green-600">{formatPrice(arv.arv)}</strong></div>
                <div><span className="text-gray-500">Tahmini Tadilat:</span> <strong>{formatPrice(arv.renovation_cost)}</strong></div>
                <div>
                  <span className="text-gray-500">Net Kar:</span>{" "}
                  <strong className={arv.net_profit > 0 ? "text-green-600" : "text-red-600"}>
                    {formatPrice(arv.net_profit)} ({arv.roi_pct > 0 ? "+" : ""}{arv.roi_pct}%)
                  </strong>
                </div>
              </div>
            </div>
          )}

          {/* ROI Hesabı */}
          {roi && (
            <div className="bg-white rounded-xl border p-5">
              <h3 className="font-bold text-gray-900 mb-3">Kira Getirisi (ROI)</h3>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div><span className="text-gray-500">Aylık Kira:</span> <strong>{formatPrice(roi.monthly_rent)}</strong></div>
                <div><span className="text-gray-500">Yıllık Kira:</span> <strong>{formatPrice(roi.annual_rent)}</strong></div>
                <div>
                  <span className="text-gray-500">Amortisman:</span>{" "}
                  <strong className={roi.is_cash_cow ? "text-green-600" : "text-gray-600"}>
                    {roi.roi_years} yıl {roi.is_cash_cow ? "🐄" : ""}
                  </strong>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Sağ — Yan Panel */}
        <div className="space-y-4">
          {/* Hukuki Kontrol */}
          {legal && (
            <div className={cn(
              "rounded-xl border p-5",
              legal.risk_level === "high" ? "border-red-300 bg-red-50" :
              legal.risk_level === "medium" ? "border-yellow-300 bg-yellow-50" :
              "border-green-300 bg-green-50"
            )}>
              <div className="flex items-center gap-2 mb-3">
                <Shield className="w-5 h-5" />
                <h3 className="font-bold text-gray-900">Hukuki Kalkan</h3>
              </div>
              {legal.warnings.map((w: string, i: number) => (
                <p key={i} className="text-sm mb-1">{w}</p>
              ))}
            </div>
          )}

          {/* Alıcı Eşleşmeleri */}
          {matches && matches.matches_count > 0 && (
            <div className="bg-white rounded-xl border p-5">
              <div className="flex items-center gap-2 mb-3">
                <Users className="w-5 h-5 text-blue-600" />
                <h3 className="font-bold text-gray-900">Eşleşen Müşteriler</h3>
              </div>
              <div className="space-y-3">
                {matches.matches.slice(0, 5).map((m: any) => (
                  <div key={m.customer_id} className="bg-blue-50 rounded-lg p-3">
                    <p className="text-sm font-medium">{m.customer_name}</p>
                    <p className="text-xs text-gray-500">{m.match_reasons.join(" · ")}</p>
                    <p className="text-xs text-blue-600 mt-1">{m.phone}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Sinyal */}
          {listing.price_signal && (
            <div className={cn(
              "rounded-xl border p-5",
              listing.price_signal === "green" ? "bg-green-50 border-green-200" :
              listing.price_signal === "red" ? "bg-red-50 border-red-200" :
              "bg-yellow-50 border-yellow-200"
            )}>
              <h3 className="font-bold text-gray-900 mb-1">Emsal Barometre</h3>
              <p className="text-sm">
                {listing.price_signal === "green" ? "Emsal fiyatın altında — FIRSAT" :
                 listing.price_signal === "red" ? "Emsal fiyatın üstünde — ŞİŞİRİLMİŞ" :
                 "Piyasa ortalamasında"}
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function InfoRow({ icon: Icon, label, value }: { icon: any; label: string; value: string | null }) {
  return (
    <div className="flex items-center gap-2">
      <Icon className="w-4 h-4 text-gray-400" />
      <span className="text-gray-500">{label}:</span>
      <span className="font-medium text-gray-900">{value || "—"}</span>
    </div>
  );
}
