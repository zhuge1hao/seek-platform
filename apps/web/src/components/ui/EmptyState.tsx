export function EmptyState({ title = "暂无数据", description }: { title?: string; description?: string }) {
  return (
    <div className="flex min-h-32 flex-col items-center justify-center rounded-2xl border border-dashed border-slate-200 bg-slate-50 px-5 text-center">
      <p className="text-sm font-semibold text-slate-700">{title}</p>
      {description ? <p className="mt-1 text-xs text-slate-400">{description}</p> : null}
    </div>
  );
}
