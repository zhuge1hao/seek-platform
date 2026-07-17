"use client";

import type { ReactNode } from "react";
import { useEffect, useState } from "react";
import { Activity, RefreshCw, ShieldCheck, Trash2 } from "lucide-react";
import { SafeDrawer } from "@/components/ui/SafeDrawer";
import {
  backupRuntimeConfigs,
  clearRuntimeCache,
  getRuntimeConfigsStatus,
  repairRuntimeConfigs,
  resetRuntimeConfigs,
  type RuntimeConfigsStatusResponse,
  type RuntimeHealthResponse
} from "@/lib/api";
import { useRuntimeHealth } from "@/hooks/useRuntimeHealth";
import { useStorageHealth } from "@/hooks/useStorageHealth";

type RuntimeHealthPanelProps = {
  open: boolean;
  onClose: () => void;
  onChanged?: () => void;
};

export function RuntimeHealthPanel({ open, onClose, onChanged }: RuntimeHealthPanelProps) {
  const [health, setHealth] = useState<RuntimeHealthResponse | null>(null);
  const [configs, setConfigs] = useState<RuntimeConfigsStatusResponse | null>(null);
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const { data: healthData, error: healthLoadError, mutate: mutateRuntimeHealth } = useRuntimeHealth(open);
  const { data: storageHealth, mutate: mutateStorageHealth } = useStorageHealth(open);

  const refresh = async () => {
    setLoading(true);
    setError("");
    try {
      const [nextHealth, nextConfigs] = await Promise.all([mutateRuntimeHealth(), getRuntimeConfigsStatus(), mutateStorageHealth()]);
      if (nextHealth) setHealth(nextHealth);
      setConfigs(nextConfigs);
    } catch (err) {
      setError(err instanceof Error ? err.message : "后台状态读取失败。");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { if (healthData) setHealth(healthData); }, [healthData]);
  useEffect(() => { if (healthLoadError) setError(healthLoadError instanceof Error ? healthLoadError.message : "后台状态读取失败。"); }, [healthLoadError]);
  useEffect(() => { if (open) refresh(); }, [open]);

  const runAction = async (label: string, action: () => Promise<unknown>, confirmMessage?: string) => {
    if (confirmMessage && !window.confirm(confirmMessage)) return;
    setLoading(true);
    setNotice("");
    setError("");
    try {
      await action();
      setNotice(`${label}完成。`);
      onChanged?.();
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : `${label}失败。`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <SafeDrawer open={open} title="后台状态" eyebrow="meizhaiseek v1.8.5" onClose={onClose} maxWidth="max-w-3xl">
        <div className="mb-5 flex items-center gap-2"><Activity className="h-5 w-5 text-violet-600" /><p className="text-sm text-slate-500">运行时配置与缓存健康检查</p></div>

        <div className="rounded-[24px] border border-slate-100 bg-slate-50 p-5">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <p className="text-sm font-semibold text-violet-700">meizhaiseek v1.8.5</p>
              <h4 className="mt-1 text-2xl font-bold text-slate-950">{health?.service || "meizhaiseek-api"}</h4>
              <p className="mt-2 text-sm text-slate-500">运行时配置、缓存、任务状态和 debug payload 自检。</p>
            </div>
            <span className={["rounded-full px-3 py-1 text-sm font-semibold", health?.status === "ok" ? "bg-emerald-50 text-emerald-600" : "bg-amber-50 text-amber-700"].join(" ")}>
              {health?.status || "loading"}
            </span>
          </div>
          {health?.warnings?.length ? (
            <div className="mt-4 rounded-2xl bg-amber-50 p-3 text-sm text-amber-700">
              {health.warnings.map((warning) => <p key={warning}>{warning}</p>)}
            </div>
          ) : null}
          {storageHealth ? <p className="mt-3 text-xs text-slate-500">APP SQLite：{storageHealth.status}{storageHealth.tables ? ` · ${Object.keys(storageHealth.tables).length} tables` : ""}</p> : null}
        </div>

        <div className="mt-5 grid gap-3">
          {configs?.configs.map((item) => (
            <div className="rounded-2xl border border-slate-100 bg-white p-4 shadow-sm" key={item.name}>
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-semibold text-slate-950">{item.name}</p>
                  <p className="mt-1 break-all text-xs text-slate-400">{item.path}</p>
                </div>
                <span className="rounded-full bg-violet-50 px-3 py-1 text-xs font-semibold text-violet-700">{item.count} 条</span>
              </div>
              {item.warnings.length ? <p className="mt-2 text-sm text-amber-700">{item.warnings.join("；")}</p> : <p className="mt-2 text-sm text-emerald-600">配置正常</p>}
            </div>
          ))}
        </div>

        {error ? <p className="mt-4 rounded-xl bg-rose-50 px-4 py-3 text-sm text-rose-600">{error}</p> : null}
        {notice ? <p className="mt-4 rounded-xl bg-emerald-50 px-4 py-3 text-sm text-emerald-600">{notice}</p> : null}

        <div className="mt-6 flex flex-wrap gap-3">
          <ActionButton disabled={loading} icon={<RefreshCw className="h-4 w-4" />} label="刷新状态" onClick={refresh} />
          <ActionButton disabled={loading} icon={<ShieldCheck className="h-4 w-4" />} label="备份配置" onClick={() => runAction("备份配置", backupRuntimeConfigs)} />
          <ActionButton disabled={loading} icon={<ShieldCheck className="h-4 w-4" />} label="修复配置" onClick={() => runAction("修复配置", repairRuntimeConfigs)} />
          <ActionButton disabled={loading} icon={<Trash2 className="h-4 w-4" />} label="重置配置" onClick={() => runAction("重置配置", resetRuntimeConfigs, "确定要重置运行时配置吗？当前配置会先备份。")} />
          <ActionButton disabled={loading} icon={<Trash2 className="h-4 w-4" />} label="清理缓存" onClick={() => runAction("清理缓存", clearRuntimeCache)} />
        </div>
    </SafeDrawer>
  );
}

function ActionButton({ disabled, icon, label, onClick }: { disabled: boolean; icon: ReactNode; label: string; onClick: () => void }) {
  return (
    <button className="inline-flex items-center gap-2 rounded-2xl border border-violet-200 bg-white px-4 py-2 text-sm font-semibold text-violet-700 transition hover:bg-violet-50 disabled:opacity-60" disabled={disabled} onClick={onClick} type="button">
      {icon}
      {label}
    </button>
  );
}


