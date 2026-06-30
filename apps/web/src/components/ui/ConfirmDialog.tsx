"use client";

import { SafeScrollableModal } from "@/components/ui/SafeScrollableModal";

export function ConfirmDialog({ open, title, message, confirmLabel = "确认", danger = false, busy = false, onCancel, onConfirm }: { open: boolean; title: string; message: string; confirmLabel?: string; danger?: boolean; busy?: boolean; onCancel: () => void; onConfirm: () => void }) {
  return <SafeScrollableModal open={open} title={title} onClose={onCancel} maxWidth="max-w-md" zIndex="z-[230]" footer={<div className="flex justify-end gap-2"><button className="rounded-xl border px-4 py-2 text-sm" disabled={busy} onClick={onCancel} type="button">取消</button><button className={`rounded-xl px-4 py-2 text-sm font-semibold text-white disabled:opacity-50 ${danger ? "bg-rose-600" : "bg-violet-600"}`} disabled={busy} onClick={onConfirm} type="button">{busy ? "处理中..." : confirmLabel}</button></div>}><p className="text-sm leading-6 text-slate-600">{message}</p></SafeScrollableModal>;
}
