"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { streamAgentRunEvents, type AgentRunSummaryDetail } from "@/lib/api";

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

  const startEvents = useCallback((runId?: string | null, status?: string | null) => {
    stopEvents();
    if (!runId || TERMINAL.has(status || "")) return;
    const controller = new AbortController();
    abortRef.current = controller;
    activeRunIdRef.current = runId;
    setEventsState("connecting");
    setEventsError("");

    void (async () => {
      await streamAgentRunEvents(runId, {
        onConnected: () => setEventsState("connected"),
        onRunChange: (next) => {
          if (activeRunIdRef.current === runId) onRunChangeRef.current?.(next);
        },
        onTerminal: () => stopEvents(),
        onFallback: (error) => {
          setEventsError(error.message || "任务状态推送连接失败，已切换轮询。");
          setEventsState("fallback");
        },
      }, controller.signal);
    })();
  }, [stopEvents]);

  useEffect(() => stopEvents, [stopEvents]);

  return { eventsState, eventsError, startEvents, stopEvents };
}
