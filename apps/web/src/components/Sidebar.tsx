"use client";

import { Bot, Brush, ChartNoAxesCombined, CircleGauge, LogOut, MessageSquareText, PenTool, Sparkles } from "lucide-react";
import { useRouter } from "next/navigation";
import { logout } from "@/lib/auth";
import { navigationItems } from "@/lib/navigation";

const icons = [
  MessageSquareText,
  Bot,
  PenTool,
  Brush,
  ChartNoAxesCombined,
  CircleGauge,
  Sparkles
];

export function Sidebar() {
  const router = useRouter();

  const handleLogout = async () => {
    try {
      await logout();
    } finally {
      router.replace("/login");
    }
  };

  return (
    <aside className="flex h-screen w-[220px] shrink-0 flex-col border-r border-slate-200/70 bg-white px-4 py-5">
      <div className="mb-8 flex items-center gap-2 px-2">
        <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-violet-500 to-rose-400 text-sm font-bold text-white shadow-soft">
          M
        </div>
        <div className="text-lg font-semibold tracking-tight text-slate-950">meizhaiseek</div>
      </div>

      <nav className="space-y-1">
        {navigationItems.map((item, index) => {
          const Icon = icons[index];
          const active = item.id === "agent";

          return (
            <button
              key={item.id}
              className={[
                "flex h-11 w-full items-center gap-3 rounded-xl px-3 text-left text-sm font-medium transition",
                active
                  ? "bg-violet-50 text-violet-700 shadow-sm"
                  : "text-slate-600 hover:bg-slate-50 hover:text-slate-950",
                item.enabled ? "" : "cursor-not-allowed opacity-70"
              ].join(" ")}
              type="button"
            >
              <Icon className="h-4 w-4" />
              {item.label}
            </button>
          );
        })}
      </nav>

      <button className="mt-auto flex h-11 w-full items-center gap-3 rounded-xl px-3 text-left text-sm font-medium text-slate-600 transition hover:bg-slate-50 hover:text-slate-950" onClick={handleLogout} type="button">
        <LogOut className="h-4 w-4" />
        退出登录
      </button>
    </aside>
  );
}
