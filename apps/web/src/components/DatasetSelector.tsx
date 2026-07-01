"use client";

import { useEffect } from "react";
import { Database } from "lucide-react";
import { EmptyState } from "@/components/ui/EmptyState";
import { ErrorState } from "@/components/ui/ErrorState";
import { LoadingState } from "@/components/ui/LoadingState";
import { useDatasets } from "@/hooks/useDatasets";

export const DATASET_AGENT_TYPES = new Set(["competitor_analysis", "smart_selection", "promotion_analysis", "crowd_diagnosis", "region_diagnosis"]);

export function DatasetSelector({ selectedIds, onChange, refreshKey = 0, readOnly = false }: { selectedIds: string[]; onChange: (ids: string[]) => void; refreshKey?: number; readOnly?: boolean }) {
  const { data, error, isLoading, mutate } = useDatasets({ status: "cleaned", limit: 50 });
  const items = data?.datasets || [];

  useEffect(() => { void mutate(); }, [refreshKey, mutate]);

  if (isLoading) return <LoadingState label="正在加载已清洗数据集..." />;
  if (error) return <ErrorState message={error instanceof Error ? error.message : "数据集加载失败。"} />;
  if (!items.length) return <EmptyState title="暂无已清洗数据集" description="打开数据清洗中心创建并清洗 Excel/CSV。" />;

  return (
    <div className="grid gap-2 sm:grid-cols-2">
      {items.map((item) => {
        const checked = selectedIds.includes(item.dataset_id);
        return (
          <label className={`flex min-w-0 items-start gap-3 rounded-xl border p-3 ${checked ? "border-violet-300 bg-violet-50" : "border-slate-200 bg-white"}`} key={item.dataset_id}>
            <input checked={checked} className="mt-1" disabled={readOnly} onChange={() => onChange(checked ? selectedIds.filter((id) => id !== item.dataset_id) : [...selectedIds, item.dataset_id])} type="checkbox" />
            <Database className="mt-0.5 h-4 w-4 shrink-0 text-violet-600" />
            <span className="min-w-0">
              <span className="block truncate text-sm font-semibold text-slate-800">{item.name}</span>
              <span className="text-xs text-slate-500">有效 {item.profile?.valid_count ?? 0} / 原始 {item.profile?.raw_count ?? item.row_count}</span>
            </span>
          </label>
        );
      })}
    </div>
  );
}
