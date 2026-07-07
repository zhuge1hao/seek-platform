"use client";

import { Component, type ErrorInfo, type ReactNode } from "react";

type Props = { children: ReactNode; label?: string };
type State = { error: Error | null; errorId: string };

function newErrorId() {
  return `panel_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 8)}`;
}

export class ResultPanelErrorBoundary extends Component<Props, State> {
  state: State = { error: null, errorId: "" };

  static getDerivedStateFromError(error: Error): State {
    return { error, errorId: newErrorId() };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    if (process.env.NODE_ENV !== "production") console.error("Result panel render error", error, info);
  }

  render() {
    if (!this.state.error) return this.props.children;
    return (
      <div className="rounded-2xl border border-rose-100 bg-rose-50 p-4 text-sm text-rose-700">
        <p className="font-semibold">{this.props.label || "结果区显示失败"}</p>
        <p className="mt-2">错误编号：{this.state.errorId}</p>
        <div className="mt-3 flex flex-wrap gap-2">
          <button className="rounded-lg bg-white px-3 py-1.5 font-semibold text-rose-700" onClick={() => window.location.reload()} type="button">重新加载</button>
          <button className="rounded-lg bg-white px-3 py-1.5 font-semibold text-rose-700" onClick={() => void navigator.clipboard?.writeText(this.state.errorId)} type="button">复制错误编号</button>
        </div>
      </div>
    );
  }
}
