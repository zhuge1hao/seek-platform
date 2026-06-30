"use client";

import type { ReactNode } from "react";
import { useEffect } from "react";
import { X } from "lucide-react";

export function SafeScrollableModal({ open, title, onClose, children, footer, maxWidth = "max-w-2xl", zIndex = "z-[200]" }: { open: boolean; title: string; onClose: () => void; children: ReactNode; footer?: ReactNode; maxWidth?: string; zIndex?: string }) {
  useEffect(() => {
    if (!open) return;
    const previous = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => { document.body.style.overflow = previous; };
  }, [open]);
  if (!open) return null;
  return <div className={`fixed inset-0 ${zIndex} flex items-center justify-center overflow-hidden bg-slate-950/35 p-4`} role="dialog" aria-modal="true"><div className={`flex max-h-[calc(100vh-48px)] w-full ${maxWidth} flex-col overflow-hidden rounded-2xl bg-white shadow-2xl`}><header className="flex shrink-0 items-center justify-between border-b px-5 py-4"><h3 className="font-bold text-slate-950">{title}</h3><button aria-label="关闭" className="rounded-full p-2 text-slate-400 hover:bg-slate-100" onClick={onClose} type="button"><X className="h-5 w-5" /></button></header><div className="min-h-0 flex-1 overflow-y-auto overscroll-contain p-5">{children}</div>{footer ? <footer className="shrink-0 border-t bg-white px-5 py-4">{footer}</footer> : null}</div></div>;
}
