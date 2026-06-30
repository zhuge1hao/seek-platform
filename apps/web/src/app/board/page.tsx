"use client";

import { ArrowUp, Bot, Plus, SlidersHorizontal, Sparkles } from "lucide-react";
import { AppShell } from "@/components/AppShell";

const quickStarts = ["上传参考图", "创建商品视觉画板", "生成详情页灵感", "生成主图方向"];

export default function BoardPage() {
  return (
    <AppShell activeId="board" dark contentClassName="bg-[#0b0b0d]">
      <section className="min-h-screen overflow-y-auto rounded-[24px] border border-white/10 bg-[radial-gradient(circle_at_top,rgba(236,72,153,0.16),transparent_30%),radial-gradient(circle,rgba(255,255,255,0.08)_1px,transparent_1px)] bg-[length:100%_100%,26px_26px] px-8 py-12 text-white">
        <div className="mx-auto max-w-6xl">
          <div className="mb-12 text-center">
            <div className="mb-7 flex items-center justify-center gap-4">
              <span className="flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-pink-600 to-violet-600 shadow-soft">
                <Sparkles className="h-8 w-8 text-white" />
              </span>
              <span className="text-4xl font-bold">meizhaiseek</span>
            </div>
            <h1 className="text-5xl font-bold">
              开启你的{" "}
              <span className="bg-gradient-to-r from-rose-500 to-fuchsia-400 bg-clip-text text-transparent">
                无限画板创作
              </span>
            </h1>
          </div>

          <div className="mx-auto max-w-5xl rounded-[28px] border border-white/10 bg-gradient-to-br from-white/12 to-white/5 p-6 shadow-soft">
            <div className="flex min-h-52 gap-6">
              <button
                className="flex h-36 w-24 shrink-0 rotate-[-5deg] flex-col items-center justify-center gap-5 rounded-2xl border border-white/10 bg-white/10 text-slate-200 transition hover:rotate-0 hover:bg-violet-900/50"
                type="button"
              >
                <span className="rounded-full bg-slate-950 px-2 py-1 text-xs font-semibold">0/9</span>
                <Plus className="h-7 w-7" />
              </button>
              <div className="flex flex-1 items-start pt-4 text-xl font-semibold text-slate-300">
                智能参考，上传参考，输入文字，创意无限可能
              </div>
            </div>

            <div className="flex flex-wrap items-center justify-between gap-4">
              <div className="flex gap-3">
                <button className="flex h-11 items-center gap-2 rounded-xl border border-violet-500 bg-violet-800/60 px-4 text-sm font-semibold text-violet-100 transition hover:bg-violet-700" type="button">
                  <Bot className="h-4 w-4" />
                  Agent 模式
                </button>
                <button className="flex h-11 items-center gap-2 rounded-xl border border-white/10 bg-white/10 px-4 text-sm font-semibold text-slate-200 transition hover:bg-white/15" type="button">
                  <SlidersHorizontal className="h-4 w-4" />
                  自定义
                </button>
              </div>
              <button
                aria-label="发送画板创作请求"
                className="flex h-12 w-12 items-center justify-center rounded-2xl bg-white/10 text-white transition hover:bg-violet-700"
                type="button"
              >
                <ArrowUp className="h-5 w-5" />
              </button>
            </div>
          </div>

          <div className="mx-auto mt-12 max-w-5xl">
            <h2 className="mb-6 flex items-center gap-3 text-2xl font-bold">
              <Sparkles className="h-6 w-6 text-fuchsia-400" />
              快速开始
            </h2>
            <div className="grid gap-5 md:grid-cols-4">
              {quickStarts.map((item, index) => (
                <button
                  className="h-40 rounded-2xl border border-white/10 bg-gradient-to-br from-violet-950 to-slate-900 p-5 text-left shadow-soft transition hover:-translate-y-1 hover:border-fuchsia-400/50"
                  key={item}
                  type="button"
                >
                  <div className="mb-10 flex h-10 w-10 items-center justify-center rounded-xl bg-white/10 text-fuchsia-300">
                    {index + 1}
                  </div>
                  <div className="text-lg font-semibold">{item}</div>
                </button>
              ))}
            </div>
          </div>
        </div>
      </section>
    </AppShell>
  );
}
