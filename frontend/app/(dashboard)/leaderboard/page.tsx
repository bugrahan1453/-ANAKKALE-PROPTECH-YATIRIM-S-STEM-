"use client";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Trophy, Phone, Calendar, Star } from "lucide-react";
import { cn } from "@/lib/utils";

const RANK_STYLES: Record<number, string> = {
  1: "bg-yellow-50 border-yellow-300",
  2: "bg-gray-50 border-gray-300",
  3: "bg-orange-50 border-orange-300",
};

export default function LeaderboardPage() {
  const { data: leaderboard } = useQuery({
    queryKey: ["leaderboard"],
    queryFn: () => api.get("/leaderboard/").then((r) => r.data),
  });

  const { data: rewards } = useQuery({
    queryKey: ["leaderboard-rewards"],
    queryFn: () => api.get("/leaderboard/rewards").then((r) => r.data),
  });

  return (
    <div className="space-y-6 max-w-3xl">
      <div className="flex items-center gap-3">
        <Trophy className="w-7 h-7 text-yellow-500" />
        <h1 className="text-2xl font-bold text-gray-900">Kurtlar Vadisi Leaderboard</h1>
      </div>

      {/* Hedefler */}
      {rewards && (
        <div className="bg-blue-50 border border-blue-200 rounded-xl p-5">
          <h3 className="font-bold text-gray-900 mb-2">Günlük Hedefler</h3>
          <div className="flex gap-6 text-sm">
            <div className="flex items-center gap-2">
              <Phone className="w-4 h-4 text-blue-600" />
              <span>{rewards.daily_call_target} arama</span>
            </div>
            <div className="flex items-center gap-2">
              <Calendar className="w-4 h-4 text-blue-600" />
              <span>{rewards.daily_appointment_target} randevu</span>
            </div>
            <div className="flex items-center gap-2">
              <Star className="w-4 h-4 text-amber-500" />
              <span>Ödül: En sıcak lead portföyü</span>
            </div>
          </div>
        </div>
      )}

      {/* Sıralama */}
      <div className="space-y-3">
        {leaderboard?.map((entry: any) => (
          <div
            key={entry.advisor_id}
            className={cn(
              "bg-white rounded-xl border-2 p-5 flex items-center gap-5",
              RANK_STYLES[entry.rank] || "border-gray-200"
            )}
          >
            <div className="text-3xl font-black text-gray-300 w-12 text-center">
              {entry.rank === 1 ? "🥇" : entry.rank === 2 ? "🥈" : entry.rank === 3 ? "🥉" : `#${entry.rank}`}
            </div>
            <div className="flex-1">
              <p className="font-bold text-gray-900 text-lg">{entry.advisor_name}</p>
              <div className="flex gap-4 text-sm text-gray-500 mt-1">
                <span>{entry.calls_today} arama</span>
                <span>{entry.appointments_today} randevu</span>
              </div>
            </div>
            <div className="text-right">
              <p className="text-2xl font-black text-blue-600">{entry.score}</p>
              <p className="text-xs text-gray-400">puan</p>
            </div>
          </div>
        ))}
        {(!leaderboard || leaderboard.length === 0) && (
          <div className="text-center py-12 text-gray-400">
            Bugün henüz aktivite yok — görevleri tamamlayarak sıralamanı yükselt!
          </div>
        )}
      </div>
    </div>
  );
}
