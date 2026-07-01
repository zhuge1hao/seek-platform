"use client";

import { useState } from "react";
import { BarChart3, CalendarDays, ChevronDown, Info, Sparkles } from "lucide-react";
import { AppShell } from "@/components/AppShell";

const metrics = [
  ["销售金额", "1,255,600"],
  ["客单价", "491.30"],
  ["销售人数", "25,556"],
  ["转化率", "1.13%"],
  ["访问人数", "2,255,560"],
  ["搜索访问人数", "1,832,400"],
  ["加购率", "4.11%"],
  ["收藏率", "2.87%"]
];

export default function CompetitionDiagnosisPage() {
  const [notice, setNotice] = useState("");

  return (
    <AppShell activeId="competition-diagnosis" contentClassName="bg-[radial-gradient(circle_at_top,#eefaff_0%,transparent_30%),linear-gradient(135deg,#fff_0%,#f8fbff_50%,#edf7ff_100%)]">
      <section className="min-h-screen overflow-y-auto px-8 py-16">
        <div className="mx-auto max-w-7xl">
          <div className="mb-12 text-center">
            <h1 className="flex items-center justify-center gap-3 text-4xl font-bold tracking-tight text-slate-950">
              <BarChart3 className="h-10 w-10 text-violet-500" />
              AI驱动的竞品深度分析
            </h1>
            <p className="mt-5 text-lg text-slate-500">多维分析市场格局，精准拆解竞品策略，助力业绩爆发</p>
          </div>

          <div className="grid gap-8 xl:grid-cols-[1fr_1.08fr]">
            <section className="rounded-[24px] border border-slate-200 bg-white p-6 shadow-soft">
              <div className="mb-8 flex flex-wrap gap-3 rounded-2xl bg-slate-50 p-2">
                {["销售数据", "搜索词数据", "流量渠道数据"].map((tab, index) => (
                  <button
                    className={[
                      "rounded-xl px-4 py-2 text-sm font-semibold transition",
                      index === 0 ? "bg-white text-blue-600 shadow-sm" : "text-slate-500 hover:bg-white hover:text-slate-900"
                    ].join(" ")}
                    key={tab}
                    type="button"
                  >
                    {tab}
                  </button>
                ))}
              </div>

              <h2 className="mb-6 border-l-4 border-blue-500 pl-3 text-lg font-bold text-slate-950">数据内容</h2>

              <div className="grid gap-4 sm:grid-cols-2">
                {metrics.map(([label, value]) => (
                  <div className="rounded-2xl border border-blue-100 bg-gradient-to-br from-white to-blue-50 p-5 text-center shadow-sm" key={label}>
                    <div className="mb-3 flex items-center justify-center gap-2 text-sm font-semibold text-blue-500">
                      {label}
                      <Info className="h-4 w-4" />
                    </div>
                    <div className="text-3xl font-bold text-blue-500">{value}</div>
                  </div>
                ))}
              </div>
            </section>

            <section className="rounded-[24px] border border-slate-200 bg-white p-7 shadow-soft">
              <div className="mb-7 flex items-center justify-between">
                <h2 className="flex items-center gap-2 text-xl font-bold text-slate-950">
                  <Sparkles className="h-5 w-5 text-violet-500" />
                  生成分析报告
                </h2>
                <button className="flex items-center gap-1 text-sm font-medium text-slate-400 transition hover:text-violet-600" type="button">
                  使用说明
                  <Info className="h-4 w-4" />
                </button>
              </div>

              <div className="space-y-5">
                <label className="block">
                  <span className="mb-2 block text-sm font-semibold text-slate-700">
                    <span className="text-rose-500">*</span> 分析时间范围
                  </span>
                  <div className="flex gap-3">
                    <div className="flex min-h-12 flex-1 items-center justify-between rounded-xl bg-slate-100 px-4 text-slate-700">
                      2026-05-15 <span className="text-slate-400">—</span> 2026-06-13
                      <CalendarDays className="h-5 w-5 text-slate-400" />
                    </div>
                    <button className="rounded-xl bg-violet-500 px-5 text-sm font-semibold text-white transition hover:bg-violet-600" type="button">
                      近30天
                    </button>
                  </div>
                </label>

                <div className="grid gap-5 md:grid-cols-2">
                  <label className="block">
                    <span className="mb-2 block text-sm font-semibold text-slate-700">
                      <span className="text-rose-500">*</span> 本店名称
                    </span>
                    <button className="flex min-h-12 w-full items-center justify-between rounded-xl bg-slate-100 px-4 text-left text-slate-400" type="button">
                      请选择店铺
                      <ChevronDown className="h-5 w-5" />
                    </button>
                  </label>

                  <label className="block">
                    <span className="mb-2 block text-sm font-semibold text-slate-700">
                      <span className="text-rose-500">*</span> 本品商品ID
                    </span>
                    <input
                      className="min-h-12 w-full rounded-xl border-0 bg-slate-100 px-4 text-slate-700 outline-none placeholder:text-slate-400"
                      placeholder="请输入想要分析的店铺商品ID"
                    />
                  </label>
                </div>

                <label className="block">
                  <span className="mb-2 block text-sm font-semibold text-slate-700">
                    <span className="text-rose-500">*</span> 竞品商品ID，需要填满5个
                  </span>
                  <div className="space-y-3">
                    {["竞品ID一", "竞品ID二", "竞品ID三", "竞品ID四", "竞品ID五"].map((placeholder) => (
                      <input
                        className="min-h-12 w-full rounded-xl border-0 bg-slate-100 px-4 text-slate-700 outline-none placeholder:text-slate-400"
                        key={placeholder}
                        placeholder={placeholder}
                      />
                    ))}
                  </div>
                </label>

                <button
                  className="min-h-12 w-full rounded-2xl bg-gradient-to-r from-violet-400 to-fuchsia-300 text-sm font-bold text-white shadow-sm transition hover:from-violet-500 hover:to-fuchsia-400"
                  onClick={() =>
                    setNotice("当前是 meizhaiseek v1.6.5，后续会接入商品数据、竞品数据和自动报告生成能力。")
                  }
                  type="button"
                >
                  生成报告（消耗298蜜豆）
                </button>
              </div>

              {notice ? <p className="mt-5 rounded-xl bg-violet-50 px-4 py-3 text-sm font-medium text-violet-700">{notice}</p> : null}
            </section>
          </div>
        </div>
      </section>
    </AppShell>
  );
}

