"use client";

import { useEffect, useState } from "react";
import { Download, Play } from "lucide-react";
import { ErrorState } from "@/components/ui/ErrorState";
import { cleanDataset, downloadArtifact, type AgentRunFile, type DatasetProfile } from "@/lib/api";

const defaults = { dedupe_by_link: true, min_total_price: 10, min_unit_price: 15, min_sales_amount: 1000, min_cost_ratio: 5 };

export function DataCleaningPanel({ datasetId, initialProfile, initialFiles = [], readOnly, onCleaned }: { datasetId: string; initialProfile?: DatasetProfile | null; initialFiles?: AgentRunFile[]; readOnly: boolean; onCleaned: (profile: DatasetProfile, files: AgentRunFile[]) => void }) {
  const [rules, setRules] = useState(defaults);
  const [profile, setProfile] = useState<DatasetProfile | null>(initialProfile || null);
  const [files, setFiles] = useState(initialFiles);
  const [cleaning, setCleaning] = useState(false);
  const [error, setError] = useState("");
  useEffect(() => { setProfile(initialProfile || null); setFiles(initialFiles); setError(""); }, [datasetId, initialProfile, initialFiles]);
  const clean = async () => { setCleaning(true); setError(""); try { const result = await cleanDataset(datasetId, rules); setProfile(result.profile); setFiles(result.files); onCleaned(result.profile, result.files); } catch (err) { setError(err instanceof Error ? err.message : "数据清洗失败。"); } finally { setCleaning(false); } };
  const numberRule = (key: keyof typeof defaults, label: string) => <label className="text-sm font-semibold text-slate-700">{label}<input className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 font-normal" disabled={readOnly} min="0" onChange={(e) => setRules((current) => ({ ...current, [key]: Number(e.target.value) }))} type="number" value={String(rules[key])} /></label>;
  return <section className="space-y-4">
    <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
      <label className="flex items-center gap-2 rounded-xl border border-slate-200 px-3 py-3 text-sm font-semibold"><input checked={rules.dedupe_by_link} disabled={readOnly} onChange={(e) => setRules((current) => ({ ...current, dedupe_by_link: e.target.checked }))} type="checkbox" />链接去重</label>
      {numberRule("min_total_price", "最低总价")}{numberRule("min_unit_price", "最低单条价")}{numberRule("min_sales_amount", "最低成交金额")}{numberRule("min_cost_ratio", "最低费比")}
    </div>
    {!readOnly ? <button className="inline-flex items-center gap-2 rounded-xl bg-violet-600 px-4 py-2.5 text-sm font-semibold text-white disabled:opacity-50" disabled={cleaning} onClick={() => void clean()} type="button"><Play className="h-4 w-4" />{cleaning ? "正在清洗..." : "开始清洗"}</button> : <p className="rounded-xl bg-sky-50 px-4 py-3 text-sm text-sky-700">当前账号为只读权限，无法执行数据清洗。</p>}
    {error ? <ErrorState message={error} /> : null}
    {profile ? <>
      <div className="grid gap-3 sm:grid-cols-4">{[["原始条数", profile.raw_count], ["有效条数", profile.valid_count], ["剔除条数", profile.excluded_count], ["有效率", `${profile.valid_rate ?? 0}%`]].map(([label, value]) => <div className="rounded-xl bg-slate-50 p-4" key={String(label)}><p className="text-xs text-slate-500">{label}</p><p className="mt-1 text-xl font-bold text-slate-900">{value}</p></div>)}</div>
      <div className="grid gap-4 lg:grid-cols-2"><StatTable title="剔除原因统计" values={profile.excluded_reason_counts || {}} /><StatTable title="价格带分布" values={profile.price_band_distribution || {}} /></div>
      <div><h4 className="mb-2 text-sm font-bold text-slate-800">低费比高成交 TOP10</h4><div className="max-h-72 overflow-auto rounded-xl border border-slate-200"><table className="min-w-[680px] w-full text-sm"><thead className="sticky top-0 bg-slate-50"><tr>{["店铺", "标题", "成交金额", "费比", "成交效益比"].map((item) => <th className="px-3 py-2 text-left" key={item}>{item}</th>)}</tr></thead><tbody>{(profile.top_low_cost_high_sales || []).map((row, index) => <tr className="border-t" key={index}><td className="px-3 py-2">{String(row.shop_name || "-")}</td><td className="max-w-64 truncate px-3 py-2">{String(row.title || "-")}</td><td className="px-3 py-2">{String(row.sales_amount ?? "-")}</td><td className="px-3 py-2">{String(row.cost_ratio ?? "-")}</td><td className="px-3 py-2">{String(row.efficiency_ratio ?? "-")}</td></tr>)}</tbody></table></div></div>
      {profile.warnings?.length ? <div className="rounded-xl bg-amber-50 p-4 text-sm text-amber-700"><p className="font-bold">计算提示</p>{profile.warnings.map((item) => <p className="mt-1" key={item}>{item}</p>)}</div> : null}
    </> : null}
    {files.length ? <div className="space-y-2"><h4 className="text-sm font-bold text-slate-800">结果文件</h4>{files.map((file) => <div className="flex flex-wrap items-center justify-between gap-2 rounded-xl border border-slate-200 px-3 py-2" key={file.path}><div className="min-w-0"><p className="truncate text-sm font-semibold">{file.name}</p><p className="truncate text-xs text-slate-400">{file.path}</p></div>{file.download_url ? <button className="inline-flex items-center gap-1 rounded-lg border px-3 py-2 text-xs font-semibold" onClick={() => void downloadArtifact(file.download_url!, file.name)} type="button"><Download className="h-3.5 w-3.5" />下载</button> : null}</div>)}</div> : null}
  </section>;
}

function StatTable({ title, values }: { title: string; values: Record<string, number> }) { return <div><h4 className="mb-2 text-sm font-bold text-slate-800">{title}</h4><div className="max-h-56 overflow-auto rounded-xl border border-slate-200"><table className="w-full text-sm"><tbody>{Object.entries(values).map(([key, value]) => <tr className="border-b last:border-0" key={key}><td className="px-3 py-2">{key}</td><td className="px-3 py-2 text-right font-semibold">{value}</td></tr>)}</tbody></table></div></div>; }
