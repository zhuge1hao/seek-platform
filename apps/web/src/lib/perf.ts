type PerfMeta = Record<string, string | number | boolean | null | undefined>;

export function markPerf(label: string, meta: PerfMeta = {}): () => void {
  if (process.env.NODE_ENV !== "development") return () => undefined;
  const startedAt = performance.now();
  return () => {
    const duration = performance.now() - startedAt;
    if (duration < 80) return;
    const safeMeta = Object.fromEntries(Object.entries(meta).filter(([key]) => !/token|payload|result|debug/i.test(key)));
    console.debug(`[perf] ${label} ${Math.round(duration)}ms`, safeMeta);
  };
}
