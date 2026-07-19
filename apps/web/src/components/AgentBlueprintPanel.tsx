"use client";

import { useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";
import { Copy, Download, FlaskConical, Import, Plus, RotateCcw, Save, ShieldCheck } from "lucide-react";
import { AgentBlueprintEditor } from "@/components/AgentBlueprintEditor";
import { ResultPanelErrorBoundary } from "@/components/ResultPanelErrorBoundary";
import { ErrorState } from "@/components/ui/ErrorState";
import { LoadingState } from "@/components/ui/LoadingState";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { useAgentBlueprint, useAgentBlueprints, useBlueprintDiff, useBlueprintTestRuns, useBlueprintValidations } from "@/hooks/useAgentBlueprints";
import {
  checkAgentBlueprintReleaseGate,
  cloneAgentBlueprint,
  createAgentBlueprint,
  createAgentBlueprintVersion,
  exportAgentBlueprint,
  importAgentBlueprint,
  applyAgentBlueprintRegistrySync,
  previewAgentBlueprintInput,
  previewAgentBlueprintRegistrySync,
  previewAgentBlueprintResult,
  previewImportAgentBlueprint,
  publishAgentBlueprint,
  rollbackAgentBlueprint,
  runAgentBlueprintTestCase,
  saveAgentBlueprintTestCase,
  setAgentBlueprintState,
  updateAgentBlueprint,
  validateAgentBlueprint,
  type AgentBlueprintRegistrySyncPreview,
  type AgentBlueprintVersion
} from "@/lib/api";
import { getStoredUser } from "@/lib/auth";

type Tab = "basic" | "editor" | "tests" | "history" | "diff" | "preview" | "import";

function pretty(value: unknown) {
  return JSON.stringify(value ?? {}, null, 2);
}

function parseJson(text: string) {
  return text.trim() ? JSON.parse(text) : {};
}

export function AgentBlueprintPanel() {
  const currentUser = getStoredUser();
  const isAdmin = currentUser?.role === "admin";
  const canWrite = currentUser?.role === "admin" || currentUser?.role === "operator";
  const { data: listData, error: listError, isLoading, mutate: mutateList } = useAgentBlueprints();
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const { data: detail, error: detailError, mutate: mutateDetail } = useAgentBlueprint(selectedId);
  const [tab, setTab] = useState<Tab>("basic");
  const [basicText, setBasicText] = useState("{}");
  const [testText, setTestText] = useState("{}");
  const [importText, setImportText] = useState("{}");
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [gate, setGate] = useState<Record<string, unknown> | null>(null);
  const [inputPreview, setInputPreview] = useState<Record<string, unknown> | null>(null);
  const [resultPreview, setResultPreview] = useState<Record<string, unknown> | null>(null);
  const [registryPreview, setRegistryPreview] = useState<AgentBlueprintRegistrySyncPreview | null>(null);

  const items = listData?.items || [];
  const blueprint = detail?.blueprint || null;
  const version = detail?.current_version || detail?.published_version || null;
  const published = detail?.published_version || null;
  const firstTest = detail?.test_cases?.[0] || null;
  const { data: validations, mutate: mutateValidations } = useBlueprintValidations(selectedId && tab === "history" ? selectedId : null);
  const { data: testRuns, mutate: mutateTestRuns } = useBlueprintTestRuns(selectedId && (tab === "tests" || tab === "history") ? selectedId : null);
  const { data: diff } = useBlueprintDiff(selectedId && tab === "diff" ? selectedId : null, published?.version_id, version?.version_id);

  useEffect(() => {
    if (!selectedId && items.length) setSelectedId(items[0].blueprint_id);
  }, [items, selectedId]);

  useEffect(() => {
    if (blueprint) setBasicText(pretty({
      agent_id: blueprint.agent_id,
      name: blueprint.name,
      display_name: blueprint.display_name,
      description: blueprint.description,
      category: blueprint.category,
      icon: blueprint.icon,
      metadata: blueprint.metadata || {}
    }));
  }, [blueprint?.blueprint_id, blueprint?.updated_at]);

  useEffect(() => {
    if (firstTest) setTestText(pretty(firstTest));
    else setTestText(pretty({ name: "基础测试", input: { agent_type: blueprint?.agent_id || "", prompt: "blueprint test" }, expected_status: "completed", expected_result_rules: {}, expected_artifacts: {} }));
  }, [firstTest?.test_case_id, blueprint?.agent_id]);

  const tabs = useMemo(() => [
    ["basic", "基本信息"], ["editor", "结构化配置"], ["tests", "测试"], ["history", "历史"], ["diff", "版本差异"], ["preview", "预览"], ["import", "导入导出"]
  ] as Array<[Tab, string]>, []);

  const refresh = async () => {
    await mutateList();
    if (selectedId) await mutateDetail();
    await mutateValidations();
    await mutateTestRuns();
  };

  const runAction = async (label: string, action: () => Promise<unknown>) => {
    setBusy(true); setError(""); setNotice("");
    try {
      await action();
      await refresh();
      setNotice(`${label}完成。`);
    } catch (err) {
      setError(err instanceof Error ? err.message : `${label}失败。`);
    } finally {
      setBusy(false);
    }
  };

  const createDefaultBlueprint = () => runAction("创建蓝图", async () => {
    const created = await createAgentBlueprint({ name: "新蓝图", display_name: "新蓝图", agent_id: "", description: "", category: "未分类" });
    setSelectedId(created.blueprint.blueprint_id);
  });

  const saveBasic = () => runAction("保存基本信息", async () => {
    if (!blueprint) return;
    await updateAgentBlueprint(blueprint.blueprint_id, parseJson(basicText));
  });

  const saveVersion = (payload: Record<string, unknown>) => runAction("创建新版本", async () => {
    if (!blueprint) return;
    await createAgentBlueprintVersion(blueprint.blueprint_id, payload);
  });

  const saveTest = () => runAction("保存测试用例", async () => {
    if (!blueprint) return;
    await saveAgentBlueprintTestCase(blueprint.blueprint_id, parseJson(testText), firstTest?.test_case_id);
  });

  const validateCurrent = () => runAction("验证", async () => {
    if (!blueprint) return;
    const result = await validateAgentBlueprint(blueprint.blueprint_id);
    setNotice(`验证完成：errors=${result.errors.length}, warnings=${result.warnings.length}`);
  });

  const publishCurrent = async () => {
    if (!blueprint || !version) return;
    await runAction("发布", async () => {
      const result = await checkAgentBlueprintReleaseGate(blueprint.blueprint_id, version.version_id);
      setGate(result as unknown as Record<string, unknown>);
      const blocking = (result.blocking_errors || []).length;
      if (blocking) throw new Error((result.blocking_errors || []).map((item) => item.message).join("；"));
      const hasWarnings = (result.warnings || []).length > 0;
      if (hasWarnings && !window.confirm("存在发布警告，确认继续发布？")) return;
      await publishAgentBlueprint(blueprint.blueprint_id, version.version_id, hasWarnings);
    });
  };

  const exportJson = () => runAction("导出蓝图", async () => {
    if (!blueprint) return;
    setImportText(pretty(await exportAgentBlueprint(blueprint.blueprint_id)));
    setTab("import");
  });

  const previewAll = () => runAction("生成预览", async () => {
    if (!blueprint || !version) return;
    setInputPreview(await previewAgentBlueprintInput(blueprint.blueprint_id, version.input_schema || {}));
    setResultPreview(await previewAgentBlueprintResult(blueprint.blueprint_id, version.output_schema || {}, version.result_ui_config || {}));
  });
  const loadRegistryPreview = () => runAction("Registry 对账", async () => {
    setRegistryPreview(await previewAgentBlueprintRegistrySync());
  });
  const createRegistryDrafts = () => runAction("创建 Registry 草稿", async () => {
    if (!registryPreview) return;
    const agentIds = registryPreview.registry_only.map((item) => String(item.agent_type || "")).filter(Boolean);
    await applyAgentBlueprintRegistrySync(agentIds);
    setRegistryPreview(await previewAgentBlueprintRegistrySync());
  });

  return (
    <div className="grid min-h-[620px] gap-4 lg:grid-cols-[280px_1fr]">
      <aside className="min-h-0 rounded-xl border bg-slate-50 p-3">
        <div className="mb-3 flex items-center justify-between gap-2">
          <h3 className="font-bold text-slate-900">智能体蓝图</h3>
          {canWrite ? <button className="rounded-lg bg-violet-600 p-2 text-white disabled:opacity-50" disabled={busy} onClick={() => void createDefaultBlueprint()} type="button"><Plus className="h-4 w-4" /></button> : null}
        </div>
        {canWrite ? <button className="mb-3 w-full rounded-lg border bg-white px-3 py-2 text-sm font-semibold text-slate-700 disabled:opacity-50" disabled={busy} onClick={() => void loadRegistryPreview()} type="button">Registry 对账</button> : null}
        {registryPreview ? <div className="mb-3 rounded-lg border bg-white p-3 text-xs text-slate-600">
          <p>已关联 {registryPreview.matched.length}，Registry 未建蓝图 {registryPreview.registry_only.length}，蓝图找不到 Registry {registryPreview.blueprint_only.length}</p>
          {isAdmin && registryPreview.registry_only.length ? <button className="mt-2 rounded-md bg-violet-600 px-2 py-1 font-semibold text-white" onClick={() => void createRegistryDrafts()} type="button">创建草稿</button> : null}
        </div> : null}
        {isLoading ? <LoadingState label="正在读取蓝图..." /> : null}
        {listError ? <ErrorState message={listError instanceof Error ? listError.message : "蓝图列表读取失败。"} /> : null}
        <div className="max-h-[560px] space-y-2 overflow-y-auto pr-1">
          {items.map((item) => (
            <button className={`w-full rounded-lg border p-3 text-left ${selectedId === item.blueprint_id ? "border-violet-200 bg-white text-violet-800" : "border-transparent bg-white/70 text-slate-700"}`} key={item.blueprint_id} onClick={() => setSelectedId(item.blueprint_id)} type="button">
              <span className="block truncate text-sm font-semibold">{item.display_name}</span>
              <span className="mt-2 flex items-center justify-between gap-2 text-xs"><StatusBadge status={item.status} /><span className="truncate">{item.agent_id || "unbound"}</span></span>
            </button>
          ))}
        </div>
      </aside>

      <section className="min-w-0 rounded-xl border bg-white p-4">
        {detailError ? <ErrorState message={detailError instanceof Error ? detailError.message : "蓝图详情读取失败。"} /> : null}
        {!blueprint ? <LoadingState label="请选择蓝图..." /> : (
          <div className="space-y-4">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <p className="text-xs font-semibold text-violet-700">meizhaiseek v1.8.9</p>
                <h2 className="mt-1 text-2xl font-bold text-slate-950">{blueprint.display_name}</h2>
                <p className="mt-1 text-sm text-slate-500">{blueprint.description || "暂无描述"}</p>
              </div>
              <div className="flex flex-wrap gap-2"><StatusBadge status={blueprint.status} /><span className="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-semibold text-slate-600">v{version?.version_number || "-"}</span></div>
            </div>
            <div className="flex flex-wrap gap-2 border-b pb-3">
              {tabs.map(([id, label]) => <button className={`rounded-lg px-3 py-2 text-sm font-semibold ${tab === id ? "bg-violet-100 text-violet-700" : "bg-slate-50 text-slate-600"}`} key={id} onClick={() => setTab(id)} type="button">{label}</button>)}
            </div>
            {error ? <p className="rounded-lg bg-rose-50 px-4 py-3 text-sm text-rose-600">{error}</p> : null}
            {notice ? <p className="rounded-lg bg-emerald-50 px-4 py-3 text-sm text-emerald-700">{notice}</p> : null}

            {tab === "basic" ? <><Editor title="基本信息 JSON" value={basicText} onChange={setBasicText} readOnly={!canWrite || blueprint.status === "published" || blueprint.status === "deprecated"} />{canWrite ? <ActionBar><Action icon={<Save className="h-4 w-4" />} label="保存基本信息" onClick={() => void saveBasic()} disabled={busy || blueprint.status === "published" || blueprint.status === "deprecated"} /></ActionBar> : null}</> : null}

            {tab === "editor" ? <ResultPanelErrorBoundary><AgentBlueprintEditor version={version as AgentBlueprintVersion | null} readOnly={!canWrite || blueprint.status === "deprecated"} onSave={(payload) => void saveVersion(payload)} /></ResultPanelErrorBoundary> : null}

            {tab === "tests" ? <div className="space-y-3">
              <Editor title="测试用例 JSON" value={testText} onChange={setTestText} readOnly={!canWrite} />
              <ActionBar>
                {canWrite ? <Action icon={<Save className="h-4 w-4" />} label="保存测试" onClick={() => void saveTest()} disabled={busy} /> : null}
                {canWrite && firstTest ? <Action icon={<FlaskConical className="h-4 w-4" />} label="运行测试" onClick={() => void runAction("运行测试", () => runAgentBlueprintTestCase(blueprint.blueprint_id, firstTest.test_case_id))} disabled={busy} /> : null}
                {canWrite ? <Action icon={<ShieldCheck className="h-4 w-4" />} label="验证" onClick={() => void validateCurrent()} disabled={busy} /> : null}
                {isAdmin ? <Action icon={<ShieldCheck className="h-4 w-4" />} label="检查门禁" onClick={() => void runAction("检查门禁", async () => setGate(await checkAgentBlueprintReleaseGate(blueprint.blueprint_id, version?.version_id)))} disabled={busy} /> : null}
                {isAdmin ? <Action icon={<ShieldCheck className="h-4 w-4" />} label="发布" onClick={() => void publishCurrent()} disabled={busy} /> : null}
                {isAdmin ? <Action icon={<RotateCcw className="h-4 w-4" />} label={blueprint.status === "disabled" ? "启用" : "停用"} onClick={() => void runAction("切换状态", () => setAgentBlueprintState(blueprint.blueprint_id, blueprint.status === "disabled" ? "enable" : "disable"))} disabled={busy} /> : null}
              </ActionBar>
              {gate ? <JsonBlock title="发布门禁" value={gate} /> : null}
              <Table title="最近测试运行" rows={testRuns?.items || []} columns={["status", "version_id", "agent_run_id", "actual_status", "duration_ms", "started_at"]} />
            </div> : null}

            {tab === "history" ? <div className="grid gap-4 xl:grid-cols-2">
              <Table title="验证历史" rows={validations?.items || []} columns={["valid", "version_id", "error_count", "warning_count", "checked_by", "checked_at"]} />
              <Table title="测试运行历史" rows={testRuns?.items || []} columns={["status", "version_id", "agent_run_id", "expected_status", "actual_status", "started_at"]} />
            </div> : null}

            {tab === "diff" ? <div className="space-y-3">
              {!published || !version ? <p className="text-sm text-slate-500">需要已发布版本和当前版本才能对比。</p> : null}
              {diff ? <><p className="text-sm font-semibold">变更汇总：{pretty(diff.summary)}</p>{diff.sections.map((section) => <details className="rounded-lg border p-3" key={section.section} open={section.has_changes && section.section !== "prompt_config"}><summary className="cursor-pointer font-semibold">{section.label} {section.has_changes ? "有变化" : "无变化"}</summary><pre className="mt-3 max-h-72 overflow-auto rounded-lg bg-slate-950 p-3 text-xs text-slate-50">{pretty(section.changes)}</pre></details>)}</> : null}
              {detail?.versions.map((item) => item.is_published && isAdmin ? <button className="mr-2 rounded-lg border px-3 py-2 text-sm font-semibold" key={item.version_id} onClick={() => window.confirm("确认回滚到该历史发布版本？") && void runAction("回滚", () => rollbackAgentBlueprint(blueprint.blueprint_id, item.version_id))} type="button">回滚到 v{item.version_number}</button> : null)}
              {canWrite ? <Action icon={<Copy className="h-4 w-4" />} label="复制为草稿" onClick={() => void runAction("复制蓝图", () => cloneAgentBlueprint(blueprint.blueprint_id))} disabled={busy} /> : null}
            </div> : null}

            {tab === "preview" ? <div className="space-y-3">
              <Action icon={<ShieldCheck className="h-4 w-4" />} label="生成输入/结果预览" onClick={() => void previewAll()} disabled={busy || !version} />
              <div className="grid gap-4 xl:grid-cols-2"><Preview title="输入表单预览" value={inputPreview} /><Preview title="结果结构预览" value={resultPreview} /></div>
            </div> : null}

            {tab === "import" ? <div className="space-y-3">
              <Editor title="导入/导出 JSON" value={importText} onChange={setImportText} readOnly={!canWrite} />
              <ActionBar>
                {canWrite ? <Action icon={<Download className="h-4 w-4" />} label="导出当前蓝图" onClick={() => void exportJson()} disabled={busy} /> : null}
                {canWrite ? <Action icon={<Import className="h-4 w-4" />} label="导入预览" onClick={() => void runAction("导入预览", async () => setNotice(pretty(await previewImportAgentBlueprint(parseJson(importText)))))} disabled={busy} /> : null}
                {canWrite ? <Action icon={<Import className="h-4 w-4" />} label="正式导入" onClick={() => window.confirm("确认导入蓝图？") && void runAction("导入蓝图", () => importAgentBlueprint(parseJson(importText)))} disabled={busy} /> : null}
              </ActionBar>
            </div> : null}
          </div>
        )}
      </section>
    </div>
  );
}

function Editor({ title, value, onChange, readOnly }: { title: string; value: string; onChange: (value: string) => void; readOnly?: boolean }) {
  return <label className="block text-sm font-semibold text-slate-800">{title}<textarea className="mt-2 h-[360px] w-full resize-none rounded-xl border border-slate-200 bg-slate-50 p-3 font-mono text-xs leading-5 text-slate-900 outline-none focus:bg-white focus:ring-2 focus:ring-violet-200" onChange={(event) => onChange(event.target.value)} readOnly={readOnly} value={value} /></label>;
}

function ActionBar({ children }: { children: ReactNode }) {
  return <div className="flex flex-wrap gap-2">{children}</div>;
}

function Action({ icon, label, onClick, disabled }: { icon: ReactNode; label: string; onClick: () => void; disabled?: boolean }) {
  return <button className="inline-flex items-center gap-2 rounded-lg border border-violet-200 bg-white px-3 py-2 text-sm font-semibold text-violet-700 disabled:opacity-50" disabled={disabled} onClick={onClick} type="button">{icon}{label}</button>;
}

function JsonBlock({ title, value }: { title: string; value: unknown }) {
  return <details className="rounded-lg border p-3" open><summary className="cursor-pointer font-semibold">{title}</summary><pre className="mt-3 max-h-72 overflow-auto rounded-lg bg-slate-950 p-3 text-xs text-slate-50">{pretty(value)}</pre></details>;
}

function Table({ title, rows, columns }: { title: string; rows: Record<string, any>[]; columns: string[] }) {
  return <section className="overflow-x-auto rounded-lg border"><h3 className="p-3 font-semibold">{title}</h3><table className="min-w-[720px] w-full text-left text-xs"><thead className="bg-slate-50"><tr>{columns.map((col) => <th className="p-2" key={col}>{col}</th>)}</tr></thead><tbody>{rows.slice(0, 20).map((row, index) => <tr className="border-t" key={row.test_run_id || row.validation_id || index}>{columns.map((col) => <td className="max-w-64 truncate p-2" key={col}>{String(row[col] ?? "-")}</td>)}</tr>)}</tbody></table>{!rows.length ? <p className="p-3 text-sm text-slate-500">暂无记录</p> : null}</section>;
}

function Preview({ title, value }: { title: string; value: Record<string, unknown> | null }) {
  return <section className="rounded-lg border p-3"><h3 className="font-semibold">{title}</h3>{value ? <pre className="mt-3 max-h-96 overflow-auto rounded-lg bg-slate-950 p-3 text-xs text-slate-50">{pretty(value)}</pre> : <p className="mt-2 text-sm text-slate-500">点击生成预览。</p>}</section>;
}
