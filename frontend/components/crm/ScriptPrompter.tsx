"use client";
import { MessageSquare } from "lucide-react";

interface Props {
  title: string;
  script: string | null;
}

export function ScriptPrompter({ title, script }: Props) {
  if (!script) {
    return (
      <div className="bg-white rounded-xl border p-6 text-center text-gray-400">
        <p className="text-sm">Bu görev için senaryo bulunmuyor</p>
      </div>
    );
  }

  const lines = script.split("\n").filter(Boolean);

  return (
    <div className="bg-white rounded-xl border p-6">
      <div className="flex items-center gap-2 mb-4">
        <div className="p-2 bg-blue-100 rounded-lg">
          <MessageSquare className="w-5 h-5 text-blue-600" />
        </div>
        <div>
          <h3 className="font-bold text-gray-900">Akıllı Tele-Prompter</h3>
          <p className="text-xs text-gray-500">{title}</p>
        </div>
      </div>

      <div className="space-y-3">
        {lines.map((line, i) => {
          const isQuestion = line.startsWith("S:") || line.startsWith("Soru:");
          const isAnswer = line.startsWith("C:") || line.startsWith("Cevap:");
          const isInstruction = line.startsWith("[") || line.startsWith("*");

          return (
            <div
              key={i}
              className={
                isQuestion
                  ? "bg-gray-100 rounded-lg p-3 text-sm font-medium text-gray-700"
                  : isAnswer
                  ? "bg-blue-50 rounded-lg p-3 text-sm text-blue-800 border-l-4 border-blue-400"
                  : isInstruction
                  ? "text-xs text-amber-600 italic px-3"
                  : "px-3 text-sm text-gray-600"
              }
            >
              {line}
            </div>
          );
        })}
      </div>
    </div>
  );
}
