export function StatusBadge({ status }: { status: string }) {
  const ok = ["ok", "success", "completed", "enabled"].includes(status);
  const warning = ["warning", "running"].includes(status);
  return <span className={["rounded-full px-2.5 py-1 text-xs font-semibold", ok ? "bg-emerald-50 text-emerald-700" : warning ? "bg-amber-50 text-amber-700" : "bg-rose-50 text-rose-700"].join(" ")}>{status}</span>;
}
