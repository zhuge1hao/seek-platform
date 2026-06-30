"use client";

import type { ReactNode } from "react";
import { useEffect } from "react";
import { X } from "lucide-react";

export function SafeDrawer({ open, title, eyebrow, onClose, sidebar, children, footer, maxWidth = "max-w-5xl", zIndex = "z-[140]" }: { open: boolean; title: string; eyebrow?: string; onClose: () => void; sidebar?: ReactNode; children: ReactNode; footer?: ReactNode; maxWidth?: string; zIndex?: string }) {
  useEffect(() => {
    if (!open) return;
    const previous = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => { document.body.style.overflow = previous; };
  }, [open]);
  if (!open) return null;
  return (
    <div className={`fixed inset-0 ${zIndex} overflow-hidden bg-slate-950/35 backdrop-blur-sm`} role="dialog" aria-modal="true">
      <div className={`absolute inset-y-0 right-0 flex h-full max-h-screen w-full ${maxWidth} overflow-hidden bg-white shadow-2xl`}>
        {sidebar ? <aside className="flex min-h-0 w-40 shrink-0 flex-col overflow-hidden border-r border-slate-100 bg-slate-50 sm:w-56">{sidebar}</aside> : null}
        <section className="flex min-h-0 min-w-0 flex-1 flex-col overflow-hidden">
          <header className="flex shrink-0 items-center justify-between border-b border-slate-100 px-5 py-4 sm:px-6">
            <div className="min-w-0">{eyebrow ? <p className="text-xs font-semibold text-violet-700">{eyebrow}</p> : null}<h2 className="truncate text-xl font-bold text-slate-950">{title}</h2></div>
            <button aria-label="关闭" className="shrink-0 rounded-full p-2 text-slate-400 hover:bg-slate-100 hover:text-slate-700" onClick={onClose} type="button"><X className="h-5 w-5" /></button>
          </header>
          <div className="min-h-0 flex-1 overflow-y-auto overscroll-contain px-5 py-5 sm:px-6">{children}</div>
          {footer ? <footer className="shrink-0 border-t border-slate-100 bg-white px-5 py-4 sm:px-6">{footer}</footer> : null}
        </section>
      </div>
    </div>
  );
}
