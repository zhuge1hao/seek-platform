"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { getAgentRunSummary, type AgentRunSummaryDetail } from "@/lib/api";
import { markPerf } from "@/lib/perf";

const TERMINAL = new Set(["completed", "failed", "cancelled"]);

export function useAgentRunPolling(onRunChange?: (run: AgentRunSummaryDetail) => void) {
  const [pollingError, setPollingError] = useState("");
  const timerRef = useRef<number | null>(null);
  const abortRef = useRef<AbortController | null>(null);
  const activeRunIdRef = useRef<string | null>(null);
  const failureCountRef = useRef(0);
  const onRunChangeRef = useRef(onRunChange);

  useEffect(() => {
    onRunChangeRef.current = onRunChange;
  }, [onRunChange]);

  const stopPolling = useCallback(() => {
    if (timerRef.current) window.clearTimeout(timerRef.current);
    timerRef.current = null;
    abortRef.current?.abort();
    abortRef.current = null;
    activeRunIdRef.current = null;
    failureCountRef.current = 0;
  }, []);

  const pollOnce = useCallback(async (runId: string) => {
    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;
    const end = markPerf("agent.pollRun", { run_id: runId });
    const next = await getAgentRunSummary(runId, controller.signal);
    end();
    if (activeRunIdRef.current !== runId) return;
    failureCountRef.current = 0;
    setPollingError("");
    onRunChangeRef.current?.(next);
    if (TERMINAL.has(next.status)) {
      stopPolling();
      return;
    }
    timerRef.current = window.setTimeout(() => void pollOnce(runId).catch(handleError), 2000);
  }, [stopPolling]);

  const handleError = useCallback((error: unknown) => {
    if ((error as Error)?.name === "AbortError") return;
    failureCountRef.current += 1;
    if (failureCountRef.current >= 3) {
      stopPolling();
      setPollingError(error instanceof Error ? error.message : "任务状态轮询失败，请稍后刷新。");
      return;
    }
    const runId = activeRunIdRef.current;
    if (runId) timerRef.current = window.setTimeout(() => void pollOnce(runId).catch(handleError), 3000);
  }, [pollOnce, stopPolling]);

  const startPolling = useCallback((runId?: string | null, status?: string | null) => {
    stopPolling();
    if (!runId || TERMINAL.has(status || "")) return;
    activeRunIdRef.current = runId;
    void pollOnce(runId).catch(handleError);
  }, [handleError, pollOnce, stopPolling]);

  useEffect(() => stopPolling, [stopPolling]);

  return { pollingError, startPolling, stopPolling };
}
