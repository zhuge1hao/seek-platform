import { Loader2 } from "lucide-react";

export function LoadingState({ label = "正在加载...", fullScreen = false }: { label?: string; fullScreen?: boolean }) {
  return (
    <div className={["flex items-center justify-center gap-3 text-sm text-slate-500", fullScreen ? "min-h-screen bg-slate-50" : "min-h-28"].join(" ")}>
      <Loader2 className="h-5 w-5 animate-spin text-violet-600" />
      {label}
    </div>
  );
}
