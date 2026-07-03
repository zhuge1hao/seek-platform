"use client";

import { ChangeEvent, useEffect, useRef, useState } from "react";
import { Database, FileSpreadsheet, Trash2, Upload } from "lucide-react";
import { DataCleaningPanel } from "@/components/DataCleaningPanel";
import { FieldMappingPanel } from "@/components/FieldMappingPanel";
import { EmptyState } from "@/components/ui/EmptyState";
import { ErrorState } from "@/components/ui/ErrorState";
import { LoadingState } from "@/components/ui/LoadingState";
import { SafeDrawer } from "@/components/ui/SafeDrawer";
import { useDatasetMappingTemplates, useDatasets } from "@/hooks/useDatasets";
import { useFiles } from "@/hooks/useFiles";
import { createDatasetFromFile, deleteDataset, getDatasetFieldMapping, getDatasetFiles, getDatasetPreview, getDatasetProfile, uploadGenericFile, type AgentRunFile, type DatasetPreview, type DatasetProfile, type DatasetSummary, type GenericUploadResponse, type MappingTemplate } from "@/lib/api";

export function DatasetPanel({ open, onClose, readOnly, onChanged }: { open: boolean; onClose: () => void; readOnly: boolean; onChanged: () => void }) {
  const [datasets, setDatasets] = useState<DatasetSummary[]>([]);
  const [files, setFiles] = useState<GenericUploadResponse[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [preview, setPreview] = useState<DatasetPreview | null>(null);
  const [mapping, setMapping] = useState<Record<string, string>>({});
  const [templates, setTemplates] = useState<MappingTemplate[]>([]);
  const [profile, setProfile] = useState<DatasetProfile | null>(null);
  const [resultFiles, setResultFiles] = useState<AgentRunFile[]>([]);
  const [sourceFileId, setSourceFileId] = useState("");
  const [name, setName] = useState("");
  const [loading, setLoading] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  const { data: datasetData, error: datasetError, isLoading: datasetsLoading, mutate: mutateDatasets } = useDatasets({}, open);
  const { data: fileData, error: fileError, mutate: mutateFiles } = useFiles("xlsx,xls,csv", 50, open);
  const { data: templateData, mutate: mutateTemplates } = useDatasetMappingTemplates(open);
  useEffect(() => { setDatasets(Array.isArray(datasetData?.datasets) ? datasetData.datasets : []); }, [datasetData]);
  useEffect(() => { setFiles(Array.isArray(fileData?.files) ? fileData.files : []); }, [fileData]);
  useEffect(() => { setTemplates(Array.isArray(templateData?.templates) ? templateData.templates : []); }, [templateData]);
  useEffect(() => { setLoading(Boolean(open && datasetsLoading)); }, [open, datasetsLoading]);
  useEffect(() => { const err = datasetError || fileError; if (err) setError(err instanceof Error ? err.message : "数据清洗中心加载失败。"); }, [datasetError, fileError]);
  const refresh = async () => { setError(""); const [datasetResult, fileResult, templateResult] = await Promise.all([mutateDatasets(), mutateFiles(), mutateTemplates()]); setDatasets(Array.isArray(datasetResult?.datasets) ? datasetResult.datasets : []); setFiles(Array.isArray(fileResult?.files) ? fileResult.files : []); setTemplates(Array.isArray(templateResult?.templates) ? templateResult.templates : []); };
  const selectDataset = async (datasetId: string) => { setSelectedId(datasetId); setLoading(true); setError(""); try { const [p, m] = await Promise.all([getDatasetPreview(datasetId), getDatasetFieldMapping(datasetId)]); setPreview(p); setMapping(Object.keys(m.mapping || {}).length ? m.mapping : m.suggested_mapping || p.suggested_mapping || {}); const dataset = datasets.find((item) => item.dataset_id === datasetId); if (dataset?.status === "cleaned") { const [prof, output] = await Promise.all([getDatasetProfile(datasetId), getDatasetFiles(datasetId)]); setProfile(prof); setResultFiles(output.files || []); } else { setProfile(null); setResultFiles([]); } } catch (err) { setError(err instanceof Error ? err.message : "数据集详情加载失败。"); } finally { setLoading(false); } };
  const upload = async (event: ChangeEvent<HTMLInputElement>) => { const file = event.target.files?.[0]; event.target.value = ""; if (!file) return; setBusy(true); setError(""); try { const record = await uploadGenericFile(file); setSourceFileId(record.file_id); setName(file.name.replace(/\.(xlsx|xls|csv)$/i, "")); await refresh(); } catch (err) { setError(err instanceof Error ? err.message : "文件上传失败。"); } finally { setBusy(false); } };
  const create = async () => { if (!sourceFileId) return; setBusy(true); setError(""); try { const created = await createDatasetFromFile(sourceFileId, name.trim() || undefined); await refresh(); await selectDataset(created.dataset_id); onChanged(); } catch (err) { setError(err instanceof Error ? err.message : "数据集创建失败。"); } finally { setBusy(false); } };
  const remove = async (datasetId: string) => { if (!window.confirm("确认删除这个数据集吗？原始文件不会被删除。")) return; setBusy(true); try { await deleteDataset(datasetId); if (selectedId === datasetId) { setSelectedId(null); setPreview(null); } await refresh(); onChanged(); } catch (err) { setError(err instanceof Error ? err.message : "数据集删除失败。"); } finally { setBusy(false); } };
  const selected = datasets.find((item) => item.dataset_id === selectedId);
  const sidebar = <><div className="shrink-0 p-4"><p className="text-xs font-semibold text-violet-700">meizhaiseek v1.7.1</p><h3 className="mt-1 font-bold">数据集</h3></div><div className="min-h-0 flex-1 overflow-y-auto px-3 pb-4">{datasets.map((item) => <button className={`mb-2 w-full rounded-xl p-3 text-left ${selectedId === item.dataset_id ? "bg-violet-100 text-violet-800" : "bg-white text-slate-700"}`} key={item.dataset_id} onClick={() => void selectDataset(item.dataset_id)} type="button"><span className="block truncate text-sm font-semibold">{item.name}</span><span className="mt-1 block text-xs">{item.status} · {item.row_count} 行</span></button>)}{!datasets.length && !loading ? <p className="px-2 text-xs text-slate-400">暂无数据集</p> : null}</div></>;
  return <SafeDrawer open={open} title={selected?.name || "Excel 字段映射与数据清洗中心"} eyebrow="meizhaiseek v1.7.1" onClose={onClose} sidebar={sidebar} maxWidth="max-w-7xl">
    {error ? <div className="mb-4"><ErrorState message={error} onRetry={() => void refresh()} /></div> : null}
    {!readOnly ? <section className="mb-6 rounded-2xl border border-violet-100 bg-violet-50/50 p-4"><h3 className="font-bold text-slate-900">创建数据集</h3><div className="mt-3 flex flex-wrap items-end gap-3"><input accept=".xlsx,.xls,.csv" className="hidden" onChange={upload} ref={inputRef} type="file" /><button className="inline-flex items-center gap-2 rounded-xl border border-violet-200 bg-white px-4 py-2 text-sm font-semibold text-violet-700 disabled:opacity-50" disabled={busy} onClick={() => inputRef.current?.click()} type="button"><Upload className="h-4 w-4" />上传 Excel/CSV/XLS</button><label className="min-w-52 flex-1 text-xs font-semibold text-slate-600">选择已上传文件<select className="mt-1 w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm font-normal" onChange={(e) => setSourceFileId(e.target.value)} value={sourceFileId}><option value="">请选择文件</option>{files.map((file) => <option key={file.file_id} value={file.file_id}>{file.filename}</option>)}</select></label><label className="min-w-44 flex-1 text-xs font-semibold text-slate-600">数据集名称<input className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm font-normal" onChange={(e) => setName(e.target.value)} value={name} /></label><button className="rounded-xl bg-violet-600 px-4 py-2 text-sm font-semibold text-white disabled:opacity-50" disabled={busy || !sourceFileId} onClick={() => void create()} type="button">{busy ? "处理中..." : "创建 Dataset"}</button></div></section> : <p className="mb-4 rounded-xl bg-sky-50 px-4 py-3 text-sm text-sky-700">当前账号为只读权限，无法创建或清洗数据集。</p>}
    {loading ? <LoadingState label="正在读取数据集..." /> : selected && preview ? <div className="space-y-8">
      <section><div className="mb-3 flex items-center justify-between"><div><h3 className="font-bold text-slate-900">原始数据预览</h3><p className="text-xs text-slate-500">共 {preview.row_count} 行，预览 {preview.preview_count} 行</p></div>{!readOnly ? <button className="inline-flex items-center gap-1 text-sm text-rose-600" disabled={busy} onClick={() => void remove(selected.dataset_id)} type="button"><Trash2 className="h-4 w-4" />删除</button> : null}</div><div className="max-h-80 overflow-auto rounded-xl border border-slate-200"><table className="min-w-max w-full text-sm"><thead className="sticky top-0 bg-slate-50"><tr>{preview.columns.map((column) => <th className="whitespace-nowrap px-3 py-2 text-left" key={column}>{column}</th>)}</tr></thead><tbody>{preview.rows.map((row, index) => <tr className="border-t" key={index}>{preview.columns.map((column) => <td className="max-w-64 truncate px-3 py-2" key={column}>{String(row[column] ?? "")}</td>)}</tr>)}</tbody></table></div></section>
      <section><h3 className="mb-3 font-bold text-slate-900">字段映射</h3><FieldMappingPanel datasetId={selected.dataset_id} initialMapping={mapping} onSaved={(value) => { setMapping(value); void refresh(); }} preview={preview} readOnly={readOnly} templates={templates} /></section>
      <section><h3 className="mb-3 font-bold text-slate-900">数据清洗</h3><DataCleaningPanel datasetId={selected.dataset_id} initialFiles={resultFiles} initialProfile={profile} onCleaned={(nextProfile, nextFiles) => { setProfile(nextProfile); setResultFiles(nextFiles); void refresh(); onChanged(); }} readOnly={readOnly} /></section>
    </div> : <EmptyState title="选择一个数据集" description="从左侧选择数据集，或先上传表格创建 Dataset。" />}
  </SafeDrawer>;
}

