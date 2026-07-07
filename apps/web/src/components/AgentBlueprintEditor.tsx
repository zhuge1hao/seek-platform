"use client";

import { useEffect, useState } from "react";
import type { ReactNode } from "react";
import { ArrowDown, ArrowUp, Plus, Trash2 } from "lucide-react";
import type { AgentBlueprintVersion } from "@/lib/api";

type Props = {
  version: AgentBlueprintVersion | null;
  readOnly?: boolean;
  onSave: (payload: Record<string, unknown>) => void;
};

type EditableItem = Record<string, unknown> & {
  field_id?: string;
  section_id?: string;
  step_id?: string;
  name?: string;
  label?: string;
  type?: string;
  description?: string;
  placeholder?: string;
  required?: boolean;
  failure_policy?: string;
  timeout_seconds?: number | string;
  input_fields?: string[];
  output_fields?: string[];
  order?: number;
};

type EditableDraft = Record<string, unknown> & {
  input_schema?: Record<string, unknown> & { fields?: EditableItem[] };
  methodology?: Record<string, unknown> & { steps?: EditableItem[] };
  prompt_config?: Record<string, unknown> & { system_prompt?: string; user_prompt_template?: string; variables?: Array<string | { name?: string }> };
  execution_config?: Record<string, unknown> & { execution_type?: string; agent_id?: string; workflow_type?: string; connector_id?: string; timeout_seconds?: number | string; output_dir_strategy?: string };
  output_schema?: Record<string, unknown> & { sections?: EditableItem[] };
  result_ui_config?: Record<string, unknown> & { renderer?: string; tabs?: string[] };
  acceptance_rules?: Record<string, unknown> & { required_result_fields?: string[]; required_artifact_types?: string[]; max_duration_seconds?: number };
};

const inputTypes = ["text", "textarea", "number", "boolean", "select", "multi_select", "file", "image", "video", "excel", "word", "local_path", "dataset", "knowledge_base"];
const failurePolicies = ["stop", "continue", "retry", "skip"];
const executionTypes = ["internal", "http_connector", "cli_connector", "mock"];
const renderers = ["generic_text", "generic_structured", "video_breakdown", "table_report", "dataset_report"];
const outputTypes = ["summary", "steps", "text", "table", "metrics", "timeline", "subtitles", "selling_points", "images", "proof_frames", "warnings", "recommendations", "artifacts", "raw_preview"];

function clone<T>(value: T): T {
  return JSON.parse(JSON.stringify(value ?? {}));
}

function pretty(value: unknown) {
  return JSON.stringify(value ?? {}, null, 2);
}

function split(value: unknown) {
  return String(value || "").split(",").map((item) => item.trim()).filter(Boolean);
}

export function AgentBlueprintEditor({ version, readOnly, onSave }: Props) {
  const [mode, setMode] = useState<"form" | "json">("form");
  const [draft, setDraft] = useState<EditableDraft>({});
  const [jsonText, setJsonText] = useState("{}");
  const [error, setError] = useState("");
  const [dragIndex, setDragIndex] = useState<number | null>(null);
  const [dragOverIndex, setDragOverIndex] = useState<number | null>(null);

  useEffect(() => {
    const next = version ? {
      input_schema: clone(version.input_schema || { fields: [] }),
      methodology: clone(version.methodology || { steps: [] }),
      prompt_config: clone(version.prompt_config || {}),
      execution_config: clone(version.execution_config || {}),
      output_schema: clone(version.output_schema || { sections: [] }),
      result_ui_config: clone(version.result_ui_config || {}),
      acceptance_rules: clone(version.acceptance_rules || {}),
    } : {};
    setDraft(next);
    setJsonText(pretty(next));
    setError("");
  }, [version?.version_id]);

  const syncJson = (next: EditableDraft) => {
    setDraft(next);
    setJsonText(pretty(next));
  };

  const save = () => {
    try {
      const payload = mode === "json" ? JSON.parse(jsonText || "{}") : draft;
      setError("");
      onSave({ ...payload, change_summary: "v1.8 visual editor update" });
    } catch (err) {
      setError(err instanceof Error ? err.message : "JSON 格式错误");
    }
  };

  const fields = draft.input_schema?.fields || [];
  const steps = draft.methodology?.steps || [];
  const sections = draft.output_schema?.sections || [];
  const variables = draft.prompt_config?.variables || [];

  const setPart = (key: string, value: unknown) => syncJson({ ...draft, [key]: value });
  const setField = (index: number, patch: Record<string, unknown>) => {
    const next = [...fields]; next[index] = { ...next[index], ...patch };
    setPart("input_schema", { ...(draft.input_schema || {}), fields: next });
  };
  const setStep = (index: number, patch: Record<string, unknown>) => {
    const next = [...steps]; next[index] = { ...next[index], ...patch };
    setPart("methodology", { ...(draft.methodology || {}), steps: next.map((step, order) => ({ ...step, order: order + 1 })) });
  };
  const setSection = (index: number, patch: Record<string, unknown>) => {
    const next = [...sections]; next[index] = { ...next[index], ...patch };
    setPart("output_schema", { ...(draft.output_schema || {}), sections: next.map((section, order) => ({ ...section, order: order + 1 })) });
  };
  const move = (items: EditableItem[], index: number, delta: number, setter: (items: EditableItem[]) => void) => {
    const next = [...items]; const target = index + delta;
    if (target < 0 || target >= next.length) return;
    [next[index], next[target]] = [next[target], next[index]];
    setter(next);
  };
  const reorderSteps = (from: number, to: number) => {
    if (readOnly || from === to || from < 0 || to < 0 || from >= steps.length || to >= steps.length) return;
    const next = [...steps];
    const [moved] = next.splice(from, 1);
    next.splice(to, 0, moved);
    setPart("methodology", { ...(draft.methodology || {}), steps: next.map((item, order) => ({ ...item, order: order + 1 })) });
  };

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex gap-2">
          <button className={`rounded-lg px-3 py-2 text-sm font-semibold ${mode === "form" ? "bg-violet-100 text-violet-700" : "bg-slate-100 text-slate-600"}`} onClick={() => setMode("form")} type="button">表单模式</button>
          <button className={`rounded-lg px-3 py-2 text-sm font-semibold ${mode === "json" ? "bg-violet-100 text-violet-700" : "bg-slate-100 text-slate-600"}`} onClick={() => setMode("json")} type="button">高级 JSON</button>
        </div>
        <button className="rounded-lg bg-violet-600 px-4 py-2 text-sm font-semibold text-white disabled:opacity-50" disabled={readOnly} onClick={save} type="button">创建新版本</button>
      </div>
      {error ? <p className="rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700">{error}</p> : null}
      {mode === "json" ? (
        <textarea className="h-[520px] w-full rounded-xl border bg-slate-50 p-3 font-mono text-xs" onChange={(event) => setJsonText(event.target.value)} readOnly={readOnly} value={jsonText} />
      ) : (
        <div className="grid gap-4 xl:grid-cols-2">
          <Section title="输入协议">
            {fields.map((field, index) => <div className="rounded-lg border p-3" key={index}>
              <Row><Text value={field.field_id} onChange={(value) => setField(index, { field_id: value })} readOnly={readOnly} placeholder="field_id" /><Text value={field.label} onChange={(value) => setField(index, { label: value })} readOnly={readOnly} placeholder="label" /></Row>
              <Row><Select value={field.type || "text"} options={inputTypes} onChange={(value) => setField(index, { type: value })} disabled={readOnly} /><Text value={field.placeholder} onChange={(value) => setField(index, { placeholder: value })} readOnly={readOnly} placeholder="placeholder" /></Row>
              <Text value={field.description} onChange={(value) => setField(index, { description: value })} readOnly={readOnly} placeholder="description" />
              <Row><label className="text-xs"><input checked={Boolean(field.required)} disabled={readOnly} onChange={(event) => setField(index, { required: event.target.checked })} type="checkbox" /> 必填</label><Tools onDelete={() => setPart("input_schema", { ...(draft.input_schema || {}), fields: fields.filter((_, i) => i !== index) })} onDown={() => move(fields, index, 1, (items) => setPart("input_schema", { ...(draft.input_schema || {}), fields: items }))} onUp={() => move(fields, index, -1, (items) => setPart("input_schema", { ...(draft.input_schema || {}), fields: items }))} readOnly={readOnly} /></Row>
            </div>)}
            <Add onClick={() => setPart("input_schema", { ...(draft.input_schema || {}), fields: [...fields, { field_id: `field_${fields.length + 1}`, label: "新字段", type: "text", required: false }] })} disabled={readOnly} />
          </Section>

          <Section title="方法论步骤">
            {steps.map((step, index) => <div
              className={`rounded-lg border p-3 ${dragOverIndex === index ? "border-violet-400 bg-violet-50" : ""}`}
              draggable={!readOnly}
              key={index}
              onDragEnd={() => { setDragIndex(null); setDragOverIndex(null); }}
              onDragOver={(event) => {
                if (readOnly) return;
                event.preventDefault();
                setDragOverIndex(index);
              }}
              onDragStart={(event) => {
                if (readOnly) return;
                setDragIndex(index);
                event.dataTransfer.effectAllowed = "move";
                event.dataTransfer.setData("text/plain", String(index));
              }}
              onDrop={(event) => {
                if (readOnly) return;
                event.preventDefault();
                const from = dragIndex ?? Number(event.dataTransfer.getData("text/plain"));
                reorderSteps(from, index);
                setDragIndex(null);
                setDragOverIndex(null);
              }}
            >
              <Row><Text value={step.step_id} onChange={(value) => setStep(index, { step_id: value })} readOnly={readOnly} placeholder="step_id" /><Text value={step.name} onChange={(value) => setStep(index, { name: value })} readOnly={readOnly} placeholder="name" /></Row>
              <Text value={step.description} onChange={(value) => setStep(index, { description: value })} readOnly={readOnly} placeholder="description" />
              <Row><Text value={(step.input_fields || []).join(", ")} onChange={(value) => setStep(index, { input_fields: split(value) })} readOnly={readOnly} placeholder="input_fields" /><Text value={(step.output_fields || []).join(", ")} onChange={(value) => setStep(index, { output_fields: split(value) })} readOnly={readOnly} placeholder="output_fields" /></Row>
              <Row><Select value={step.failure_policy || "stop"} options={failurePolicies} onChange={(value) => setStep(index, { failure_policy: value })} disabled={readOnly} /><Text value={step.timeout_seconds || ""} onChange={(value) => setStep(index, { timeout_seconds: Number(value) || 30 })} readOnly={readOnly} placeholder="timeout_seconds" /></Row>
              <Row><label className="text-xs"><input checked={Boolean(step.required)} disabled={readOnly} onChange={(event) => setStep(index, { required: event.target.checked })} type="checkbox" /> 必需</label><Tools onDelete={() => setPart("methodology", { ...(draft.methodology || {}), steps: steps.filter((_, i) => i !== index).map((item, order) => ({ ...item, order: order + 1 })) })} onDown={() => move(steps, index, 1, (items) => setPart("methodology", { ...(draft.methodology || {}), steps: items.map((item, order) => ({ ...item, order: order + 1 })) }))} onUp={() => move(steps, index, -1, (items) => setPart("methodology", { ...(draft.methodology || {}), steps: items.map((item, order) => ({ ...item, order: order + 1 })) }))} readOnly={readOnly} /></Row>
            </div>)}
            <Add onClick={() => setPart("methodology", { ...(draft.methodology || {}), steps: [...steps, { step_id: `step_${steps.length + 1}`, name: "新步骤", order: steps.length + 1, required: true, failure_policy: "stop" }] })} disabled={readOnly} />
          </Section>

          <Section title="Prompt">
            <Area value={draft.prompt_config?.system_prompt || ""} onChange={(value) => setPart("prompt_config", { ...(draft.prompt_config || {}), system_prompt: value })} readOnly={readOnly} placeholder="system_prompt" />
            <Area value={draft.prompt_config?.user_prompt_template || ""} onChange={(value) => setPart("prompt_config", { ...(draft.prompt_config || {}), user_prompt_template: value })} readOnly={readOnly} placeholder="user_prompt_template" />
            <Text value={variables.map((item) => typeof item === "string" ? item : item.name || "").filter(Boolean).join(", ")} onChange={(value) => setPart("prompt_config", { ...(draft.prompt_config || {}), variables: split(value).map((name) => ({ name, required: true })) })} readOnly={readOnly} placeholder="variables: video_file, output_dir" />
          </Section>

          <Section title="执行配置">
            <Row><Select value={draft.execution_config?.execution_type || "mock"} options={executionTypes} onChange={(value) => setPart("execution_config", { ...(draft.execution_config || {}), execution_type: value })} disabled={readOnly} /><Text value={draft.execution_config?.agent_id || ""} onChange={(value) => setPart("execution_config", { ...(draft.execution_config || {}), agent_id: value })} readOnly={readOnly} placeholder="agent_id" /></Row>
            <Row><Text value={draft.execution_config?.workflow_type || ""} onChange={(value) => setPart("execution_config", { ...(draft.execution_config || {}), workflow_type: value })} readOnly={readOnly} placeholder="workflow_type" /><Text value={draft.execution_config?.connector_id || ""} onChange={(value) => setPart("execution_config", { ...(draft.execution_config || {}), connector_id: value })} readOnly={readOnly} placeholder="connector_id" /></Row>
            <Row><Text value={draft.execution_config?.timeout_seconds || ""} onChange={(value) => setPart("execution_config", { ...(draft.execution_config || {}), timeout_seconds: Number(value) || 300 })} readOnly={readOnly} placeholder="timeout_seconds" /><Text value={draft.execution_config?.output_dir_strategy || ""} onChange={(value) => setPart("execution_config", { ...(draft.execution_config || {}), output_dir_strategy: value })} readOnly={readOnly} placeholder="output_dir_strategy" /></Row>
            {draft.execution_config?.execution_type === "mock" ? <p className="rounded-lg bg-amber-50 px-3 py-2 text-xs text-amber-700">mock 仅用于测试描述，不代表正式业务智能体可用。</p> : null}
          </Section>

          <Section title="输出协议">
            {sections.map((section, index) => <div className="rounded-lg border p-3" key={index}>
              <Row><Text value={section.section_id} onChange={(value) => setSection(index, { section_id: value })} readOnly={readOnly} placeholder="section_id" /><Select value={section.type || "text"} options={outputTypes} onChange={(value) => setSection(index, { type: value })} disabled={readOnly} /></Row>
              <Row><Text value={section.label} onChange={(value) => setSection(index, { label: value })} readOnly={readOnly} placeholder="label" /><label className="text-xs"><input checked={Boolean(section.required)} disabled={readOnly} onChange={(event) => setSection(index, { required: event.target.checked })} type="checkbox" /> 必需</label></Row>
              <Tools onDelete={() => setPart("output_schema", { ...(draft.output_schema || {}), sections: sections.filter((_, i) => i !== index) })} onDown={() => move(sections, index, 1, (items) => setPart("output_schema", { ...(draft.output_schema || {}), sections: items }))} onUp={() => move(sections, index, -1, (items) => setPart("output_schema", { ...(draft.output_schema || {}), sections: items }))} readOnly={readOnly} />
            </div>)}
            <Add onClick={() => setPart("output_schema", { ...(draft.output_schema || {}), sections: [...sections, { section_id: `section_${sections.length + 1}`, type: "text", label: "新区块", order: sections.length + 1 }] })} disabled={readOnly} />
            <Row><Select value={draft.result_ui_config?.renderer || "generic_structured"} options={renderers} onChange={(value) => setPart("result_ui_config", { ...(draft.result_ui_config || {}), renderer: value })} disabled={readOnly} /><Text value={(draft.result_ui_config?.tabs || []).join(", ")} onChange={(value) => setPart("result_ui_config", { ...(draft.result_ui_config || {}), tabs: split(value) })} readOnly={readOnly} placeholder="tabs" /></Row>
          </Section>

          <Section title="验收规则">
            <Text value={(draft.acceptance_rules?.required_result_fields || []).join(", ")} onChange={(value) => setPart("acceptance_rules", { ...(draft.acceptance_rules || {}), required_result_fields: split(value) })} readOnly={readOnly} placeholder="required_result_fields" />
            <Text value={(draft.acceptance_rules?.required_artifact_types || []).join(", ")} onChange={(value) => setPart("acceptance_rules", { ...(draft.acceptance_rules || {}), required_artifact_types: split(value) })} readOnly={readOnly} placeholder="required_artifact_types" />
            <Text value={draft.acceptance_rules?.max_duration_seconds || ""} onChange={(value) => setPart("acceptance_rules", { ...(draft.acceptance_rules || {}), max_duration_seconds: Number(value) || undefined })} readOnly={readOnly} placeholder="max_duration_seconds" />
          </Section>
        </div>
      )}
    </div>
  );
}

function Section({ title, children }: { title: string; children: ReactNode }) {
  return <section className="space-y-3 rounded-xl border bg-white p-4"><h3 className="font-semibold text-slate-900">{title}</h3>{children}</section>;
}

function Row({ children }: { children: ReactNode }) {
  return <div className="grid gap-2 sm:grid-cols-2">{children}</div>;
}

function Text({ value, onChange, readOnly, placeholder }: { value: unknown; onChange: (value: string) => void; readOnly?: boolean; placeholder?: string }) {
  return <input className="w-full rounded-lg border px-3 py-2 text-sm" onChange={(event) => onChange(event.target.value)} placeholder={placeholder} readOnly={readOnly} value={String(value ?? "")} />;
}

function Area({ value, onChange, readOnly, placeholder }: { value: string; onChange: (value: string) => void; readOnly?: boolean; placeholder?: string }) {
  return <textarea className="h-28 w-full rounded-lg border px-3 py-2 text-sm" onChange={(event) => onChange(event.target.value)} placeholder={placeholder} readOnly={readOnly} value={value} />;
}

function Select({ value, options, onChange, disabled }: { value: string; options: string[]; onChange: (value: string) => void; disabled?: boolean }) {
  return <select className="w-full rounded-lg border px-3 py-2 text-sm" disabled={disabled} onChange={(event) => onChange(event.target.value)} value={value}>{options.map((item) => <option key={item} value={item}>{item}</option>)}</select>;
}

function Add({ onClick, disabled }: { onClick: () => void; disabled?: boolean }) {
  return <button className="inline-flex items-center gap-2 rounded-lg border px-3 py-2 text-sm font-semibold disabled:opacity-50" disabled={disabled} onClick={onClick} type="button"><Plus className="h-4 w-4" />新增</button>;
}

function Tools({ onUp, onDown, onDelete, readOnly }: { onUp: () => void; onDown: () => void; onDelete: () => void; readOnly?: boolean }) {
  return <div className="flex gap-2"><button disabled={readOnly} onClick={onUp} type="button"><ArrowUp className="h-4 w-4" /></button><button disabled={readOnly} onClick={onDown} type="button"><ArrowDown className="h-4 w-4" /></button><button disabled={readOnly} onClick={() => window.confirm("确认删除？") && onDelete()} type="button"><Trash2 className="h-4 w-4 text-rose-600" /></button></div>;
}
