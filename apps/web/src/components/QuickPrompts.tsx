"use client";

import { quickPrompts } from "@/lib/mockData";

type QuickPromptsProps = {
  onSelect: (prompt: string) => void;
  prompts?: readonly string[];
};

export function QuickPrompts({ onSelect, prompts = quickPrompts }: QuickPromptsProps) {
  return (
    <div className="mx-auto mt-5 flex w-full max-w-3xl flex-wrap justify-center gap-2">
      {prompts.map((prompt) => (
        <button
          className="rounded-full border border-white/80 bg-white/80 px-4 py-2 text-sm text-slate-700 shadow-sm backdrop-blur transition hover:border-violet-200 hover:bg-violet-50 hover:text-violet-700"
          key={prompt}
          onClick={() => onSelect(prompt)}
          type="button"
        >
          {prompt}
        </button>
      ))}
    </div>
  );
}
