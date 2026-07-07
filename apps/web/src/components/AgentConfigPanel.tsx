"use client";

import { useEffect, useMemo, useState } from "react";
import { Save, Settings } from "lucide-react";
import { SafeDrawer } from "@/components/ui/SafeDrawer";
import { useAgentConfigs } from "@/hooks/useAgentConfigs";
import { useAgentConnectors } from "@/hooks/useAgentConnectors";
import { updateAgentConfig, type AgentConfig, type AgentConnector } from "@/lib/api";
import { sanitizeAgentConfigs } from "@/lib/safeFallbacks";

const splitList = (value: string) => value.split(",").map((item) => item.trim()).filter(Boolean);

export function AgentConfigPanel({ open, onClose, onSaved }: { open: boolean; onClose: () => void; onSaved?: (configs: AgentConfig[]) => void }) {
  const [configs, setConfigs] = useState<AgentConfig[]>([]); const [connectors, setConnectors] = useState<AgentConnector[]>([]);
  const [selectedType, setSelectedType] = useState(""); const [draft, setDraft] = useState<AgentConfig | null>(null);
  const [notice, setNotice] = useState(""); const [error, setError] = useState(""); const [isLoading, setIsLoading] = useState(false); const [isSaving, setIsSaving] = useState(false);

  const { data: configData, error: configError, isLoading: configsLoading, mutate: mutateConfigs } = useAgentConfigs(open);
  const { data: connectorData, mutate: mutateConnectors } = useAgentConnectors(open);

  useEffect(() => {
    if (!open) return;
    setNotice("");
    setConnectors(Array.isArray(connectorData?.items) ? connectorData.items : []);
    const normalized = sanitizeAgentConfigs(configError ? null : configData);
    setConfigs(normalized.configs);
    setIsLoading(configsLoading);
    setError(normalized.usedFallback || configError ? "后端智能体配置异常，当前已切换为前端安全默认配置。" : "");
    const current = normalized.configs.find((item) => item.agent_type === selectedType) || normalized.configs[0];
    if (current) { setSelectedType(current.agent_type); setDraft(current); }
  }, [open, configData, connectorData, configError, configsLoading]);

  const selectedConfig = useMemo(() => configs.find((item) => item.agent_type === selectedType), [configs, selectedType]);
  useEffect(() => { if (selectedConfig) setDraft(selectedConfig); }, [selectedConfig]);

  const saveDraft = async () => {
    if (!draft) return;
    setIsSaving(true); setError(""); setNotice("");
    try {
      const updated = await updateAgentConfig(draft.agent_type, { enabled: draft.enabled, workflow: draft.workflow, session_id: draft.session_id, accepted_inputs: draft.accepted_inputs, default_skill_ids: draft.default_skill_ids, output_types: draft.output_types, default_options: draft.default_options, connector_id: draft.connector_id || null });
      const next = configs.map((item) => item.agent_type === updated.agent_type ? updated : item); setConfigs(next); setDraft(updated); setNotice("配置已保存。"); await mutateConfigs(); await mutateConnectors(); onSaved?.(next);
    } catch (err) { setError(err instanceof Error ? err.message : "配置保存失败。"); }
    finally { setIsSaving(false); }
  };

  const sidebar = <><div className="shrink-0 border-b p-4"><div className="flex items-center gap-2"><Settings className="h-5 w-5 text-violet-600" /><h3 className="font-bold">智能体列表</h3></div></div><div className="min-h-0 flex-1 space-y-2 overflow-y-auto overscroll-contain p-4">{isLoading ? <p className="text-sm text-slate-500">正在加载配置...</p> : configs.map((config) => <button className={`w-full rounded-xl px-3 py-3 text-left ${selectedType === config.agent_type ? "bg-violet-100 text-violet-700" : "hover:bg-white"}`} key={config.agent_type} onClick={() => setSelectedType(config.agent_type)} type="button"><p className="text-sm font-semibold">{config.name || config.agent_type}</p><p className="mt-1 truncate font-mono text-xs text-slate-400">{config.agent_type}</p><div className="mt-2 flex gap-1"><span className={`rounded-full px-2 py-0.5 text-[11px] ${config.enabled ? "bg-emerald-50 text-emerald-600" : "bg-rose-50 text-rose-600"}`}>{config.enabled ? "已启用" : "未启用"}</span><span className="rounded-full bg-slate-100 px-2 py-0.5 text-[11px] text-slate-500">{config.session_id ? "已绑定" : "未绑定"}</span></div></button>)}</div></>;
  const footer = <div className="flex items-center justify-between gap-3"><div>{error ? <p className="text-sm text-rose-600">{error}</p> : notice ? <p className="text-sm text-emerald-600">{notice}</p> : null}</div><button className="inline-flex shrink-0 items-center gap-2 rounded-xl bg-violet-600 px-5 py-2.5 text-sm font-semibold text-white disabled:opacity-50" disabled={isSaving || !draft} onClick={() => void saveDraft()} type="button"><Save className="h-4 w-4" />{isSaving ? "保存中..." : "保存配置"}</button></div>;

  return <SafeDrawer open={open} title={draft?.name || "智能体设置"} eyebrow={draft?.agent_type || "meizhaiseek v1.8"} onClose={onClose} sidebar={sidebar} footer={footer}>
    {draft ? <div className="mx-auto max-w-3xl space-y-5"><div><h3 className="text-2xl font-bold">{draft.name || draft.agent_type}</h3><p className="mt-2 text-sm leading-6 text-slate-500">{draft.description || "配置该智能体的运行方式、输入和输出。"}</p></div><div className="space-y-5 rounded-2xl border bg-slate-50/60 p-5"><label className="flex items-center gap-2 text-sm font-medium"><input checked={draft.enabled} onChange={(e) => setDraft({ ...draft, enabled: e.target.checked })} type="checkbox" />启用该智能体</label><Field label="workflow" value={draft.workflow} onChange={(value) => setDraft({ ...draft, workflow: value })} /><Field label="session_id" value={draft.session_id || ""} onChange={(value) => setDraft({ ...draft, session_id: value })} /><label className="block text-sm font-medium">绑定本地 Agent 连接器<select className="mt-2 w-full rounded-xl border bg-white px-3 py-2" value={draft.connector_id || ""} onChange={(e) => setDraft({ ...draft, connector_id: e.target.value || null })}><option value="">未绑定（使用环境变量）</option>{connectors.map((connector) => <option key={connector.connector_id} value={connector.connector_id}>{connector.name} / {connector.connector_id} / {connector.mode} / {connector.enabled ? "启用" : "禁用"}</option>)}</select></label>{draft.connector_id && !connectors.some((item) => item.connector_id === draft.connector_id) ? <p className="rounded-xl bg-rose-50 p-3 text-sm text-rose-700">当前绑定的连接器不存在。</p> : null}{draft.connector_id && connectors.some((item) => item.connector_id === draft.connector_id && !item.enabled) ? <p className="rounded-xl bg-amber-50 p-3 text-sm text-amber-700">当前绑定的连接器已禁用。</p> : null}<Field label="accepted_inputs（逗号分隔）" value={(draft.accepted_inputs || []).join(", ")} onChange={(value) => setDraft({ ...draft, accepted_inputs: splitList(value) })} /><Field label="default_skill_ids（逗号分隔）" value={(draft.default_skill_ids || []).join(", ")} onChange={(value) => setDraft({ ...draft, default_skill_ids: splitList(value) })} /><Field label="output_types（逗号分隔）" value={(draft.output_types || []).join(", ")} onChange={(value) => setDraft({ ...draft, output_types: splitList(value) })} />{draft.agent_type === "video_script_breakdown" ? <p className="rounded-xl bg-violet-50 p-3 text-sm text-violet-700">视频脚本拆解固定 session_id：019dd824-f4bb-7273-8ac3-6e19b195ff82</p> : null}</div></div> : <p className="text-sm text-slate-500">请选择智能体配置。</p>}
  </SafeDrawer>;
}

function Field({ label, value, onChange }: { label: string; value: string; onChange: (value: string) => void }) { return <label className="block text-sm font-medium">{label}<input className="mt-2 w-full rounded-xl border bg-white px-3 py-2 outline-none focus:ring-2 focus:ring-violet-200" value={value} onChange={(e) => onChange(e.target.value)} /></label>; }


