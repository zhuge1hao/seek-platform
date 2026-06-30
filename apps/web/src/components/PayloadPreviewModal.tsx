"use client";

import { Clipboard } from "lucide-react";
import { SafeScrollableModal } from "@/components/ui/SafeScrollableModal";

export function PayloadPreviewModal({ payload, connectorId, error, onClose, onCopied }: { payload: Record<string, unknown> | null; connectorId?: string | null; error?: string; onClose: () => void; onCopied?: () => void }) {
  const copy = async () => { if (!payload) return; await navigator.clipboard.writeText(JSON.stringify(payload, null, 2)); onCopied?.(); };
  return <SafeScrollableModal open title="Payload 预览" onClose={onClose} maxWidth="max-w-3xl" footer={<div className="flex justify-end"><button className="inline-flex items-center gap-2 rounded-xl bg-violet-600 px-4 py-2 text-sm font-semibold text-white disabled:opacity-50" disabled={!payload} onClick={() => void copy()} type="button"><Clipboard className="h-4 w-4" />复制 Payload</button></div>}><p className="text-xs text-slate-500">连接器：{connectorId || "环境变量默认配置"}</p>{error ? <p className="mt-4 rounded-xl bg-rose-50 p-3 text-sm text-rose-700">{error}</p> : null}{payload ? <pre className="mt-4 max-h-[420px] overflow-auto whitespace-pre-wrap break-words rounded-xl bg-slate-950 p-4 text-xs text-slate-100">{JSON.stringify(payload, null, 2)}</pre> : null}</SafeScrollableModal>;
}
