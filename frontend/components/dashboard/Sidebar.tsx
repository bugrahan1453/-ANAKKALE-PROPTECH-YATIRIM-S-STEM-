"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Home, Building2, Users, CheckSquare, TrendingUp,
  Radar, FileText, Map, Trophy, LogOut
} from "lucide-react";
import { cn } from "@/lib/utils";

const navItems = [
  { href: "/", icon: Home, label: "Komuta Merkezi" },
  { href: "/listings", icon: Building2, label: "İlanlar" },
  { href: "/radar", icon: Radar, label: "Yatırım Radarı", brokerOnly: true },
  { href: "/crm", icon: Users, label: "CRM / Müşteriler" },
  { href: "/tasks", icon: CheckSquare, label: "Görevler" },
  { href: "/valuation", icon: TrendingUp, label: "Değerleme" },
  { href: "/map", icon: Map, label: "Harita" },
  { href: "/reports", icon: FileText, label: "Raporlar" },
  { href: "/leaderboard", icon: Trophy, label: "Leaderboard" },
];

export function Sidebar() {
  const pathname = usePathname();
  return (
    <aside className="w-64 bg-slate-900 text-white flex flex-col">
      <div className="p-6 border-b border-slate-700">
        <h1 className="text-lg font-bold text-blue-400">PropTech</h1>
        <p className="text-xs text-slate-400 mt-1">Çanakkale Yatırım Sistemi</p>
      </div>

      <nav className="flex-1 p-4 space-y-1">
        {navItems.map(({ href, icon: Icon, label }) => (
          <Link
            key={href}
            href={href}
            className={cn(
              "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors",
              pathname === href
                ? "bg-blue-600 text-white"
                : "text-slate-300 hover:bg-slate-800 hover:text-white"
            )}
          >
            <Icon className="w-4 h-4" />
            {label}
          </Link>
        ))}
      </nav>

      <div className="p-4 border-t border-slate-700">
        <button className="flex items-center gap-3 w-full px-3 py-2 text-sm text-slate-400 hover:text-white rounded-lg hover:bg-slate-800">
          <LogOut className="w-4 h-4" />
          Çıkış Yap
        </button>
      </div>
    </aside>
  );
}
