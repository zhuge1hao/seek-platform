"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { AlertTriangle, CheckCircle2, ChevronDown, Clipboard, Database, RotateCcw, Square } from "lucide-react";
import { AppShell } from "@/components/AppShell";
import { ChatInput } from "@/components/ChatInput";
import { ConversationPanel } from "@/components/ConversationPanel";
import { KnowledgeBasePanel } from "@/components/KnowledgeBasePanel";
import { QuickPrompts } from "@/components/QuickPrompts";
import { ResultPanelErrorBoundary } from "@/components/ResultPanelErrorBoundary";
import { getStoredUser, type AuthUser } from "@/lib/auth";
import { chatQuickPrompts } from "@/lib/mockData";
import { useQAConversations } from "@/hooks/useQAConversations";
import {
  deleteQAConversation,
  getQAConversation,
  qaChat,
  streamQAChat,
  type ConversationSummary,
  type QAConversationSummary,
  type QAConversation,
  type QAConversationMessage,
  type QASource
} from "@/lib/api";

const ACTIVE_QA_CONVERSATION_KEY = "meizhaiseek_active_qa_conversation_id";

function replaceChatUrl(nextUrl: string) {
  if (`${window.location.pathname}${window.location.search}` !== nextUrl) window.history.replaceState(null, "", nextUrl);
}

type ChatMessage = QAConversationMessage & { error?: string; loading_note?: string };

function mapQASummaries(items: QAConversationSummary[]): ConversationSummary[] {
  return items.map((item) => ({
    conversation_id: item.conversation_id,
    title: item.title,
    agent_type: "qa_chat",
    agent_name: "AI 对话",
    created_at: item.updated_at,
    updated_at: item.updated_at,
    latest_run_id: null,
    status: item.status,
    summary: `${item.message_count} 条消息`,
    is_archived: false
  }));
}

function SourceList({ sources }: { sources?: QASource[] }) {
  const [open, setOpen] = useState(false);
  if (!sources?.length) return null;
  return (
    <div className="mt-3 rounded-2xl border border-sky-100 bg-sky-50/70">
      <button className="flex w-full items-center justify-between px-3 py-2 text-sm font-semibold text-sky-800" onClick={() => setOpen((value) => !value)} type="button">
        已参考本地知识库 {sources.length} 条内容
        <ChevronDown className={["h-4 w-4 transition", open ? "rotate-180" : ""].join(" ")} />
      </button>
      {open ? <div className="max-h-64 space-y-2 overflow-y-auto border-t border-sky-100 p-3">
        {sources.map((source) => <div className="rounded-xl bg-white p-3 text-left text-xs text-slate-600" key={source.chunk_id}>
          <div className="flex flex-wrap items-center justify-between gap-2">
            <span className="font-semibold text-slate-900">{source.title || "本地知识库"}</span>
            <span className="text-sky-700">score {Number(source.score || 0).toFixed(2)}</span>
          </div>
          <p className="mt-2 whitespace-pre-wrap break-words leading-5">{source.content_preview || source.content}</p>
        </div>)}
      </div> : null}
    </div>
  );
}

function MessageList({ messages, onCopy, onRegenerate }: { messages: ChatMessage[]; onCopy: (content: string) => void; onRegenerate: () => void }) {
  if (!messages.length) return null;
  return (
    <div className="mx-auto mb-6 max-h-[54vh] w-full max-w-3xl space-y-3 overflow-y-auto rounded-[28px] border border-white/80 bg-white/70 p-4 text-left shadow-soft">
      {messages.map((message, index) => {
        const isAssistant = message.role === "assistant";
        const isStreaming = message.status === "streaming";
        return (
          <div className={["rounded-2xl p-4", message.role === "user" ? "bg-slate-50" : message.status === "failed" ? "bg-rose-50" : "bg-violet-50/80"].join(" ")} key={message.message_id}>
            <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
              <p className="text-xs font-semibold text-slate-500">{message.role === "user" ? "你" : "meizhaiseek 2.0"}</p>
              <div className="flex items-center gap-2">
                {isStreaming ? <span className="text-xs text-violet-600">正在生成...</span> : null}
                {message.status === "completed" ? <span className="inline-flex items-center gap-1 text-xs text-emerald-600"><CheckCircle2 className="h-3 w-3" />已完成</span> : null}
                {message.status === "failed" ? <span className="text-xs text-rose-600">失败</span> : null}
                {message.status === "stopped" ? <span className="text-xs text-amber-600">已停止</span> : null}
              </div>
            </div>
            {message.loading_note ? <p className="mb-2 text-sm text-violet-700">{message.loading_note}</p> : null}
            <p className="whitespace-pre-wrap break-words text-sm leading-7 text-slate-700">{message.content || (isStreaming ? "meizhaiseek 2.0 正在生成..." : "")}</p>
            {message.warnings?.length ? <div className="mt-3 rounded-xl bg-amber-50 px-3 py-2 text-sm text-amber-700"><AlertTriangle className="mr-1 inline h-4 w-4" />{message.warnings.join("；")}</div> : null}
            {message.error ? <div className="mt-3 rounded-xl bg-rose-50 px-3 py-2 text-sm text-rose-700">{message.error}</div> : null}
            <SourceList sources={message.sources} />
            {isAssistant && message.content ? <div className="mt-3 flex flex-wrap gap-2">
              <button className="inline-flex items-center gap-1 rounded-lg border border-violet-100 bg-white px-2.5 py-1.5 text-xs font-medium text-violet-700 hover:bg-violet-50" onClick={() => onCopy(message.content)} type="button">
                <Clipboard className="h-3.5 w-3.5" />复制回答
              </button>
              {index === messages.length - 1 ? <button className="inline-flex items-center gap-1 rounded-lg border border-violet-100 bg-white px-2.5 py-1.5 text-xs font-medium text-violet-700 hover:bg-violet-50" onClick={onRegenerate} type="button">
                <RotateCcw className="h-3.5 w-3.5" />重新生成
              </button> : null}
            </div> : null}
          </div>
        );
      })}
    </div>
  );
}

export default function ChatPage() {
  const [inputValue, setInputValue] = useState("");
  const [conversations, setConversations] = useState<ConversationSummary[]>([]);
  const [currentConversation, setCurrentConversation] = useState<QAConversation | null>(null);
  const [activeConversationId, setActiveConversationId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(true);
  const [isSending, setIsSending] = useState(false);
  const [knowledgeOpen, setKnowledgeOpen] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [currentUser, setCurrentUser] = useState<AuthUser | null>(null);
  const abortRef = useRef<AbortController | null>(null);
  const selectConversationRef = useRef<(conversationId: string) => Promise<void>>(async () => undefined);
  const { data: qaConversationData, error: qaConversationError, mutate: mutateQAConversations } = useQAConversations();

  const qaSummaries = useMemo(() => conversations, [conversations]);

  const refreshConversations = useCallback(async () => {
    const result = await mutateQAConversations();
    const mapped = mapQASummaries(result?.conversations || []);
    setConversations(mapped);
    return mapped;
  }, [mutateQAConversations]);

  useEffect(() => {
    if (qaConversationData?.conversations) setConversations(mapQASummaries(qaConversationData.conversations));
  }, [qaConversationData]);

  useEffect(() => {
    if (qaConversationError) setError(qaConversationError instanceof Error ? qaConversationError.message : "AI 对话加载失败。");
  }, [qaConversationError]);

  const selectConversation = useCallback(async (conversationId: string) => {
    if (conversationId === activeConversationId) {
      localStorage.setItem(ACTIVE_QA_CONVERSATION_KEY, conversationId);
      replaceChatUrl(`/chat?conversation_id=${encodeURIComponent(conversationId)}`);
      return;
    }
    setError("");
    const detail = await getQAConversation(conversationId);
    setCurrentConversation(detail.conversation);
    setActiveConversationId(detail.conversation.conversation_id);
    setMessages(detail.conversation.messages);
    localStorage.setItem(ACTIVE_QA_CONVERSATION_KEY, detail.conversation.conversation_id);
    replaceChatUrl(`/chat?conversation_id=${encodeURIComponent(detail.conversation.conversation_id)}`);
  }, [activeConversationId]);

  useEffect(() => {
    selectConversationRef.current = selectConversation;
  }, [selectConversation]);

  useEffect(() => {
    setCurrentUser(getStoredUser());
    let active = true;
    const restore = async () => {
      try {
        await refreshConversations();
        if (!active) return;
        const queryId = new URLSearchParams(window.location.search).get("conversation_id");
        const storedId = localStorage.getItem(ACTIVE_QA_CONVERSATION_KEY);
        const targetId = queryId || storedId;
        if (targetId) await selectConversationRef.current(targetId);
      } catch (restoreError) {
        if (active) setError(restoreError instanceof Error ? restoreError.message : "AI 对话加载失败。");
      } finally {
        if (active) setLoading(false);
      }
    };
    void restore();
    return () => {
      active = false;
      abortRef.current?.abort();
    };
  }, [refreshConversations]);

  const handleNewConversation = () => {
    abortRef.current?.abort();
    localStorage.removeItem(ACTIVE_QA_CONVERSATION_KEY);
    setCurrentConversation(null);
    setActiveConversationId(null);
    setMessages([]);
    setInputValue("");
    setError("");
    replaceChatUrl("/chat");
  };

  const handleDeleteConversation = async (conversation: ConversationSummary) => {
    setError("");
    try {
      await deleteQAConversation(conversation.conversation_id);
      if (conversation.conversation_id === activeConversationId) handleNewConversation();
      await refreshConversations();
    } catch (deleteError) {
      setError(deleteError instanceof Error ? deleteError.message : "对话删除失败。");
    }
  };

  const fallbackNonStream = async (question: string, conversationId: string | null) => {
    const result = await qaChat({ conversation_id: conversationId, question, use_rag: true, top_k: 5 });
    localStorage.setItem(ACTIVE_QA_CONVERSATION_KEY, result.conversation_id);
    setActiveConversationId(result.conversation_id);
    replaceChatUrl(`/chat?conversation_id=${encodeURIComponent(result.conversation_id)}`);
    await refreshConversations();
    await selectConversation(result.conversation_id);
  };

  const sendQuestion = async (question: string) => {
    const trimmed = question.trim();
    if (!trimmed) {
      setError("请输入内容。");
      return;
    }
    if (isSending) return;
    const now = new Date().toISOString();
    const pendingAssistantId = `streaming_${Date.now()}`;
    let receivedStart = false;
    let streamConversationId = activeConversationId;
    setMessages((items) => [
      ...items,
      { message_id: `pending_user_${Date.now()}`, role: "user", content: trimmed, created_at: now, status: "completed" },
      { message_id: pendingAssistantId, role: "assistant", content: "", created_at: now, status: "streaming", sources: [], warnings: [], loading_note: "正在思考..." }
    ]);
    setInputValue("");
    setIsSending(true);
    setError("");
    setNotice("");
    const controller = new AbortController();
    abortRef.current = controller;
    try {
      await streamQAChat(
        { conversation_id: activeConversationId, question: trimmed, use_rag: true, top_k: 5 },
        {
          onStart: (data) => {
            receivedStart = true;
            streamConversationId = data.conversation_id;
            setActiveConversationId(data.conversation_id);
            localStorage.setItem(ACTIVE_QA_CONVERSATION_KEY, data.conversation_id);
            replaceChatUrl(`/chat?conversation_id=${encodeURIComponent(data.conversation_id)}`);
            setMessages((items) => items.map((item) => item.message_id === pendingAssistantId ? { ...item, message_id: data.message_id } : item));
            void refreshConversations();
          },
          onRetrievalStart: (data) => {
            setMessages((items) => items.map((item) => item.status === "streaming" && item.role === "assistant" ? { ...item, loading_note: data.message || "正在检索本地知识库..." } : item));
          },
          onSources: (data) => {
            setMessages((items) => items.map((item) => item.status === "streaming" && item.role === "assistant" ? { ...item, sources: data.sources, warnings: data.warnings, loading_note: data.sources.length ? `已参考本地知识库 ${data.sources.length} 条内容` : "正在生成回答..." } : item));
          },
          onDelta: (data) => {
            setMessages((items) => items.map((item) => item.status === "streaming" && item.role === "assistant" ? { ...item, content: `${item.content || ""}${data.text}`, loading_note: "" } : item));
          },
          onDone: (data) => {
            streamConversationId = data.conversation_id;
            setMessages((items) => items.map((item) => item.message_id === data.message_id || (item.status === "streaming" && item.role === "assistant") ? { ...item, content: data.answer, status: "completed", loading_note: "" } : item));
          },
          onError: (data) => {
            setMessages((items) => items.map((item) => item.status === "streaming" && item.role === "assistant" ? { ...item, status: "failed", error: data.error, content: item.content || data.error, loading_note: "" } : item));
            setError(data.error);
          }
        },
        controller.signal
      );
      if (streamConversationId) {
        await refreshConversations();
        await selectConversation(streamConversationId).catch(() => undefined);
      }
    } catch (sendError) {
      if (controller.signal.aborted) {
        setMessages((items) => items.map((item) => item.status === "streaming" && item.role === "assistant" ? { ...item, status: "stopped", loading_note: "", error: "已停止生成。" } : item));
      } else if (!receivedStart) {
        await fallbackNonStream(trimmed, activeConversationId).catch((fallbackError) => {
          const message = fallbackError instanceof Error ? fallbackError.message : "AI 问答失败。";
          setError(message);
          setMessages((items) => items.map((item) => item.status === "streaming" && item.role === "assistant" ? { ...item, status: "failed", content: message, error: message, loading_note: "" } : item));
        });
      } else {
        const message = sendError instanceof Error ? sendError.message : "AI 问答失败。";
        setError(message);
        setMessages((items) => items.map((item) => item.status === "streaming" && item.role === "assistant" ? { ...item, status: "failed", content: item.content || message, error: message, loading_note: "" } : item));
      }
    } finally {
      setIsSending(false);
      abortRef.current = null;
    }
  };

  const handleSend = () => void sendQuestion(inputValue);

  const handleStop = () => {
    abortRef.current?.abort();
  };

  const handleCopy = async (content: string) => {
    await navigator.clipboard.writeText(content);
    setNotice("回答已复制。");
  };

  const handleRegenerate = () => {
    const lastUser = [...messages].reverse().find((item) => item.role === "user");
    if (lastUser?.content) void sendQuestion(lastUser.content);
  };

  return (
    <AppShell activeId="chat" contentClassName="flex bg-[radial-gradient(circle_at_top,#eef8ff_0%,transparent_32%),linear-gradient(135deg,#ffffff_0%,#f8f4ff_54%,#eff8ff_100%)]">
      <ConversationPanel canDelete={currentUser?.role ? currentUser.role !== "viewer" : false} collapsedStorageKey="meizhaiseek_chat_panel_collapsed" conversations={qaSummaries} deleteDisabledMessage="当前账号为只读权限，无法删除对话。" error={error} getDeleteConfirmMessage={() => "确认删除该对话吗？删除后将不再显示在聊天记录中。"} loading={loading} onDeleteConversation={handleDeleteConversation} onNewConversation={handleNewConversation} onSelectConversation={(id) => void selectConversation(id)} selectedConversationId={activeConversationId} title="AI 对话" />

      <section className="min-h-screen min-w-0 flex-1 overflow-y-auto px-6 py-10">
        <div className="mx-auto flex min-h-[calc(100vh-80px)] w-full max-w-5xl flex-col items-center justify-start pt-10 text-center">
          <div className="flex w-full flex-wrap items-start justify-between gap-4">
            <div className="flex-1 text-center">
              <h1 className="text-4xl font-bold tracking-tight text-slate-950">
                为您提供{" "}
                <span className="bg-gradient-to-r from-fuchsia-500 via-violet-500 to-blue-500 bg-clip-text text-transparent">
                  电商经营全链路AI解决方案
                </span>
              </h1>
            </div>
            <button className="inline-flex items-center gap-2 rounded-2xl border border-violet-200 bg-white/90 px-4 py-2 text-sm font-semibold text-violet-700 shadow-sm transition hover:bg-violet-50" onClick={() => setKnowledgeOpen(true)} type="button">
              <Database className="h-4 w-4" />
              知识库
            </button>
          </div>
          <p className="mt-5 text-lg text-slate-500">数据驱动决策，智能赋能增长</p>

          <div className="mt-10 w-full pb-20">
            <ResultPanelErrorBoundary>
              <MessageList messages={messages} onCopy={(content) => void handleCopy(content)} onRegenerate={handleRegenerate} />
            </ResultPanelErrorBoundary>
            {notice ? <p className="mx-auto mb-4 max-w-3xl rounded-2xl bg-emerald-50 px-4 py-3 text-sm font-medium text-emerald-700">{notice}</p> : null}
            {isSending ? <div className="mx-auto mb-4 flex max-w-3xl items-center justify-between gap-3 rounded-2xl bg-violet-50 px-4 py-3 text-sm font-medium text-violet-700">
              <span>meizhaiseek 2.0 正在生成...</span>
              <button className="inline-flex items-center gap-1 rounded-lg bg-white px-3 py-1.5 text-xs text-violet-700 shadow-sm hover:bg-violet-100" onClick={handleStop} type="button">
                <Square className="h-3.5 w-3.5" />停止生成
              </button>
            </div> : null}
            {error ? <p className="mx-auto mb-4 max-w-3xl rounded-2xl bg-rose-50 px-4 py-3 text-sm font-medium text-rose-600">{error}</p> : null}
            <ChatInput isSending={isSending} onChange={setInputValue} onSend={handleSend} selectedAgentId={null} showAgentButton={false} showToolButtons={false} value={inputValue} />
            <QuickPrompts onSelect={(prompt) => { setInputValue(prompt); setError(""); }} prompts={chatQuickPrompts} />
          </div>
        </div>
      </section>
      <ResultPanelErrorBoundary>
        <KnowledgeBasePanel onClose={() => setKnowledgeOpen(false)} onUploaded={setNotice} open={knowledgeOpen} />
      </ResultPanelErrorBoundary>
    </AppShell>
  );
}
