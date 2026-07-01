"use client";

import { useState } from "react";
import { Clipboard, Play } from "lucide-react";
import { EmptyState } from "@/components/ui/EmptyState";
import { ErrorState } from "@/components/ui/ErrorState";
import { LoadingState } from "@/components/ui/LoadingState";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { useDebugPayloads } from "@/hooks/useDebugPayloads";
import { getDebugPayload, replayDebugPayload, type DebugPayloadDetail } from "@/lib/api";

export function DebugPayloadPanel() {
  const [agentType, setAgentType] = useState("");
  const [status, setStatus] = useState("");
  const filters = { limit: 50, agent_type: agentType || undefined, status: status || undefined };
  const { data, error: loadError, isLoading, mutate } = useDebugPayloads(filters);
  const items = data?.items || [];
  const [selected, setSelected] = useState<DebugPayloadDetail | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [replay, setReplay] = useState<unknown>(null);

  const load = async () => { setError(""); await mutate(); };
  const open = async (runId: string) => {
    setBusy(true); setError("");
    try { setSelected(await getDebugPayload(runId)); setReplay(null); }
    catch (err) { setError(err instanceof Error ? err.message : "联调详情读取失败。"); }
    finally { setBusy(false); }
  };
  const copy = async (value: unknown, label: string) => {
    await navigator.clipboard.writeText(typeof value === "string" ? value : JSON.stringify(value, null, 2));
    setNotice(`${label} 已复制。`);
  };
  const runReplay = async () => {
    if (!selected) return;
    setBusy(true); setError("");
    try { const result = await replayDebugPayload(selected.run_id); setReplay(result.replay_result); }
    catch (err) { setError(err instanceof Error ? err.message : "重放失败。"); }
    finally { setBusy(false); }
  };

  if (isLoading) return <LoadingState label="正在加载联调记录..." />;

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-2">
        <input className="rounded-xl border px-3 py-2 text-sm" placeholder="agent_type" value={agentType} onChange={(e) => setAgentType(e.target.value)} />
        <select className="rounded-xl border px-3 py-2 text-sm" value={status} onChange={(e) => setStatus(e.target.value)}><option value="">全部状态</option><option value="success">success</option><option value="failed">failed</option><option value="running">running</option></select>
        <button className="rounded-xl bg-slate-950 px-4 py-2 text-sm text-white" onClick={() => void load()} type="button">筛选</button>
      </div>
      {(error || loadError) ? <ErrorState message={error || (loadError instanceof Error ? loadError.message : "联调记录读取失败。")} onRetry={() => void load()} /> : null}
      {notice ? <p className="rounded-xl bg-emerald-50 px-4 py-2 text-sm text-emerald-700">{notice}</p> : null}
      {!items.length ? <EmptyState title="暂无联调记录" /> : (
        <div className="grid min-h-[460px] gap-4 lg:grid-cols-[280px_minmax(0,1fr)]">
          <div className="max-h-[65vh] space-y-2 overflow-y-auto pr-1">
            {items.map((item) => <button className="w-full rounded-xl border p-3 text-left hover:border-violet-200" key={item.run_id} onClick={() => void open(item.run_id)} type="button"><div className="flex items-center justify-between gap-2"><span className="truncate font-mono text-xs">{item.run_id}</span><StatusBadge status={item.status} /></div><p className="mt-2 text-xs text-slate-500">{item.agent_type || "unknown"} / {item.connector_id || "env"}</p><p className="mt-1 text-[11px] text-slate-400">{item.created_at}</p></button>)}
          </div>
          <div className="min-w-0 rounded-2xl border border-slate-100 p-4">
            {busy && !selected ? <LoadingState label="正在读取详情..." /> : selected ? <div className="space-y-4"><div className="flex flex-wrap gap-2"><button className="rounded-lg border px-3 py-1.5 text-xs" onClick={() => void copy(selected.request, "request")} type="button"><Clipboard className="mr-1 inline h-3 w-3" />复制 request</button><button className="rounded-lg border px-3 py-1.5 text-xs" onClick={() => void copy(selected.response, "response")} type="button"><Clipboard className="mr-1 inline h-3 w-3" />复制 response</button><button className="rounded-lg bg-violet-600 px-3 py-1.5 text-xs text-white disabled:opacity-50" disabled={busy} onClick={() => void runReplay()} type="button"><Play className="mr-1 inline h-3 w-3" />{busy ? "重放中" : "重放"}</button></div><Code title="request.json" value={selected.request} /><Code title="response.json" value={selected.response} /><Code title="error.txt" value={selected.error} />{replay ? <Code title="replay_result" value={replay} /> : null}</div> : <EmptyState title="请选择一条联调记录" />}
          </div>
        </div>
      )}
    </div>
  );
}

function Code({ title, value }: { title: string; value: unknown }) {
  if (value == null || value === "") return null;
  return <section><p className="mb-2 text-xs font-semibold text-slate-500">{title}</p><pre className="max-h-56 max-w-full overflow-auto whitespace-pre-wrap break-all rounded-xl bg-slate-950 p-3 text-xs text-slate-100">{typeof value === "string" ? value : JSON.stringify(value, null, 2)}</pre></section>;
}
