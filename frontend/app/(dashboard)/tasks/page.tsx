"use client";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { DailyTaskList } from "@/components/crm/DailyTaskList";
import { ScriptPrompter } from "@/components/crm/ScriptPrompter";
import { useState } from "react";

export default function TasksPage() {
  const [selectedTaskId, setSelectedTaskId] = useState<string | null>(null);

  const { data: tasks } = useQuery({
    queryKey: ["tasks", "today"],
    queryFn: () => api.get("/tasks/today").then((r) => r.data),
  });

  const { data: script } = useQuery({
    queryKey: ["script", selectedTaskId],
    queryFn: () => api.get(`/tasks/${selectedTaskId}/script`).then((r) => r.data),
    enabled: !!selectedTaskId,
  });

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">Görev Merkezi</h1>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div>
          <DailyTaskList tasks={tasks ?? []} />
          {tasks?.map((t: any) => (
            <button
              key={t.id}
              onClick={() => setSelectedTaskId(t.id)}
              className="block w-full text-left text-xs text-blue-600 px-4 py-1 hover:bg-blue-50"
            >
              Senaryoyu göster: {t.title}
            </button>
          ))}
        </div>

        <div>
          {script ? (
            <ScriptPrompter title={script.title} script={script.script} />
          ) : (
            <div className="bg-white rounded-xl border p-6 text-center text-gray-400">
              <p className="text-sm">Konuşma senaryosu görmek için bir görev seçin</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
