"use client";
import { FileText, Share2, Shield, Users } from "lucide-react";

export default function ReportsPage() {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">Raporlar ve Araçlar</h1>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <ReportTool
          icon={FileText}
          title="Gerçeklik Tokadı PDF"
          description="Yüksek fiyattan girdiği için satılamayan ilanları, mahallenin gerçek m² fiyatını ve satış hızını tek tıkla şık PDF'e dönüştür"
          action="İlan detay sayfasından kullanılır"
          color="red"
        />
        <ReportTool
          icon={Users}
          title="Alıcı-Portföy Çöpçatanı"
          description="Yeni ilan düştüğünde, müşteri kayıtlarını tarayıp kriterlere uygun müşterileri otomatik eşleştir"
          action="Her saat otomatik çalışır + ilan detayından manuel tetiklenebilir"
          color="blue"
        />
        <ReportTool
          icon={Share2}
          title="Tek Tıkla Sosyal Medya"
          description="Portföy verileriyle Instagram Story, WhatsApp mesajı ve cam afişi taslağı otomatik üret"
          action="İlan detay sayfasından 'Paylaş' butonuyla"
          color="green"
        />
        <ReportTool
          icon={Shield}
          title="Hukuki Kalkan (SİT/İmar)"
          description="TKGM Parsel API ile ilan adresinin SİT alanı, zeytinlik veya imarsız tarım arazisi kontrolü"
          action="İlan detay sayfasında otomatik kontrol edilir"
          color="amber"
        />
      </div>
    </div>
  );
}

function ReportTool({ icon: Icon, title, description, action, color }: {
  icon: any; title: string; description: string; action: string; color: string;
}) {
  const colors: Record<string, string> = {
    red: "bg-red-100 text-red-600",
    blue: "bg-blue-100 text-blue-600",
    green: "bg-green-100 text-green-600",
    amber: "bg-amber-100 text-amber-600",
  };

  return (
    <div className="bg-white rounded-xl border p-6">
      <div className="flex items-center gap-3 mb-3">
        <div className={`p-3 rounded-lg ${colors[color]}`}>
          <Icon className="w-6 h-6" />
        </div>
        <h3 className="font-bold text-gray-900 text-lg">{title}</h3>
      </div>
      <p className="text-sm text-gray-600 mb-3">{description}</p>
      <p className="text-xs text-blue-600 font-medium">{action}</p>
    </div>
  );
}
