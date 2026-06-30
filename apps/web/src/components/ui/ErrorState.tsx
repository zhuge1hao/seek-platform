import { AlertCircle } from "lucide-react";

export function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div className="rounded-2xl border border-rose-100 bg-rose-50 p-4 text-sm text-rose-700">
      <div className="flex items-start gap-2">
        <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
        <p className="leading-6">{message}</p>
      </div>
      {onRetry ? <button className="mt-3 rounded-xl bg-white px-3 py-2 font-semibold shadow-sm" onClick={onRetry} type="button">重试</button> : null}
    </div>
  );
}
