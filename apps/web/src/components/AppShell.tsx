"use client";

import { ReactNode, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import { Bot, Brush, ChartNoAxesCombined, CircleGauge, Headphones, LogOut, MessageSquareText, PenTool, Sparkles } from "lucide-react";
import { AuthGuard } from "@/components/AuthGuard";
import { logout } from "@/lib/auth";
import { navigationItems, type NavigationItemId } from "@/lib/navigation";

const iconMap: Record<NavigationItemId, typeof MessageSquareText> = {
  chat: MessageSquareText,
  agent: Bot,
  "ai-creation": PenTool,
  board: Brush,
  "competition-diagnosis": ChartNoAxesCombined,
  bi: CircleGauge,
  shrimp: Sparkles
};

type AppShellProps = {
  children: ReactNode;
  activeId?: NavigationItemId;
  dark?: boolean;
  contentClassName?: string;
};

export function AppShell({ children, activeId, dark = false, contentClassName = "" }: AppShellProps) {
  const router = useRouter();
  const pathname = usePathname();
  const [notice, setNotice] = useState("");

  const resolvedActiveId = activeId ?? navigationItems.find((item) => item.enabled && item.path && pathname.startsWith(item.path))?.id ?? "agent";

  const handleNavigate = (item: (typeof navigationItems)[number]) => {
    if (!item.enabled) {
      setNotice("该功能正在建设中。");
      window.setTimeout(() => setNotice(""), 2200);
      return;
    }
    router.push(item.path);
  };

  const handleLogout = async () => {
    try {
      await logout();
    } finally {
      router.replace("/login");
    }
  };

  return (
    <AuthGuard>
      <main className={["flex min-h-screen overflow-hidden", dark ? "bg-[#121212]" : "bg-slate-100"].join(" ")}>
        <aside className={["m-3 flex h-[calc(100vh-24px)] w-[220px] shrink-0 flex-col rounded-[24px] px-4 py-5 shadow-sm", dark ? "border border-white/10 bg-[#232323] text-white" : "border border-white bg-white text-slate-950"].join(" ")}>
          <div className="mb-9 flex items-center gap-3 px-2">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-violet-500 to-fuchsia-400 text-sm font-bold text-white shadow-soft">M</div>
            <div className={["text-lg font-semibold tracking-tight", dark ? "text-white" : "text-slate-950"].join(" ")}>meizhaiseek</div>
          </div>

          <nav className="space-y-2">
            {navigationItems.map((item) => {
              const Icon = iconMap[item.id];
              const active = resolvedActiveId === item.id;
              return (
                <button
                  className={[
                    "flex h-12 w-full items-center gap-3 rounded-2xl px-3 text-left text-sm font-semibold transition",
                    active ? (dark ? "bg-violet-700/55 text-violet-100" : "bg-violet-50 text-violet-700 shadow-sm") : dark ? "text-slate-400 hover:bg-white/5 hover:text-white" : "text-slate-600 hover:bg-slate-50 hover:text-slate-950",
                    item.enabled ? "" : "cursor-not-allowed opacity-70"
                  ].join(" ")}
                  key={item.id}
                  onClick={() => handleNavigate(item)}
                  type="button"
                >
                  <Icon className="h-5 w-5 shrink-0" />
                  {item.label}
                </button>
              );
            })}
          </nav>

          <div className="mt-auto">
            <button
              className={[
                "flex h-12 w-full items-center gap-3 rounded-2xl px-3 text-left text-sm font-semibold transition",
                dark ? "text-slate-400 hover:bg-white/5 hover:text-white" : "text-slate-600 hover:bg-slate-50 hover:text-slate-950"
              ].join(" ")}
              onClick={handleLogout}
              type="button"
            >
              <LogOut className="h-5 w-5 shrink-0" />
              退出登录
            </button>
          </div>
        </aside>

        <section className={["relative min-h-screen flex-1 overflow-y-auto", contentClassName].join(" ")}>
          {notice ? <div className="fixed left-1/2 top-6 z-50 -translate-x-1/2 rounded-full bg-slate-950 px-5 py-2 text-sm font-medium text-white shadow-soft">{notice}</div> : null}
          {children}
          <button aria-label="联系客服" className="fixed bottom-6 right-6 z-40 flex h-14 w-14 items-center justify-center rounded-full bg-black text-white shadow-soft transition hover:scale-105" type="button">
            <Headphones className="h-6 w-6" />
          </button>
        </section>
      </main>
    </AuthGuard>
  );
}
