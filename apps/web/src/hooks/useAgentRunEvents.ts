"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { StreamHttpError, streamAgentRunEvents, type AgentRunSummaryDetail } from "@/lib/api";

const TERMINAL = new Set(["completed", "failed", "cancelled"]);
const NON_RETRYABLE_STATUS = new Set([401, 403, 404]);
const RETRY_DELAYS = [1000, 2000, 4000, 8000, 16000, 30000];

type State = "idle" | "connecting" | "connected" | "fallback";

function retryDelay(attempt: number) {
  const base = RETRY_DELAYS[Math.min(attempt, RETRY_DELAYS.length - 1)];
  const jitter = Math.floor(Math.random() * Math.min(1000, base * 0.25));
  return Math.min(30000, base + jitter);
}

export function useAgentRunEvents(onRunChange?: (run: AgentRunSummaryDetail) => void) {
  const [eventsState, setEventsState] = useState<State>("idle");
  const [eventsError, setEventsError] = useState("");
  const abortRef = useRef<AbortController | null>(null);
  const timerRef = useRef<number | null>(null);
  const activeRunIdRef = useRef<string | null>(null);
  const activeStatusRef = useRef<string | null>(null);
  const retryAttemptRef = useRef(0);
  const onRunChangeRef = useRef(onRunChange);

  useEffect(() => {
    onRunChangeRef.current = onRunChange;
  }, [onRunChange]);

  const stopEvents = useCallback(() => {
    if (timerRef.current) window.clearTimeout(timerRef.current);
    timerRef.current = null;
    abortRef.current?.abort();
    abortRef.current = null;
    activeRunIdRef.current = null;
    activeStatusRef.current = null;
    retryAttemptRef.current = 0;
    setEventsState("idle");
  }, []);

  const connect = useCallback((runId: string) => {
    if (activeRunIdRef.current !== runId || TERMINAL.has(activeStatusRef.current || "")) return;
    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;
    setEventsState(retryAttemptRef.current === 0 ? "connecting" : "fallback");

    void streamAgentRunEvents(runId, {
      onConnected: () => {
        retryAttemptRef.current = 0;
        setEventsError("");
        setEventsState("connected");
      },
      onRunChange: (next) => {
        if (activeRunIdRef.current !== runId) return;
        activeStatusRef.current = next.status;
        onRunChangeRef.current?.(next);
      },
      onTerminal: () => stopEvents(),
      onFallback: (error) => {
        if (activeRunIdRef.current !== runId) return;
        const status = error instanceof StreamHttpError ? error.status : undefined;
        setEventsError(error.message || "SSE connection failed; polling fallback is active.");
        setEventsState("fallback");
        if (status && NON_RETRYABLE_STATUS.has(status)) return;
        const delay = retryDelay(retryAttemptRef.current);
        retryAttemptRef.current += 1;
        if (timerRef.current) window.clearTimeout(timerRef.current);
        timerRef.current = window.setTimeout(() => connect(runId), delay);
      },
    }, controller.signal);
  }, [stopEvents]);

  const startEvents = useCallback((runId?: string | null, status?: string | null) => {
    stopEvents();
    if (!runId || TERMINAL.has(status || "")) return;
    activeRunIdRef.current = runId;
    activeStatusRef.current = status || null;
    retryAttemptRef.current = 0;
    setEventsError("");
    connect(runId);
  }, [connect, stopEvents]);

  useEffect(() => {
    const retryNow = () => {
      const runId = activeRunIdRef.current;
      if (!runId || eventsState !== "fallback" || TERMINAL.has(activeStatusRef.current || "")) return;
      if (timerRef.current) window.clearTimeout(timerRef.current);
      retryAttemptRef.current = 0;
      connect(runId);
    };
    window.addEventListener("online", retryNow);
    return () => window.removeEventListener("online", retryNow);
  }, [connect, eventsState]);

  useEffect(() => stopEvents, [stopEvents]);

  return { eventsState, eventsError, startEvents, stopEvents };
}
