"use client";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { StatsCard } from "@/components/dashboard/StatsCard";
import { MotivationRadar } from "@/components/dashboard/MotivationRadar";
import { DailyTaskList } from "@/components/crm/DailyTaskList";
import { BloodyMarketAlert } from "@/components/dashboard/BloodyMarketAlert";

export default function DashboardPage() {
  const { data: tasks } = useQuery({
    queryKey: ["tasks", "today"],
    queryFn: () => api.get("/tasks/today").then((r) => r.data),
  });

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">Komuta Merkezi</h1>

      {/* Üst İstatistikler */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatsCard title="Aktif İlanlar" value="1,247" trend="+12%" />
        <StatsCard title="Sahibinden" value="89" trend="+5%" color="green" />
        <StatsCard title="Bugünkü Görev" value={tasks?.length ?? 0} />
        <StatsCard title="Fırsat İlanlar" value="23" color="red" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Günlük Görev Listesi */}
        <div className="lg:col-span-2">
          <DailyTaskList tasks={tasks ?? []} />
        </div>

        {/* Kanlı Piyasa Radari */}
        <div>
          <BloodyMarketAlert />
        </div>
      </div>

      {/* Motivasyon Radar */}
      <MotivationRadar />
    </div>
  );
}
