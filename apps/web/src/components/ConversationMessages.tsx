import { Bot, UserRound } from "lucide-react";
import type { ConversationMessage } from "@/lib/api";

const statusLabels: Record<string, string> = {
  submitted: "已提交", running: "执行中", completed: "已完成", failed: "失败", cancelled: "已取消"
};

export function ConversationMessages({ messages }: { messages: ConversationMessage[] }) {
  if (!messages.length) return null;
  return (
    <div className="mb-6 max-h-[360px] w-full max-w-[880px] space-y-3 overflow-y-auto rounded-[24px] border border-violet-100 bg-white/80 p-4 shadow-soft">
      {messages.map((message) => (
        <div className={["flex gap-3 rounded-2xl p-4", message.role === "user" ? "bg-slate-50" : "bg-violet-50/70"].join(" ")} key={message.message_id}>
          <div className={["flex h-8 w-8 shrink-0 items-center justify-center rounded-full", message.role === "user" ? "bg-slate-200 text-slate-600" : "bg-violet-200 text-violet-700"].join(" ")}>
            {message.role === "user" ? <UserRound className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
          </div>
          <div className="min-w-0 flex-1">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <p className="text-xs font-semibold text-slate-500">{message.role === "user" ? "你" : "meizhaiseek 2.0"}</p>
              <span className="text-xs font-medium text-slate-400">{statusLabels[message.status] || message.status}</span>
            </div>
            <p className="mt-2 whitespace-pre-wrap break-words text-sm leading-6 text-slate-700">{message.content}</p>
            {message.error ? <p className="mt-2 rounded-xl bg-rose-50 px-3 py-2 text-sm text-rose-600">{message.error}</p> : null}
          </div>
        </div>
      ))}
    </div>
  );
}
