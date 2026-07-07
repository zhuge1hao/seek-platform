"use client";

import { Component, type ErrorInfo, type ReactNode } from "react";

type Props = { children: ReactNode; label?: string };
type State = { error: Error | null; errorId: string };

function newErrorId() {
  return `err_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 8)}`;
}

export class AppErrorBoundary extends Component<Props, State> {
  state: State = { error: null, errorId: "" };

  static getDerivedStateFromError(error: Error): State {
    return { error, errorId: newErrorId() };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    if (process.env.NODE_ENV !== "production") console.error("App render error", error, info);
  }

  render() {
    if (!this.state.error) return this.props.children;
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-100 px-6">
        <div className="w-full max-w-lg rounded-2xl border border-rose-100 bg-white p-6 text-center shadow-soft">
          <p className="text-sm font-semibold text-rose-600">{this.props.label || "页面渲染异常"}</p>
          <h1 className="mt-3 text-2xl font-bold text-slate-950">页面暂时无法显示</h1>
          <p className="mt-3 text-sm leading-6 text-slate-500">错误编号：{this.state.errorId}</p>
          <div className="mt-5 flex flex-wrap justify-center gap-3">
            <button className="rounded-xl bg-slate-950 px-4 py-2 text-sm font-semibold text-white" onClick={() => window.location.reload()} type="button">重新加载</button>
            <button className="rounded-xl border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-700" onClick={() => window.location.assign("/")} type="button">返回首页</button>
            <button className="rounded-xl border border-violet-200 px-4 py-2 text-sm font-semibold text-violet-700" onClick={() => void navigator.clipboard?.writeText(this.state.errorId)} type="button">复制错误编号</button>
          </div>
        </div>
      </div>
    );
  }
}
