"use client";
import { Bell, Mic } from "lucide-react";

export function Header() {
  return (
    <header className="h-16 bg-white border-b border-gray-200 flex items-center justify-between px-6">
      <div />
      <div className="flex items-center gap-4">
        {/* Sesli CRM — Speech-to-Text */}
        <button
          className="flex items-center gap-2 px-3 py-1.5 bg-blue-50 text-blue-700 rounded-full text-sm font-medium hover:bg-blue-100 transition-colors"
          title="Sesli not bırak"
        >
          <Mic className="w-4 h-4" />
          Sesli Not
        </button>

        {/* Bildirimler */}
        <button className="relative p-2 text-gray-500 hover:text-gray-700">
          <Bell className="w-5 h-5" />
          <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full" />
        </button>

        {/* Kullanıcı */}
        <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center text-white text-sm font-bold">
          B
        </div>
      </div>
    </header>
  );
}
