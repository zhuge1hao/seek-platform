"use client";

import { useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";
import { Copy, Download, FlaskConical, Import, Plus, RotateCcw, Save, ShieldCheck } from "lucide-react";
import { ErrorState } from "@/components/ui/ErrorState";
import { LoadingState } from "@/components/ui/LoadingState";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { useAgentBlueprint, useAgentBlueprints } from "@/hooks/useAgentBlueprints";
import {
  cloneAgentBlueprint,
  createAgentBlueprint,
  createAgentBlueprintVersion,
  exportAgentBlueprint,
  importAgentBlueprint,
  previewImportAgentBlueprint,
  publishAgentBlueprint,
  rollbackAgentBlueprint,
  runAgentBlueprintTestCase,
  saveAgentBlueprintTestCase,
  setAgentBlueprintState,
  updateAgentBlueprint,
  validateAgentBlueprint,
  type AgentBlueprintVersion
} from "@/lib/api";
import { getStoredUser } from "@/lib/auth";

type Tab = "basic" | "config" | "tests" | "versions" | "import";
type ConfigKey = "input_schema" | "methodology" | "prompt_config" | "execution_config" | "output_schema" | "result_ui_config" | "acceptance_rules";

const configLabels: Record<ConfigKey, string> = {
  input_schema: "输入配置",
  methodology: "方法论",
  prompt_config: "Prompt",
  execution_config: "执行配置",
  output_schema: "输出配置",
  result_ui_config: "结果 UI",
  acceptance_rules: "验收规则"
};

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
  const [configKey, setConfigKey] = useState<ConfigKey>("input_schema");
  const [jsonText, setJsonText] = useState("{}");
  const [importText, setImportText] = useState("{}");
  const [basicText, setBasicText] = useState("{}");
  const [testText, setTestText] = useState("{}");
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const items = listData?.items || [];
  const blueprint = detail?.blueprint || null;
  const version = detail?.current_version || detail?.published_version || null;
  const firstTest = detail?.test_cases?.[0] || null;
  const versions = detail?.versions || [];

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
    if (version) setJsonText(pretty(version[configKey] || {}));
  }, [version?.version_id, configKey]);

  useEffect(() => {
    if (firstTest) setTestText(pretty(firstTest));
    else setTestText(pretty({ name: "基础测试", input: { agent_type: blueprint?.agent_id || "", prompt: "blueprint test" }, expected_status: "completed" }));
  }, [firstTest?.test_case_id, blueprint?.agent_id]);

  const runAction = async (label: string, action: () => Promise<unknown>) => {
    setBusy(true); setError(""); setNotice("");
    try {
      await action();
      await mutateList();
      if (selectedId) await mutateDetail();
      setNotice(`${label}完成。`);
    } catch (err) {
      setError(err instanceof Error ? err.message : `${label}失败。`);
    } finally {
      setBusy(false);
    }
  };

  const tabs = useMemo(() => [
    ["basic", "基本信息"], ["config", "配置"], ["tests", "测试与发布"], ["versions", "版本历史"], ["import", "导入导出"]
  ] as Array<[Tab, string]>, []);

  const createDefaultBlueprint = () => runAction("创建蓝图", async () => {
    const detail = await createAgentBlueprint({ name: "新蓝图", display_name: "新蓝图", agent_id: "", description: "", category: "未分类" });
    setSelectedId(detail.blueprint.blueprint_id);
  });

  const saveBasic = () => runAction("保存基本信息", async () => {
    if (!blueprint) return;
    await updateAgentBlueprint(blueprint.blueprint_id, parseJson(basicText));
  });

  const saveVersion = () => runAction("创建新版本", async () => {
    if (!blueprint || !version) return;
    await createAgentBlueprintVersion(blueprint.blueprint_id, { ...version, [configKey]: parseJson(jsonText), change_summary: `更新${configLabels[configKey]}` });
  });

  const saveTest = () => runAction("保存测试用例", async () => {
    if (!blueprint) return;
    const payload = parseJson(testText);
    await saveAgentBlueprintTestCase(blueprint.blueprint_id, payload, firstTest?.test_case_id);
  });

  const exportJson = () => runAction("导出蓝图", async () => {
    if (!blueprint) return;
    const data = await exportAgentBlueprint(blueprint.blueprint_id);
    setImportText(pretty(data));
    setTab("import");
  });

  const previewImport = () => runAction("导入预览", async () => {
    const result = await previewImportAgentBlueprint(parseJson(importText));
    setNotice(`导入预览：${result.valid ? "可导入" : "不可导入"}${result.conflict ? "，ID 冲突将创建新蓝图" : ""}`);
  });

  const doImport = () => runAction("导入蓝图", async () => {
    await importAgentBlueprint(parseJson(importText));
  });

  return (
    <div className="grid min-h-[620px] gap-4 lg:grid-cols-[280px_1fr]">
      <aside className="min-h-0 rounded-2xl border bg-slate-50 p-3">
        <div className="mb-3 flex items-center justify-between gap-2">
          <h3 className="font-bold text-slate-900">智能体蓝图</h3>
          {canWrite ? <button className="rounded-xl bg-violet-600 p-2 text-white disabled:opacity-50" disabled={busy} onClick={() => void createDefaultBlueprint()} type="button"><Plus className="h-4 w-4" /></button> : null}
        </div>
        {isLoading ? <LoadingState label="正在读取蓝图..." /> : null}
        {listError ? <ErrorState message={listError instanceof Error ? listError.message : "蓝图列表读取失败。"} /> : null}
        <div className="max-h-[560px] space-y-2 overflow-y-auto pr-1">
          {items.map((item) => (
            <button className={`w-full rounded-xl border p-3 text-left ${selectedId === item.blueprint_id ? "border-violet-200 bg-white text-violet-800" : "border-transparent bg-white/70 text-slate-700"}`} key={item.blueprint_id} onClick={() => setSelectedId(item.blueprint_id)} type="button">
              <span className="block truncate text-sm font-semibold">{item.display_name}</span>
              <span className="mt-2 flex items-center justify-between gap-2 text-xs"><StatusBadge status={item.status} /><span className="truncate">{item.agent_id || "unbound"}</span></span>
            </button>
          ))}
        </div>
      </aside>

      <section className="min-w-0 rounded-2xl border bg-white p-4">
        {detailError ? <ErrorState message={detailError instanceof Error ? detailError.message : "蓝图详情读取失败。"} /> : null}
        {!blueprint ? <LoadingState label="请选择蓝图..." /> : (
          <div className="space-y-4">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <p className="text-xs font-semibold text-violet-700">meizhaiseek v1.7</p>
                <h2 className="mt-1 text-2xl font-bold text-slate-950">{blueprint.display_name}</h2>
                <p className="mt-1 text-sm text-slate-500">{blueprint.description || "暂无描述"}</p>
              </div>
              <div className="flex flex-wrap gap-2">
                <StatusBadge status={blueprint.status} />
                <span className="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-semibold text-slate-600">v{version?.version_number || "-"}</span>
              </div>
            </div>
            <div className="flex flex-wrap gap-2 border-b pb-3">
              {tabs.map(([id, label]) => <button className={`rounded-xl px-3 py-2 text-sm font-semibold ${tab === id ? "bg-violet-100 text-violet-700" : "bg-slate-50 text-slate-600"}`} key={id} onClick={() => setTab(id)} type="button">{label}</button>)}
            </div>
            {error ? <p className="rounded-xl bg-rose-50 px-4 py-3 text-sm text-rose-600">{error}</p> : null}
            {notice ? <p className="rounded-xl bg-emerald-50 px-4 py-3 text-sm text-emerald-700">{notice}</p> : null}

            {tab === "basic" ? <Editor title="基本信息 JSON" value={basicText} onChange={setBasicText} readOnly={!canWrite || blueprint.status === "published" || blueprint.status === "deprecated"} /> : null}
            {tab === "basic" && canWrite ? <ActionBar><Action icon={<Save className="h-4 w-4" />} label="保存基本信息" onClick={() => void saveBasic()} disabled={busy || blueprint.status === "published" || blueprint.status === "deprecated"} /></ActionBar> : null}

            {tab === "config" ? <div className="space-y-3">
              <select className="rounded-xl border px-3 py-2 text-sm" value={configKey} onChange={(event) => setConfigKey(event.target.value as ConfigKey)}>
                {(Object.keys(configLabels) as ConfigKey[]).map((key) => <option key={key} value={key}>{configLabels[key]}</option>)}
              </select>
              <Editor title={`${configLabels[configKey]} JSON`} value={jsonText} onChange={setJsonText} readOnly={!canWrite || blueprint.status === "deprecated"} />
              {canWrite ? <ActionBar><Action icon={<Save className="h-4 w-4" />} label="创建新版本" onClick={() => void saveVersion()} disabled={busy || blueprint.status === "deprecated"} /></ActionBar> : null}
            </div> : null}

            {tab === "tests" ? <div className="space-y-3">
              <Editor title="测试用例 JSON" value={testText} onChange={setTestText} readOnly={!canWrite} />
              <div className="flex flex-wrap gap-2">
                {canWrite ? <Action icon={<Save className="h-4 w-4" />} label="保存测试" onClick={() => void saveTest()} disabled={busy} /> : null}
                {canWrite && firstTest ? <Action icon={<FlaskConical className="h-4 w-4" />} label="运行测试" onClick={() => void runAction("运行测试", () => runAgentBlueprintTestCase(blueprint.blueprint_id, firstTest.test_case_id))} disabled={busy} /> : null}
                {canWrite ? <Action icon={<ShieldCheck className="h-4 w-4" />} label="校验" onClick={() => void runAction("校验", async () => { const result = await validateAgentBlueprint(blueprint.blueprint_id); setNotice(`errors=${result.errors.length}, warnings=${result.warnings.length}`); })} disabled={busy} /> : null}
                {isAdmin ? <Action icon={<ShieldCheck className="h-4 w-4" />} label="发布" onClick={() => window.confirm("确认发布当前蓝图版本？") && void runAction("发布", () => publishAgentBlueprint(blueprint.blueprint_id, version?.version_id))} disabled={busy} /> : null}
                {isAdmin ? <Action icon={<RotateCcw className="h-4 w-4" />} label={blueprint.status === "disabled" ? "启用" : "停用"} onClick={() => void runAction("切换状态", () => setAgentBlueprintState(blueprint.blueprint_id, blueprint.status === "disabled" ? "enable" : "disable"))} disabled={busy} /> : null}
              </div>
              {firstTest?.last_result ? <pre className="max-h-40 overflow-auto rounded-xl bg-slate-950 p-3 text-xs text-slate-50">{pretty(firstTest.last_result)}</pre> : null}
            </div> : null}

            {tab === "versions" ? <div className="space-y-2">
              {versions.map((item: AgentBlueprintVersion) => (
                <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border p-3" key={item.version_id}>
                  <div><p className="font-semibold">v{item.version_number} {item.version_name}</p><p className="text-xs text-slate-500">{item.change_summary || item.created_at}</p></div>
                  <div className="flex gap-2">{item.is_published ? <StatusBadge status="published" /> : null}{isAdmin && item.is_published ? <button className="rounded-xl border px-3 py-2 text-sm font-semibold" onClick={() => window.confirm("确认回滚到该历史发布版本？") && void runAction("回滚", () => rollbackAgentBlueprint(blueprint.blueprint_id, item.version_id))} type="button">回滚</button> : null}</div>
                </div>
              ))}
              {canWrite ? <Action icon={<Copy className="h-4 w-4" />} label="复制为草稿" onClick={() => void runAction("复制蓝图", () => cloneAgentBlueprint(blueprint.blueprint_id))} disabled={busy} /> : null}
            </div> : null}

            {tab === "import" ? <div className="space-y-3">
              <Editor title="导入/导出 JSON" value={importText} onChange={setImportText} readOnly={!canWrite} />
              <div className="flex flex-wrap gap-2">
                {canWrite ? <Action icon={<Download className="h-4 w-4" />} label="导出当前蓝图" onClick={() => void exportJson()} disabled={busy} /> : null}
                {canWrite ? <Action icon={<Import className="h-4 w-4" />} label="导入预览" onClick={() => void previewImport()} disabled={busy} /> : null}
                {canWrite ? <Action icon={<Import className="h-4 w-4" />} label="正式导入" onClick={() => window.confirm("确认导入蓝图？") && void doImport()} disabled={busy} /> : null}
              </div>
            </div> : null}
          </div>
        )}
      </section>
    </div>
  );
}

function Editor({ title, value, onChange, readOnly }: { title: string; value: string; onChange: (value: string) => void; readOnly?: boolean }) {
  return <label className="block text-sm font-semibold text-slate-800">{title}<textarea className="mt-2 h-[360px] w-full resize-none rounded-2xl border border-slate-200 bg-slate-50 p-3 font-mono text-xs leading-5 text-slate-900 outline-none focus:bg-white focus:ring-2 focus:ring-violet-200" onChange={(event) => onChange(event.target.value)} readOnly={readOnly} value={value} /></label>;
}

function ActionBar({ children }: { children: ReactNode }) {
  return <div className="flex flex-wrap gap-2">{children}</div>;
}

function Action({ icon, label, onClick, disabled }: { icon: ReactNode; label: string; onClick: () => void; disabled?: boolean }) {
  return <button className="inline-flex items-center gap-2 rounded-xl border border-violet-200 bg-white px-3 py-2 text-sm font-semibold text-violet-700 disabled:opacity-50" disabled={disabled} onClick={onClick} type="button">{icon}{label}</button>;
}
