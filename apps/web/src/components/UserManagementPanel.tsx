"use client";

import type { ReactNode } from "react";
import { useCallback, useEffect, useState } from "react";
import { Eye, KeyRound, Pencil, Plus, Power, PowerOff } from "lucide-react";
import { ConfirmDialog } from "@/components/ui/ConfirmDialog";
import { EmptyState } from "@/components/ui/EmptyState";
import { ErrorState } from "@/components/ui/ErrorState";
import { LoadingState } from "@/components/ui/LoadingState";
import { SafeScrollableModal } from "@/components/ui/SafeScrollableModal";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { createAdminUser, getAdminUserRuns, getAdminUsers, resetAdminUserPassword, setAdminUserEnabled, updateAdminUser, type AdminUser, type AgentRunSummary } from "@/lib/api";

type EditorMode = "create" | "edit" | "password" | "runs" | null;

export function UserManagementPanel() {
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [keyword, setKeyword] = useState("");
  const [role, setRole] = useState("");
  const [enabled, setEnabled] = useState("");
  const [mode, setMode] = useState<EditorMode>(null);
  const [selected, setSelected] = useState<AdminUser | null>(null);
  const [runs, setRuns] = useState<AgentRunSummary[]>([]);
  const [form, setForm] = useState({ username: "", password: "", confirmPassword: "", role: "operator" as AdminUser["role"], enabled: true, remark: "" });
  const [confirm, setConfirm] = useState<{ user: AdminUser; enabled: boolean } | null>(null);

  const load = useCallback(async () => {
    setLoading(true); setError("");
    try {
      const result = await getAdminUsers({ keyword: keyword || undefined, role: role || undefined, enabled: enabled || undefined });
      setUsers(Array.isArray(result.users) ? result.users.filter((item) => item?.user_id && item?.username && item?.role) : []);
    } catch (err) { setError(err instanceof Error ? err.message : "用户列表读取失败。"); }
    finally { setLoading(false); }
  }, [enabled, keyword, role]);

  useEffect(() => { void load(); }, [load]);

  const openCreate = () => { setSelected(null); setForm({ username: "", password: "", confirmPassword: "", role: "operator", enabled: true, remark: "" }); setMode("create"); setError(""); };
  const openEdit = (user: AdminUser) => { setSelected(user); setForm({ username: user.username, password: "", confirmPassword: "", role: user.role, enabled: user.enabled, remark: user.remark || "" }); setMode("edit"); setError(""); };
  const openPassword = (user: AdminUser) => { setSelected(user); setForm((current) => ({ ...current, password: "", confirmPassword: "" })); setMode("password"); setError(""); };

  const save = async () => {
    setError(""); setNotice("");
    if (mode === "create" && !form.username.trim()) return setError("请输入用户名。");
    if (mode === "create" && form.password.length < 8) return setError("密码至少需要 8 位。");
    if ((mode === "create" || mode === "password") && form.password !== form.confirmPassword) return setError("两次输入的密码不一致。");
    if (mode === "password" && form.password.length < 8) return setError("新密码至少需要 8 位。");
    setBusy(true);
    try {
      if (mode === "create") {
        await createAdminUser({ username: form.username.trim(), password: form.password, role: form.role, enabled: form.enabled, remark: form.remark });
        setNotice("用户已创建。");
      } else if (mode === "edit" && selected) {
        await updateAdminUser(selected.user_id, { role: form.role, enabled: form.enabled, remark: form.remark });
        setNotice("用户信息已保存。");
      } else if (mode === "password" && selected) {
        await resetAdminUserPassword(selected.user_id, form.password);
        setNotice("密码已重置，该用户需要重新登录。");
      }
      setMode(null); await load();
    } catch (err) { setError(err instanceof Error ? err.message : "操作失败。"); }
    finally { setBusy(false); }
  };

  const toggleEnabled = async () => {
    if (!confirm) return;
    setBusy(true); setError("");
    try { await setAdminUserEnabled(confirm.user.user_id, confirm.enabled); setNotice(confirm.enabled ? "用户已启用。" : "用户已禁用。"); setConfirm(null); await load(); }
    catch (err) { setError(err instanceof Error ? err.message : "用户状态更新失败。"); setConfirm(null); }
    finally { setBusy(false); }
  };

  const openRuns = async (user: AdminUser) => {
    setSelected(user); setMode("runs"); setRuns([]); setBusy(true); setError("");
    try { const result = await getAdminUserRuns(user.user_id); setRuns(Array.isArray(result.runs) ? result.runs : []); }
    catch (err) { setError(err instanceof Error ? err.message : "用户任务读取失败。"); }
    finally { setBusy(false); }
  };

  return <div className="space-y-4">
    <div className="flex flex-wrap items-center gap-2">
      <input className="min-w-[180px] flex-1 rounded-xl border px-3 py-2 text-sm" placeholder="搜索用户名或备注" value={keyword} onChange={(e) => setKeyword(e.target.value)} />
      <select className="rounded-xl border px-3 py-2 text-sm" value={role} onChange={(e) => setRole(e.target.value)}><option value="">全部角色</option><option value="admin">admin</option><option value="operator">operator</option><option value="viewer">viewer</option></select>
      <select className="rounded-xl border px-3 py-2 text-sm" value={enabled} onChange={(e) => setEnabled(e.target.value)}><option value="">全部状态</option><option value="true">已启用</option><option value="false">已禁用</option></select>
      <button className="rounded-xl border px-4 py-2 text-sm" onClick={() => void load()} type="button">查询</button>
      <button className="inline-flex items-center gap-2 rounded-xl bg-violet-600 px-4 py-2 text-sm font-semibold text-white" onClick={openCreate} type="button"><Plus className="h-4 w-4" />新增用户</button>
    </div>
    {notice ? <p className="rounded-xl bg-emerald-50 px-4 py-3 text-sm text-emerald-700">{notice}</p> : null}
    {error && !mode ? <ErrorState message={error} onRetry={() => void load()} /> : null}
    {loading ? <LoadingState label="正在加载用户..." /> : users.length ? <div className="max-w-full overflow-x-auto rounded-2xl border"><table className="min-w-[900px] w-full text-left text-sm"><thead className="sticky top-0 bg-slate-50 text-xs text-slate-500"><tr><th className="p-3">用户名</th><th className="p-3">角色</th><th className="p-3">状态</th><th className="p-3">创建时间</th><th className="p-3">最近登录</th><th className="p-3">备注</th><th className="p-3">操作</th></tr></thead><tbody>{users.map((user) => <tr className="border-t" key={user.user_id}><td className="p-3 font-semibold">{user.username}</td><td className="p-3"><StatusBadge status={user.role} /></td><td className="p-3"><StatusBadge status={user.enabled ? "enabled" : "disabled"} /></td><td className="whitespace-nowrap p-3 text-xs">{user.created_at || "-"}</td><td className="whitespace-nowrap p-3 text-xs">{user.last_login_at || "从未登录"}</td><td className="max-w-44 truncate p-3">{user.remark || "-"}</td><td className="p-3"><div className="flex flex-wrap gap-1"><IconButton label="编辑" icon={<Pencil className="h-3 w-3" />} onClick={() => openEdit(user)} /><IconButton label={user.enabled ? "禁用" : "启用"} icon={user.enabled ? <PowerOff className="h-3 w-3" /> : <Power className="h-3 w-3" />} onClick={() => setConfirm({ user, enabled: !user.enabled })} /><IconButton label="重置密码" icon={<KeyRound className="h-3 w-3" />} onClick={() => openPassword(user)} /><IconButton label="查看任务" icon={<Eye className="h-3 w-3" />} onClick={() => void openRuns(user)} /></div></td></tr>)}</tbody></table></div> : <EmptyState title="暂无用户" />}
    <SafeScrollableModal open={mode === "create" || mode === "edit"} title={mode === "create" ? "新增用户" : `编辑用户：${selected?.username || ""}`} onClose={() => setMode(null)} footer={<div className="flex justify-end gap-2"><button className="rounded-xl border px-4 py-2 text-sm" onClick={() => setMode(null)} type="button">取消</button><button className="rounded-xl bg-violet-600 px-4 py-2 text-sm font-semibold text-white disabled:opacity-50" disabled={busy} onClick={() => void save()} type="button">{busy ? "保存中..." : "保存"}</button></div>}><div className="space-y-4">{mode === "create" ? <><Field label="用户名" value={form.username} onChange={(value) => setForm({ ...form, username: value })} /><Field label="初始密码" type="password" value={form.password} onChange={(value) => setForm({ ...form, password: value })} /><Field label="确认密码" type="password" value={form.confirmPassword} onChange={(value) => setForm({ ...form, confirmPassword: value })} /></> : null}<label className="block text-sm font-medium">角色<select className="mt-2 w-full rounded-xl border px-3 py-2" value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value as AdminUser["role"] })}><option value="admin">admin</option><option value="operator">operator</option><option value="viewer">viewer</option></select></label><label className="flex items-center gap-2 text-sm"><input checked={form.enabled} onChange={(e) => setForm({ ...form, enabled: e.target.checked })} type="checkbox" />启用账号</label><label className="block text-sm font-medium">备注<textarea className="mt-2 h-24 w-full rounded-xl border p-3" value={form.remark} onChange={(e) => setForm({ ...form, remark: e.target.value })} /></label>{error ? <ErrorState message={error} /> : null}</div></SafeScrollableModal>
    <SafeScrollableModal open={mode === "password"} title={`重置密码：${selected?.username || ""}`} onClose={() => setMode(null)} footer={<div className="flex justify-end gap-2"><button className="rounded-xl border px-4 py-2 text-sm" onClick={() => setMode(null)} type="button">取消</button><button className="rounded-xl bg-violet-600 px-4 py-2 text-sm font-semibold text-white disabled:opacity-50" disabled={busy} onClick={() => void save()} type="button">{busy ? "重置中..." : "重置密码"}</button></div>}><div className="space-y-4"><Field label="新密码" type="password" value={form.password} onChange={(value) => setForm({ ...form, password: value })} /><Field label="确认新密码" type="password" value={form.confirmPassword} onChange={(value) => setForm({ ...form, confirmPassword: value })} />{error ? <ErrorState message={error} /> : null}</div></SafeScrollableModal>
    <SafeScrollableModal open={mode === "runs"} title={`${selected?.username || "用户"}的任务`} onClose={() => setMode(null)} maxWidth="max-w-4xl">{busy ? <LoadingState label="正在读取任务..." /> : error ? <ErrorState message={error} /> : runs.length ? <div className="overflow-x-auto rounded-xl border"><table className="min-w-[720px] w-full text-left text-xs"><thead className="bg-slate-50"><tr><th className="p-3">run_id</th><th className="p-3">agent_type</th><th className="p-3">状态</th><th className="p-3">创建时间</th><th className="p-3">更新时间</th></tr></thead><tbody>{runs.map((run) => <tr className="border-t" key={run.run_id}><td className="p-3 font-mono">{run.run_id}</td><td className="p-3">{run.agent_type}</td><td className="p-3"><StatusBadge status={run.status} /></td><td className="p-3">{run.created_at || "-"}</td><td className="p-3">{run.updated_at || "-"}</td></tr>)}</tbody></table></div> : <EmptyState title="该用户暂无任务" />}</SafeScrollableModal>
    <ConfirmDialog open={Boolean(confirm)} title={confirm?.enabled ? "启用用户" : "禁用用户"} message={`确定${confirm?.enabled ? "启用" : "禁用"}用户 ${confirm?.user.username || ""} 吗？`} confirmLabel={confirm?.enabled ? "启用" : "禁用"} danger={!confirm?.enabled} busy={busy} onCancel={() => setConfirm(null)} onConfirm={() => void toggleEnabled()} />
  </div>;
}

function IconButton({ label, icon, onClick }: { label: string; icon: ReactNode; onClick: () => void }) { return <button className="inline-flex items-center gap-1 rounded-lg border px-2 py-1 text-xs hover:bg-slate-50" onClick={onClick} type="button">{icon}{label}</button>; }
function Field({ label, value, type = "text", onChange }: { label: string; value: string; type?: string; onChange: (value: string) => void }) { return <label className="block text-sm font-medium">{label}<input className="mt-2 w-full rounded-xl border px-3 py-2" type={type} value={value} onChange={(e) => onChange(e.target.value)} /></label>; }
