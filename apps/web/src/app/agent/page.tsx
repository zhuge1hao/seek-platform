"use client";

import { startTransition, useCallback, useEffect, useRef, useState } from "react";
import { Settings, Shield } from "lucide-react";
import { AdminConsolePanel } from "@/components/AdminConsolePanel";
import { AgentCard } from "@/components/AgentCard";
import { AgentConfigPanel } from "@/components/AgentConfigPanel";
import { AgentWorkspace } from "@/components/AgentWorkspace";
import { AppShell } from "@/components/AppShell";
import { ConversationMessages } from "@/components/ConversationMessages";
import { ConversationPanel } from "@/components/ConversationPanel";
import { QuickPrompts } from "@/components/QuickPrompts";
import { getStoredUser, type AuthUser } from "@/lib/auth";
import { findAgentByType, type AgentDefinition, type AgentToolId } from "@/lib/agents";
import { deleteConversation, getConversation, type AgentRunStatus, type Conversation, type ConversationSummary } from "@/lib/api";
import { useAgentConversations } from "@/hooks/useAgentConversations";
import { useAgentRunEvents } from "@/hooks/useAgentRunEvents";
import { useAgentRunPolling } from "@/hooks/useAgentRunPolling";
import { agentCards } from "@/lib/mockData";
import { markPerf } from "@/lib/perf";

const ACTIVE_CONVERSATION_KEY = "meizhaiseek_active_conversation_id";

function syncConversationUrl(conversationId?: string | null) {
  const nextUrl = conversationId ? `/agent?conversation_id=${encodeURIComponent(conversationId)}` : "/agent";
  if (`${window.location.pathname}${window.location.search}` !== nextUrl) window.history.replaceState(null, "", nextUrl);
}

const quickPromptAgentMap: Record<string, AgentToolId> = {
  "给我一些选款优化建议": "smart-selection",
  "一键拆解爆款主图": "hot-main-image-breakdown",
  "为我生成高转化的详情页策划稿": "detail-page-planning",
  "我的推广投产为什么上不去？": "promotion-analysis",
  "帮我找到行业必争蓝海词": "blue-ocean",
  "一键拆解爆款视频": "video-script-breakdown"
};

function runMessageContent(current: string, run: AgentRunStatus) {
  if (run.status === "failed") return run.error || "任务执行失败。";
  if (run.status === "cancelled") return "任务已取消。";
  if (run.status === "completed") return run.result?.answer || "任务执行完成";
  return current || run.current_step || "任务正在执行。";
}

export default function AgentPage() {
  const [selectedAgentId, setSelectedAgentId] = useState<AgentToolId | null>(null);
  const [inputValue, setInputValue] = useState("");
  const [conversations, setConversations] = useState<ConversationSummary[]>([]);
  const [activeConversationId, setActiveConversationId] = useState<string | null>(null);
  const [currentConversation, setCurrentConversation] = useState<Conversation | null>(null);
  const [currentRun, setCurrentRun] = useState<AgentRunStatus | null>(null);
  const [conversationLoading, setConversationLoading] = useState(true);
  const [detailLoading, setDetailLoading] = useState(false);
  const [conversationError, setConversationError] = useState("");
  const [conversationWarnings, setConversationWarnings] = useState<string[]>([]);
  const [isConfigOpen, setIsConfigOpen] = useState(false);
  const [isAdminOpen, setIsAdminOpen] = useState(false);
  const [currentUser, setCurrentUser] = useState<AuthUser | null>(null);
  const [configRefreshKey, setConfigRefreshKey] = useState(0);

  const activeRequestRef = useRef<AbortController | null>(null);
  const requestSeqRef = useRef(0);
  const lastLoadedConversationIdRef = useRef<string | null>(null);
  const loadingConversationIdRef = useRef<string | null>(null);
  const mountedRef = useRef(false);
  const loadConversationRef = useRef<(conversationId: string, options?: { force?: boolean }) => Promise<void>>(async () => undefined);
  const { data: conversationData, error: conversationsLoadError, mutate: mutateAgentConversations } = useAgentConversations();

  const refreshConversations = useCallback(async () => {
    const result = await mutateAgentConversations();
    const items = result?.conversations || [];
    setConversations(items);
    return items;
  }, [mutateAgentConversations]);

  useEffect(() => {
    if (conversationData?.conversations) setConversations(conversationData.conversations);
  }, [conversationData]);

  useEffect(() => {
    if (conversationsLoadError) setConversationError(conversationsLoadError instanceof Error ? conversationsLoadError.message : "聊天记录加载失败。");
  }, [conversationsLoadError]);

  const clearActiveConversation = useCallback((message = "") => {
    activeRequestRef.current?.abort();
    activeRequestRef.current = null;
    lastLoadedConversationIdRef.current = null;
    loadingConversationIdRef.current = null;
    localStorage.removeItem(ACTIVE_CONVERSATION_KEY);
    syncConversationUrl(null);
    setSelectedAgentId(null);
    setActiveConversationId(null);
    setInputValue("");
    setCurrentConversation(null);
    setCurrentRun(null);
    setDetailLoading(false);
    setConversationWarnings([]);
    setConversationError(message);
  }, []);

  const loadConversation = useCallback(async (conversationId: string, options: { force?: boolean } = {}) => {
    if (!conversationId) return;
    if (!options.force && (conversationId === lastLoadedConversationIdRef.current || conversationId === loadingConversationIdRef.current)) {
      localStorage.setItem(ACTIVE_CONVERSATION_KEY, conversationId);
      syncConversationUrl(conversationId);
      return;
    }

    activeRequestRef.current?.abort();
    const controller = new AbortController();
    activeRequestRef.current = controller;
    const requestSeq = requestSeqRef.current + 1;
    requestSeqRef.current = requestSeq;
    loadingConversationIdRef.current = conversationId;

    const endLoad = markPerf("agent.loadConversation", { conversation_id: conversationId });
    setActiveConversationId(conversationId);
    setDetailLoading(true);
    setConversationError("");
    setConversationWarnings([]);
    localStorage.setItem(ACTIVE_CONVERSATION_KEY, conversationId);
    syncConversationUrl(conversationId);

    try {
      const endFetch = markPerf("agent.fetchConversation", { conversation_id: conversationId });
      const detail = await getConversation(conversationId, controller.signal);
      endFetch();
      if (!mountedRef.current || requestSeq !== requestSeqRef.current) return;
      const conversation = detail.conversation;
      const endState = markPerf("agent.setConversationState", { conversation_id: conversation.conversation_id, messages: conversation.messages.length });
      startTransition(() => {
        setCurrentConversation(conversation);
        setCurrentRun(detail.latest_run);
        setConversationWarnings(detail.warnings || []);
        setSelectedAgentId(findAgentByType(conversation.agent_type)?.id || null);
        setInputValue(conversation.prompt || [...conversation.messages].reverse().find((message) => message.role === "user")?.content || "");
      });
      endState();
      lastLoadedConversationIdRef.current = conversation.conversation_id;
      endLoad();
    } catch (error) {
      if ((error as Error)?.name === "AbortError" || !mountedRef.current || requestSeq !== requestSeqRef.current) return;
      const message = error instanceof Error && error.message.includes("404") ? "该会话不存在或已被删除。" : error instanceof Error ? error.message : "会话加载失败。";
      clearActiveConversation(message);
    } finally {
      if (mountedRef.current && requestSeq === requestSeqRef.current) {
        loadingConversationIdRef.current = null;
        activeRequestRef.current = null;
        setDetailLoading(false);
        setConversationLoading(false);
      }
    }
  }, [clearActiveConversation]);

  useEffect(() => {
    loadConversationRef.current = loadConversation;
  }, [loadConversation]);

  useEffect(() => {
    mountedRef.current = true;
    setCurrentUser(getStoredUser());
    let active = true;
    const restore = async () => {
      try {
        await refreshConversations();
        if (!active) return;
        const queryId = new URLSearchParams(window.location.search).get("conversation_id");
        const storedId = localStorage.getItem(ACTIVE_CONVERSATION_KEY);
        const targetId = queryId || storedId;
        if (targetId) await loadConversationRef.current(targetId);
      } catch (error) {
        if (active) setConversationError(error instanceof Error ? error.message : "聊天记录加载失败。");
      } finally {
        if (active) setConversationLoading(false);
      }
    };
    void restore();
    return () => {
      active = false;
      mountedRef.current = false;
      activeRequestRef.current?.abort();
    };
  }, [refreshConversations]);

  const handleNewConversation = () => {
    clearActiveConversation();
  };

  const handleDeleteConversation = async (conversation: ConversationSummary) => {
    setConversationError("");
    try {
      await deleteConversation(conversation.conversation_id);
      if (conversation.conversation_id === currentConversation?.conversation_id) clearActiveConversation();
      await refreshConversations();
    } catch (error) {
      setConversationError(error instanceof Error ? error.message : "会话删除失败。");
    }
  };

  const handleAgentSelect = (agentId: AgentToolId) => { setSelectedAgentId(agentId); setCurrentRun(null); };
  const handlePopoverAgentSelect = (agent: AgentDefinition) => handleAgentSelect(agent.id);
  const handleQuickPromptSelect = (prompt: string) => {
    const nextAgentId = quickPromptAgentMap[prompt] ?? null;
    setSelectedAgentId(nextAgentId);
    setInputValue(nextAgentId === "video-script-breakdown" ? "" : prompt);
  };
  const handleSend = async () => {
    if (inputValue.trim()) setConversationError("请先选择一个智能体，再通过统一后端任务接口提交。");
  };

  const handleConversationChange = useCallback(async (conversationId: string) => {
    await loadConversationRef.current(conversationId, { force: true });
    await refreshConversations();
  }, [refreshConversations]);

  const handleRunChange = useCallback((run: AgentRunStatus) => {
    setCurrentRun(run);
    setConversations((items) => items.map((item) => item.conversation_id === run.conversation_id ? { ...item, latest_run_id: run.run_id, status: run.status, summary: run.error || run.result?.answer || item.summary } : item));
    setCurrentConversation((conversation) => {
      if (!conversation || conversation.conversation_id !== run.conversation_id) return conversation;
      return {
        ...conversation,
        latest_run_id: run.run_id,
        status: run.status,
        summary: run.error || run.result?.answer || conversation.summary,
        messages: conversation.messages.map((message) => message.run_id === run.run_id ? { ...message, content: runMessageContent(message.content, run), status: run.status, result: run.result, error: run.error, progress: run.progress, current_step: run.current_step, logs: run.logs } : message)
      };
    });
    if (["completed", "failed", "cancelled"].includes(run.status) && run.conversation_id) void refreshConversations();
  }, [refreshConversations]);

  const { pollingError, startPolling, stopPolling } = useAgentRunPolling(handleRunChange);
  const { eventsState, eventsError, startEvents, stopEvents } = useAgentRunEvents(handleRunChange);

  useEffect(() => {
    stopPolling();
    stopEvents();
    if (!currentRun?.run_id || ["completed", "failed", "cancelled"].includes(currentRun.status)) return;
    startEvents(currentRun.run_id, currentRun.status);
  }, [currentRun?.run_id, currentRun?.status, startEvents, stopEvents, stopPolling]);

  useEffect(() => {
    if (eventsState === "fallback") startPolling(currentRun?.run_id, currentRun?.status);
    else if (eventsState === "connected") stopPolling();
  }, [currentRun?.run_id, currentRun?.status, eventsState, startPolling, stopPolling]);

  const handleSelectConversation = useCallback((conversationId: string) => {
    if (conversationId === activeConversationId || conversationId === loadingConversationIdRef.current) return;
    void loadConversation(conversationId);
  }, [activeConversationId, loadConversation]);

  return (
    <AppShell activeId="agent" contentClassName="flex bg-[radial-gradient(circle_at_top,#f4e8ff_0%,transparent_35%),linear-gradient(135deg,#fafcff_0%,#f6f4ff_54%,#eef6ff_100%)]">
      <ConversationPanel
        canDelete={currentUser?.role ? currentUser.role !== "viewer" : false}
        collapsedStorageKey="meizhaiseek_agent_panel_collapsed"
        conversations={conversations}
        deleteDisabledMessage="当前账号为只读权限，无法删除对话。"
        error={conversationError || pollingError || eventsError}
        getDeleteConfirmMessage={(conversation) => conversation.status === "running" ? "该任务仍在执行，删除记录不会停止后台任务，是否继续？" : "确认删除该智能体对话记录吗？"}
        loading={conversationLoading}
        onDeleteConversation={handleDeleteConversation}
        onNewConversation={handleNewConversation}
        onSelectConversation={handleSelectConversation}
        selectedConversationId={activeConversationId || currentConversation?.conversation_id}
        title="AI 智能体"
      />
      <section className="min-h-screen min-w-0 flex-1 overflow-y-auto px-8 py-10">
        <div className="mx-auto flex min-h-[calc(100vh-80px)] max-w-5xl flex-col items-center justify-center">
          {currentUser?.role === "admin" ? <div className="mb-4 flex w-full justify-end gap-3">
            <button className="inline-flex items-center gap-2 rounded-full border border-slate-200 bg-white/90 px-4 py-2 text-sm font-semibold text-slate-700 shadow-sm" onClick={() => setIsAdminOpen(true)} type="button"><Shield className="h-4 w-4" />后台管理</button>
            <button className="inline-flex items-center gap-2 rounded-full border border-violet-200 bg-white/90 px-4 py-2 text-sm font-semibold text-violet-700 shadow-sm" onClick={() => setIsConfigOpen(true)} type="button"><Settings className="h-4 w-4" />智能体设置</button>
          </div> : null}
          <div className="mb-8 text-center"><p className="text-sm font-medium text-violet-700">AI 智能经营助手</p><h2 className="mt-3 text-4xl font-semibold tracking-tight text-slate-950">你好，meizhaiseek</h2></div>
          {conversationWarnings.length ? <div className="mb-4 w-full max-w-[880px] rounded-2xl bg-amber-50 px-4 py-3 text-sm text-amber-700">{conversationWarnings.join("；")}</div> : null}
          {detailLoading ? <div className="mb-6 w-full max-w-[880px] rounded-2xl border border-violet-100 bg-white/80 px-4 py-3 text-sm text-slate-500">正在切换会话...</div> : null}
          {currentConversation && !detailLoading ? <ConversationMessages messages={currentConversation.messages} /> : !detailLoading ? <div className="mb-9 grid w-full max-w-3xl grid-cols-2 gap-4 sm:grid-cols-4">{agentCards.map((card, index) => <AgentCard active={selectedAgentId === card.id} index={index} key={card.id} onClick={() => handleAgentSelect(card.id)} title={card.title} />)}</div> : null}
          <AgentWorkspace configRefreshKey={configRefreshKey} inputValue={inputValue} isSending={false} onAgentSelect={handlePopoverAgentSelect} onInputChange={setInputValue} onSend={handleSend} selectedAgentId={selectedAgentId} conversationId={currentConversation?.conversation_id || null} initialRun={currentRun} onConversationChange={(id) => void handleConversationChange(id)} onRunChange={handleRunChange} />
          {!selectedAgentId ? <QuickPrompts onSelect={handleQuickPromptSelect} /> : null}
        </div>
      </section>
      <AgentConfigPanel onClose={() => setIsConfigOpen(false)} onSaved={() => setConfigRefreshKey((key) => key + 1)} open={isConfigOpen} />
      <AdminConsolePanel onChanged={() => setConfigRefreshKey((key) => key + 1)} onClose={() => setIsAdminOpen(false)} open={isAdminOpen} />
    </AppShell>
  );
}

