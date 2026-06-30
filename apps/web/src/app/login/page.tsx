"use client";

import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { isAuthenticated, login, verifyAuth } from "@/lib/auth";

export default function LoginPage() {
  const router = useRouter();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (isAuthenticated()) {
      verifyAuth().then(() => router.replace("/agent")).catch(() => undefined);
    }
  }, [router]);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const nextUsername = username.trim();
    if (!nextUsername) {
      setError("请输入用户名");
      return;
    }
    if (!password) {
      setError("请输入密码");
      return;
    }
    setIsSubmitting(true);
    setError("");
    try {
      await login(nextUsername, password);
      router.replace("/agent");
    } catch (loginError) {
      setError(loginError instanceof Error ? loginError.message : "账号或密码错误。");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <main className="flex min-h-screen items-center justify-center bg-[radial-gradient(circle_at_top_left,#f3e8ff,transparent_34%),linear-gradient(135deg,#ffffff_0%,#f8fafc_48%,#eef2ff_100%)] px-6">
      <section className="w-full max-w-md rounded-[32px] border border-white/80 bg-white/85 p-10 shadow-soft backdrop-blur">
        <div className="mx-auto mb-6 flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-violet-500 to-rose-400 text-2xl font-bold text-white shadow-soft">
          M
        </div>
        <div className="text-center">
          <p className="text-lg font-semibold tracking-tight text-violet-700">meizhaiseek</p>
          <h1 className="mt-3 text-3xl font-semibold tracking-tight text-slate-950">登录 meizhaiseek</h1>
          <p className="mt-3 text-base text-slate-600">电商 AI 智能分析平台</p>
        </div>

        <form className="mt-8 space-y-4" onSubmit={handleSubmit}>
          <label className="block text-sm font-medium text-slate-700">
            用户名
            <input
              className="mt-2 h-12 w-full rounded-2xl border border-slate-200 bg-white px-4 text-sm text-slate-950 outline-none transition focus:border-violet-300 focus:ring-4 focus:ring-violet-100"
              onChange={(event) => {
                setUsername(event.target.value);
                setError("");
              }}
              placeholder="请输入用户名"
              value={username}
            />
          </label>
          <label className="block text-sm font-medium text-slate-700">
            密码
            <input
              className="mt-2 h-12 w-full rounded-2xl border border-slate-200 bg-white px-4 text-sm text-slate-950 outline-none transition focus:border-violet-300 focus:ring-4 focus:ring-violet-100"
              onChange={(event) => {
                setPassword(event.target.value);
                setError("");
              }}
              placeholder="请输入密码"
              type="password"
              value={password}
            />
          </label>

          {error ? <p className="rounded-2xl bg-rose-50 px-4 py-3 text-sm font-medium text-rose-600">{error}</p> : null}

          <button className="h-12 w-full rounded-2xl bg-slate-950 text-base font-semibold text-white shadow-sm transition hover:bg-violet-700 disabled:cursor-not-allowed disabled:opacity-60" disabled={isSubmitting} type="submit">
            {isSubmitting ? "正在登录..." : "登录"}
          </button>
        </form>

        <div className="mt-6 rounded-2xl bg-violet-50 px-4 py-3 text-sm leading-6 text-violet-700">
          <p>默认管理员账号：admin</p>
          <p>初始密码：admin123</p>
        </div>
      </section>
    </main>
  );
}
