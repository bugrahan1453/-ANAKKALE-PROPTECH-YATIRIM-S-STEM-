import { cn } from "@/lib/utils";

interface StatsCardProps {
  title: string;
  value: string | number;
  trend?: string;
  color?: "default" | "green" | "red" | "yellow";
}

export function StatsCard({ title, value, trend, color = "default" }: StatsCardProps) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5">
      <p className="text-sm text-gray-500">{title}</p>
      <p className={cn(
        "text-3xl font-bold mt-1",
        color === "green" && "text-green-600",
        color === "red" && "text-red-600",
        color === "yellow" && "text-yellow-600",
        color === "default" && "text-gray-900",
      )}>
        {value}
      </p>
      {trend && (
        <p className="text-xs text-green-600 mt-1 font-medium">{trend} bu hafta</p>
      )}
    </div>
  );
}
