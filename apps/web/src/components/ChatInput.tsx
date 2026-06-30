"use client";

import { ArrowUp, Bot, Link2, WandSparkles } from "lucide-react";

type ChatInputProps = {
  value: string;
  onChange: (value: string) => void;
  onSend: () => void;
  isSending?: boolean;
  showAgentButton?: boolean;
  showToolButtons?: boolean;
  selectedAgentId?: string | null;
  selectedAgentName?: string;
  onOpenAgentSelector?: () => void;
};

export function ChatInput({ value, onChange, onSend, isSending = false, showAgentButton = true, showToolButtons = true, selectedAgentId = null, selectedAgentName, onOpenAgentSelector }: ChatInputProps) {
  return (
    <div className="mx-auto w-full max-w-3xl rounded-[28px] border border-white/90 bg-white p-4 shadow-soft">
      <textarea
        className="h-28 w-full resize-none border-0 bg-transparent px-2 py-1 text-base leading-7 text-slate-900 outline-none placeholder:text-slate-400"
        onChange={(event) => onChange(event.target.value)}
        onKeyDown={(event) => {
          if (event.key === "Enter" && !event.shiftKey) {
            event.preventDefault();
            onSend();
          }
        }}
        placeholder="请输入内容..."
        value={value}
      />

      <div className="flex items-center justify-between gap-3 pt-3">
        <div className="flex flex-wrap items-center gap-2">
          {showAgentButton ? (
            <button
              className={["flex h-9 items-center gap-2 rounded-full border px-3 text-sm font-medium transition", selectedAgentId ? "border-violet-200 bg-violet-50 text-violet-700" : "border-slate-200 text-slate-700 hover:border-violet-200 hover:bg-violet-50 hover:text-violet-700"].join(" ")}
              onClick={onOpenAgentSelector}
              type="button"
            >
              <Bot className="h-4 w-4" />
              {selectedAgentName || "智能体"}
            </button>
          ) : null}
          {showToolButtons ? <>
            <button className="flex h-9 items-center gap-2 rounded-full border border-slate-200 px-3 text-sm font-medium text-slate-700 transition hover:border-violet-200 hover:bg-violet-50 hover:text-violet-700" type="button">
              <WandSparkles className="h-4 w-4" />
              技能
            </button>
            <button className="flex h-9 items-center gap-2 rounded-full border border-slate-200 px-3 text-sm font-medium text-slate-700 transition hover:border-violet-200 hover:bg-violet-50 hover:text-violet-700" type="button">
              <Link2 className="h-4 w-4" />
              链接
            </button>
          </> : null}
        </div>

        <div className="flex items-center gap-3">
          <span className="hidden text-sm font-medium text-slate-500 sm:inline">meizhaiseek 2.0</span>
          <button
            aria-label="发送"
            className="flex h-10 w-10 items-center justify-center rounded-full bg-slate-950 text-white shadow-sm transition hover:bg-violet-700 disabled:cursor-not-allowed disabled:bg-slate-300"
            disabled={isSending || value.trim().length === 0}
            onClick={onSend}
            type="button"
          >
            <ArrowUp className="h-5 w-5" />
          </button>
        </div>
      </div>
    </div>
  );
}
