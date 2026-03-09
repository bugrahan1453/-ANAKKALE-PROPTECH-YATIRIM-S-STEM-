"use client";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { CheckCircle, Phone, User, Bell } from "lucide-react";
import { toast } from "sonner";

const TASK_ICONS = {
  cold_call: Phone,
  follow_up: User,
  neighbor_radar: Bell,
  buyer_match: User,
  price_drop_alert: Bell,
  showing: User,
};

export function DailyTaskList({ tasks }: { tasks: any[] }) {
  const qc = useQueryClient();
  const completeMutation = useMutation({
    mutationFn: (taskId: string) => api.patch(`/tasks/${taskId}/complete`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["tasks", "today"] });
      toast.success("Görev tamamlandı!");
    },
  });

  if (!tasks.length) {
    return (
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <h3 className="font-bold text-gray-900 mb-2">Bugünkü Görevler</h3>
        <p className="text-gray-400 text-sm">Tebrikler! Bugün tüm görevler tamamlandı.</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-bold text-gray-900">Bugünkü Görevler</h3>
        <span className="text-sm text-blue-600 font-medium">{tasks.length} bekliyor</span>
      </div>

      <div className="space-y-3">
        {tasks.map((task) => {
          const Icon = TASK_ICONS[task.task_type as keyof typeof TASK_ICONS] ?? Bell;
          return (
            <div
              key={task.id}
              className="flex items-start gap-3 p-4 border border-gray-100 rounded-lg hover:border-blue-200 transition-colors"
            >
              <div className="p-2 bg-blue-50 rounded-lg mt-0.5">
                <Icon className="w-4 h-4 text-blue-600" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="font-medium text-gray-900 text-sm">{task.title}</p>
                <p className="text-xs text-gray-400 mt-0.5 capitalize">
                  {task.task_type.replace("_", " ")}
                </p>
              </div>
              <button
                onClick={() => completeMutation.mutate(task.id)}
                disabled={completeMutation.isPending}
                className="p-1.5 text-gray-300 hover:text-green-500 transition-colors"
                title="Tamamlandı"
              >
                <CheckCircle className="w-5 h-5" />
              </button>
            </div>
          );
        })}
      </div>
    </div>
  );
}
