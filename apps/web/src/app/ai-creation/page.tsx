"use client";

import { useState } from "react";
import { ArrowUp, Clock, Home, Image, Shirt, Sparkles, Video, WandSparkles } from "lucide-react";
import { AppShell } from "@/components/AppShell";

const creationCards = ["新中式茶室场景", "商品场景大片", "多场景详情页", "氛围灯光大片"];
const creationMenu = [
  { label: "首页", icon: Home },
  { label: "AI视频", icon: Video },
  { label: "AI生图", icon: Image },
  { label: "AI场景", icon: WandSparkles },
  { label: "AI试衣", icon: Shirt }
];

export default function AiCreationPage() {
  const [prompt, setPrompt] = useState("");
  const [notice, setNotice] = useState("");

  const handleSubmit = () => {
    setNotice("当前是 meizhaiseek v1.8，后续会接入生图、生视频和商品场景生成能力。");
  };

  return (
    <AppShell activeId="ai-creation" dark contentClassName="flex bg-[#0c0c10]">
      <aside className="hidden h-screen w-[180px] shrink-0 border-r border-white/10 bg-[#181818] px-6 py-10 text-white lg:block">
        <h1 className="mb-9 text-2xl font-bold">AI创作</h1>
        <div className="space-y-5">
          {creationMenu.map((item, index) => {
            const Icon = item.icon;
            const active = index === 0;

            return (
              <button
                className={[
                  "flex h-20 w-full flex-col items-center justify-center gap-2 rounded-xl text-sm font-semibold transition",
                  active ? "bg-violet-900/70 text-violet-100" : "text-slate-400 hover:bg-white/5 hover:text-white"
                ].join(" ")}
                key={item.label}
                type="button"
              >
                <Icon className="h-5 w-5" />
                {item.label}
              </button>
            );
          })}
        </div>
      </aside>

      <section className="min-h-screen flex-1 overflow-y-auto bg-[radial-gradient(circle_at_center,rgba(124,58,237,0.14),transparent_34%),radial-gradient(circle,rgba(255,255,255,0.09)_1px,transparent_1px)] bg-[length:100%_100%,18px_18px] px-8 py-12 text-white">
        <div className="mx-auto max-w-6xl">
          <div className="mb-11 text-center">
            <div className="mb-7 flex items-center justify-center gap-4">
              <span className="flex h-16 w-16 items-center justify-center rounded-full bg-gradient-to-br from-violet-400 to-cyan-300 shadow-soft">
                <Sparkles className="h-8 w-8 text-white" />
              </span>
              <span className="text-4xl font-bold">meizhaiseek</span>
            </div>
            <h2 className="text-5xl font-bold tracking-tight">
              开启你的{" "}
              <span className="bg-gradient-to-r from-violet-400 to-cyan-300 bg-clip-text text-transparent">
                AI创意生成
              </span>
            </h2>
          </div>

          <div className="mx-auto max-w-4xl rounded-2xl border border-white/10 bg-white/[0.06] p-5 shadow-soft backdrop-blur">
            <textarea
              className="h-36 w-full resize-none bg-transparent text-base text-white outline-none placeholder:text-slate-500"
              onChange={(event) => setPrompt(event.target.value)}
              placeholder="请输入提示词，描述想要生成的内容"
              value={prompt}
            />
            <div className="flex flex-wrap items-center justify-between gap-3 border-t border-white/10 pt-4">
              <div className="flex flex-wrap gap-2">
                {["文生视频", "seedance-2-0 NEW", "5s", "720p", "16:9"].map((item) => (
                  <button
                    className="rounded-lg bg-white/10 px-3 py-2 text-sm font-semibold text-slate-200 transition hover:bg-violet-700/60"
                    key={item}
                    type="button"
                  >
                    {item}
                  </button>
                ))}
              </div>
              <div className="flex items-center gap-3">
                <span className="text-sm font-semibold text-violet-300">-10</span>
                <button
                  aria-label="发送 AI 创作提示词"
                  className="flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-br from-violet-500 to-cyan-300 text-white transition hover:scale-105"
                  onClick={handleSubmit}
                  type="button"
                >
                  <ArrowUp className="h-5 w-5" />
                </button>
              </div>
            </div>
          </div>

          {notice ? <div className="mx-auto mt-5 max-w-4xl rounded-xl bg-violet-950/70 px-5 py-4 text-sm text-violet-100">{notice}</div> : null}

          <div className="mx-auto mt-10 max-w-4xl">
            <h3 className="mb-5 flex items-center gap-2 text-xl font-semibold">
              <Clock className="h-5 w-5 text-violet-300" />
              热门
            </h3>
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              {creationCards.map((card, index) => (
                <button
                  className="group h-44 overflow-hidden rounded-2xl bg-gradient-to-br from-violet-900 via-slate-800 to-cyan-900 p-4 text-left shadow-soft transition hover:-translate-y-1"
                  key={card}
                  type="button"
                >
                  <div className="h-full rounded-xl border border-white/10 bg-white/10 p-4">
                    <div className="text-sm text-slate-300">0{index + 1}</div>
                    <div className="mt-16 text-lg font-semibold text-white">{card}</div>
                  </div>
                </button>
              ))}
            </div>
          </div>
        </div>
      </section>
    </AppShell>
  );
}


