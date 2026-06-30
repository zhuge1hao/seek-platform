"use client";

import { useEffect, useState } from "react";
import { Save } from "lucide-react";
import { ErrorState } from "@/components/ui/ErrorState";
import { saveDatasetFieldMapping, type DatasetPreview, type MappingTemplate } from "@/lib/api";

export function FieldMappingPanel({ datasetId, preview, initialMapping, templates, readOnly, onSaved }: { datasetId: string; preview: DatasetPreview; initialMapping: Record<string, string>; templates: MappingTemplate[]; readOnly: boolean; onSaved: (mapping: Record<string, string>) => void }) {
  const [mapping, setMapping] = useState<Record<string, string>>(initialMapping);
  const [templateName, setTemplateName] = useState("");
  const [saveTemplate, setSaveTemplate] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  useEffect(() => setMapping(Object.keys(initialMapping).length ? initialMapping : preview.suggested_mapping || {}), [initialMapping, preview]);

  const applyTemplate = (templateId: string) => {
    const template = templates.find((item) => item.template_id === templateId);
    if (template) setMapping(template.mapping);
  };
  const save = async () => {
    setSaving(true); setError(""); setNotice("");
    try { const result = await saveDatasetFieldMapping(datasetId, { mapping, save_as_template: saveTemplate, template_name: saveTemplate ? templateName : undefined }); setMapping(result.mapping); onSaved(result.mapping); setNotice("字段映射已保存。"); }
    catch (err) { setError(err instanceof Error ? err.message : "字段映射保存失败。"); }
    finally { setSaving(false); }
  };
  return <section className="space-y-4">
    <div className="flex flex-wrap items-end gap-3">
      <label className="min-w-52 flex-1 text-sm font-semibold text-slate-700">应用用户映射模板<select className="mt-1 w-full rounded-xl border border-slate-200 bg-white px-3 py-2 font-normal" disabled={readOnly} onChange={(e) => applyTemplate(e.target.value)} defaultValue=""><option value="">请选择模板</option>{templates.map((item) => <option key={item.template_id} value={item.template_id}>{item.name}</option>)}</select></label>
      <button className="rounded-xl border border-violet-200 px-3 py-2 text-sm font-semibold text-violet-700 disabled:opacity-50" disabled={readOnly} onClick={() => setMapping(preview.suggested_mapping || {})} type="button">恢复建议映射</button>
    </div>
    <div className="max-w-full overflow-x-auto rounded-xl border border-slate-200">
      <table className="min-w-[680px] w-full text-left text-sm"><thead className="bg-slate-50 text-slate-600"><tr><th className="px-4 py-3">标准字段</th><th className="px-4 py-3">中文名</th><th className="px-4 py-3">原始列</th></tr></thead><tbody>
        {preview.detected_fields.map((field) => <tr className="border-t border-slate-100" key={field.key}><td className="px-4 py-2 font-mono text-xs">{field.key}</td><td className="px-4 py-2">{field.name}</td><td className="px-4 py-2"><select className="w-full rounded-lg border border-slate-200 px-2 py-2" disabled={readOnly} onChange={(e) => setMapping((current) => ({ ...current, [field.key]: e.target.value }))} value={mapping[field.key] || ""}><option value="">不映射</option>{preview.columns.map((column) => <option key={column} value={column}>{column}</option>)}</select></td></tr>)}
      </tbody></table>
    </div>
    {!readOnly ? <div className="flex flex-wrap items-center gap-3 rounded-xl bg-slate-50 p-3"><label className="flex items-center gap-2 text-sm"><input checked={saveTemplate} onChange={(e) => setSaveTemplate(e.target.checked)} type="checkbox" />保存为用户模板</label>{saveTemplate ? <input className="min-w-48 flex-1 rounded-xl border border-slate-200 px-3 py-2 text-sm" onChange={(e) => setTemplateName(e.target.value)} placeholder="模板名称" value={templateName} /> : null}<button className="inline-flex items-center gap-2 rounded-xl bg-violet-600 px-4 py-2 text-sm font-semibold text-white disabled:opacity-50" disabled={saving || (saveTemplate && !templateName.trim())} onClick={() => void save()} type="button"><Save className="h-4 w-4" />{saving ? "保存中..." : "保存字段映射"}</button></div> : null}
    {error ? <ErrorState message={error} /> : null}{notice ? <p className="rounded-xl bg-emerald-50 px-4 py-3 text-sm text-emerald-700">{notice}</p> : null}
  </section>;
}
