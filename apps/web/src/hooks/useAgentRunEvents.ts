"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { API_BASE_URL, type AgentRunSummaryDetail } from "@/lib/api";
import { clearAuthSession, getAuthToken } from "@/lib/auth";

const TERMINAL = new Set(["completed", "failed", "cancelled"]);

type State = "idle" | "connecting" | "connected" | "fallback";

export function useAgentRunEvents(onRunChange?: (run: AgentRunSummaryDetail) => void) {
  const [eventsState, setEventsState] = useState<State>("idle");
  const [eventsError, setEventsError] = useState("");
  const abortRef = useRef<AbortController | null>(null);
  const activeRunIdRef = useRef<string | null>(null);
  const onRunChangeRef = useRef(onRunChange);

  useEffect(() => {
    onRunChangeRef.current = onRunChange;
  }, [onRunChange]);

  const stopEvents = useCallback(() => {
    abortRef.current?.abort();
    abortRef.current = null;
    activeRunIdRef.current = null;
    setEventsState("idle");
  }, []);

  const handlePayload = useCallback((runId: string, raw: string) => {
    if (!raw.trim()) return;
    const data = raw.split("\n").filter((line) => line.startsWith("data:")).map((line) => line.slice(5).trim()).join("\n");
    if (!data) return;
    const next = JSON.parse(data) as AgentRunSummaryDetail;
    if (activeRunIdRef.current !== runId) return;
    onRunChangeRef.current?.(next);
    if (TERMINAL.has(next.status)) stopEvents();
  }, [stopEvents]);

  const startEvents = useCallback((runId?: string | null, status?: string | null) => {
    stopEvents();
    if (!runId || TERMINAL.has(status || "")) return;
    const token = getAuthToken();
    if (!token) {
      setEventsState("fallback");
      return;
    }
    const controller = new AbortController();
    abortRef.current = controller;
    activeRunIdRef.current = runId;
    setEventsState("connecting");
    setEventsError("");

    void (async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/api/agent-runs/${encodeURIComponent(runId)}/events`, {
          headers: { Authorization: `Bearer ${token}` },
          signal: controller.signal,
        });
        if (response.status === 401 || response.status === 403) clearAuthSession();
        if (!response.ok || !response.body) throw new Error(`SSE ${response.status}`);
        setEventsState("connected");
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";
        while (activeRunIdRef.current === runId) {
          const { value, done } = await reader.read();
          if (done) break;
          buffer += decoder.decode(value, { stream: true });
          const chunks = buffer.split("\n\n");
          buffer = chunks.pop() || "";
          chunks.forEach((chunk) => handlePayload(runId, chunk));
        }
      } catch (error) {
        if ((error as Error)?.name === "AbortError") return;
        setEventsError(error instanceof Error ? error.message : "任务状态推送连接失败，已切换轮询。");
        setEventsState("fallback");
      }
    })();
  }, [handlePayload, stopEvents]);

  useEffect(() => stopEvents, [stopEvents]);

  return { eventsState, eventsError, startEvents, stopEvents };
}
