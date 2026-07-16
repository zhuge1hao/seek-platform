"use client";

import type { ReactNode } from "react";
import { useCallback, useEffect, useState } from "react";
import { Activity, Cable, Download, FileClock, KeyRound, Settings, ShieldCheck, TerminalSquare, Trash2, Users } from "lucide-react";
import { useRouter } from "next/navigation";
import { AgentBlueprintPanel } from "@/components/AgentBlueprintPanel";
import { AgentConnectorPanel } from "@/components/AgentConnectorPanel";
import { DebugPayloadPanel } from "@/components/DebugPayloadPanel";
import { UserManagementPanel } from "@/components/UserManagementPanel";
import { ConfirmDialog } from "@/components/ui/ConfirmDialog";
import { EmptyState } from "@/components/ui/EmptyState";
import { ErrorState } from "@/components/ui/ErrorState";
import { LoadingState } from "@/components/ui/LoadingState";
import { SafeDrawer } from "@/components/ui/SafeDrawer";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { backupRuntimeConfigs, changePassword, clearRuntimeCache, exportAuditLogs, getAuditLogs, getCurrentUser, getRuntimeConfigsStatus, getRuntimeHealth, repairRuntimeConfigs, resetRuntimeConfigs, type AuditLog, type RuntimeConfigsStatusResponse, type RuntimeHealthResponse } from "@/lib/api";
import { clearAuthSession, type AuthUser } from "@/lib/auth";

type TabId = "system" | "account" | "users" | "audit" | "maintenance" | "connectors" | "blueprints" | "debug";
const tabs: Array<{ id: TabId; label: string; icon: typeof Activity }> = [
  { id: "system", label: "系统状态", icon: Activity }, { id: "account", label: "账号安全", icon: KeyRound }, { id: "users", label: "账号管理", icon: Users }, { id: "audit", label: "操作日志", icon: FileClock }, { id: "maintenance", label: "配置维护", icon: Settings }, { id: "connectors", label: "本地 Agent", icon: Cable }, { id: "blueprints", label: "智能体蓝图", icon: ShieldCheck }, { id: "debug", label: "联调记录", icon: TerminalSquare }
];

export function AdminConsolePanel({ open, onClose, onChanged }: { open: boolean; onClose: () => void; onChanged?: () => void }) {
  const router = useRouter();
  const [tab, setTab] = useState<TabId>("system");
  const [health, setHealth] = useState<RuntimeHealthResponse | null>(null);
  const [configs, setConfigs] = useState<RuntimeConfigsStatusResponse | null>(null);
  const [user, setUser] = useState<AuthUser | null>(null);
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [auditAction, setAuditAction] = useState(""); const [auditUser, setAuditUser] = useState(""); const [auditStatus, setAuditStatus] = useState("");
  const [oldPassword, setOldPassword] = useState(""); const [newPassword, setNewPassword] = useState("");
  const [loading, setLoading] = useState(false); const [error, setError] = useState(""); const [notice, setNotice] = useState("");
  const [maintenanceConfirm, setMaintenanceConfirm] = useState(false);

  const loadTab = useCallback(async () => {
    if (!open) return;
    setLoading(true); setError("");
    try {
      if (tab === "system") { const [nextHealth, nextConfigs] = await Promise.all([getRuntimeHealth(), getRuntimeConfigsStatus()]); setHealth(nextHealth); setConfigs(nextConfigs); }
      else if (tab === "account") setUser(await getCurrentUser());
      else if (tab === "audit") { const result = await getAuditLogs({ action: auditAction || undefined, user: auditUser || undefined, status: auditStatus || undefined, limit: 100 }); setLogs(Array.isArray(result.logs) ? result.logs : []); }
    } catch (err) { setError(err instanceof Error ? err.message : "后台数据读取失败。"); }
    finally { setLoading(false); }
  }, [auditAction, auditStatus, auditUser, open, tab]);
  useEffect(() => { void loadTab(); }, [loadTab]);

  const runMaintenance = async (label: string, action: () => Promise<unknown>) => { setLoading(true); setError(""); setNotice(""); try { await action(); setNotice(`${label}完成。`); onChanged?.(); } catch (err) { setError(err instanceof Error ? err.message : `${label}失败。`); } finally { setLoading(false); } };
  const submitPassword = async () => { if (!oldPassword || newPassword.length < 8) return setError("请输入原密码，新密码至少 8 位。"); setLoading(true); setError(""); try { await changePassword(oldPassword, newPassword); clearAuthSession(); router.replace("/login"); } catch (err) { setError(err instanceof Error ? err.message : "密码修改失败。"); } finally { setLoading(false); } };
  const exportLogs = async (format: "csv" | "jsonl") => { setLoading(true); setError(""); try { await exportAuditLogs(format, { action: auditAction || undefined, user: auditUser || undefined, status: auditStatus || undefined }); setNotice(`操作日志 ${format.toUpperCase()} 已导出。`); } catch (err) { setError(err instanceof Error ? err.message : "操作日志导出失败。"); } finally { setLoading(false); } };

  const sidebar = <><div className="shrink-0 p-4"><p className="text-xs font-semibold text-violet-700">meizhaiseek v1.8.4</p><h2 className="mt-1 text-lg font-bold">后台管理</h2></div><nav className="min-h-0 flex-1 space-y-2 overflow-y-auto overscroll-contain px-4 pb-4">{tabs.map((item) => { const Icon = item.icon; return <button className={`flex w-full items-center gap-2 rounded-xl px-3 py-2.5 text-sm font-semibold ${tab === item.id ? "bg-violet-100 text-violet-700" : "text-slate-600 hover:bg-white"}`} key={item.id} onClick={() => { setTab(item.id); setNotice(""); setError(""); }} type="button"><Icon className="h-4 w-4" />{item.label}</button>; })}</nav></>;

  return <><SafeDrawer open={open} title={tabs.find((item) => item.id === tab)?.label || "后台管理"} eyebrow="meizhaiseek v1.8.4" onClose={onClose} sidebar={sidebar}>
    {loading && !["users", "connectors", "blueprints", "debug"].includes(tab) ? <LoadingState label="正在读取后台数据..." /> : null}
    {error ? <div className="mb-4"><ErrorState message={error} onRetry={() => void loadTab()} /></div> : null}
    {notice ? <p className="mb-4 rounded-xl bg-emerald-50 px-4 py-3 text-sm text-emerald-700">{notice}</p> : null}
    {!loading && tab === "system" ? <div className="space-y-4"><div className="rounded-2xl border bg-slate-50 p-5"><div className="flex items-center justify-between"><div><p className="text-sm text-slate-500">{health?.service || "meizhaiseek-api"}</p><p className="mt-1 text-2xl font-bold">运行时健康检查</p></div><StatusBadge status={health?.status || "unknown"} /></div>{health?.warnings?.length ? <div className="mt-4 rounded-xl bg-amber-50 p-3 text-sm text-amber-700">{health.warnings.join("；")}</div> : null}</div><div className="grid gap-3">{configs?.configs?.map((item) => <div className="rounded-2xl border p-4" key={item.name}><div className="flex items-center justify-between"><p className="font-semibold">{item.name}</p><StatusBadge status={item.valid ? "ok" : "failed"} /></div><p className="mt-1 break-all text-xs text-slate-400">{item.path}</p><p className="mt-2 text-sm text-slate-600">{item.count} 条记录</p></div>)}</div></div> : null}
    {!loading && tab === "account" ? <div className="max-w-xl space-y-5"><div className="rounded-2xl bg-slate-50 p-5"><p className="text-sm text-slate-500">当前账号</p><p className="mt-1 text-lg font-bold">{user?.username}</p><p className="mt-1 text-sm text-violet-700">角色：{user?.role}</p></div><Field label="原密码" type="password" value={oldPassword} onChange={setOldPassword} /><Field label="新密码" type="password" value={newPassword} onChange={setNewPassword} placeholder="至少 8 位" /><button className="rounded-xl bg-violet-600 px-4 py-2.5 text-sm font-semibold text-white disabled:opacity-50" disabled={loading} onClick={() => void submitPassword()} type="button">修改密码并重新登录</button></div> : null}
    {tab === "users" ? <UserManagementPanel /> : null}
    {!loading && tab === "audit" ? <div className="space-y-4"><div className="flex flex-wrap gap-2"><input className="min-w-40 flex-1 rounded-xl border px-3 py-2 text-sm" placeholder="action" value={auditAction} onChange={(e) => setAuditAction(e.target.value)} /><input className="min-w-40 flex-1 rounded-xl border px-3 py-2 text-sm" placeholder="用户 ID 或用户名" value={auditUser} onChange={(e) => setAuditUser(e.target.value)} /><select className="rounded-xl border px-3 py-2 text-sm" value={auditStatus} onChange={(e) => setAuditStatus(e.target.value)}><option value="">全部状态</option><option value="success">success</option><option value="failed">failed</option></select><button className="rounded-xl bg-slate-950 px-4 py-2 text-sm text-white" onClick={() => void loadTab()} type="button">查询</button><button className="inline-flex items-center gap-1 rounded-xl border px-3 py-2 text-sm" onClick={() => void exportLogs("csv")} type="button"><Download className="h-4 w-4" />CSV</button><button className="inline-flex items-center gap-1 rounded-xl border px-3 py-2 text-sm" onClick={() => void exportLogs("jsonl")} type="button"><Download className="h-4 w-4" />JSONL</button></div>{logs.length ? <div className="max-w-full overflow-x-auto rounded-2xl border"><table className="min-w-[850px] w-full text-left text-xs"><thead className="sticky top-0 bg-slate-50"><tr><th className="p-3">时间</th><th className="p-3">账号</th><th className="p-3">操作</th><th className="p-3">状态</th><th className="p-3">目标</th></tr></thead><tbody>{logs.map((log, index) => <tr className="border-t" key={`${log.time}-${index}`}><td className="whitespace-nowrap p-3">{log.time}</td><td className="p-3">{log.username || log.user_id}</td><td className="p-3 font-mono">{log.action}</td><td className="p-3"><StatusBadge status={log.status} /></td><td className="p-3">{log.target}</td></tr>)}</tbody></table></div> : <EmptyState title="暂无操作日志" />}</div> : null}
    {!loading && tab === "maintenance" ? <div className="grid gap-3 sm:grid-cols-2"><MaintenanceButton icon={<ShieldCheck className="h-5 w-5" />} title="备份配置" description="保存当前 runtime 配置快照。" onClick={() => void runMaintenance("备份配置", backupRuntimeConfigs)} /><MaintenanceButton icon={<ShieldCheck className="h-5 w-5" />} title="修复配置" description="校验并修复损坏或缺失字段。" onClick={() => void runMaintenance("修复配置", repairRuntimeConfigs)} /><MaintenanceButton icon={<Trash2 className="h-5 w-5" />} title="重置配置" description="备份后恢复默认智能体和技能配置。" onClick={() => setMaintenanceConfirm(true)} /><MaintenanceButton icon={<Trash2 className="h-5 w-5" />} title="清理缓存" description="清理文件预览等可重建缓存。" onClick={() => void runMaintenance("清理缓存", clearRuntimeCache)} /></div> : null}
    {tab === "connectors" ? <AgentConnectorPanel /> : null}{tab === "blueprints" ? <AgentBlueprintPanel /> : null}{tab === "debug" ? <DebugPayloadPanel /> : null}
  </SafeDrawer><ConfirmDialog open={maintenanceConfirm} title="重置运行时配置" message="确定重置配置吗？当前配置会先自动备份。" confirmLabel="重置配置" danger busy={loading} onCancel={() => setMaintenanceConfirm(false)} onConfirm={() => { setMaintenanceConfirm(false); void runMaintenance("重置配置", resetRuntimeConfigs); }} /></>;
}

function MaintenanceButton({ icon, title, description, onClick }: { icon: ReactNode; title: string; description: string; onClick: () => void }) { return <button className="rounded-2xl border p-5 text-left transition hover:border-violet-200 hover:bg-violet-50" onClick={onClick} type="button"><span className="text-violet-600">{icon}</span><p className="mt-3 font-semibold">{title}</p><p className="mt-1 text-sm leading-6 text-slate-500">{description}</p></button>; }
function Field({ label, value, type, placeholder, onChange }: { label: string; value: string; type: string; placeholder?: string; onChange: (value: string) => void }) { return <label className="block text-sm font-medium">{label}<input className="mt-2 w-full rounded-xl border px-3 py-2" placeholder={placeholder} type={type} value={value} onChange={(e) => onChange(e.target.value)} /></label>; }


