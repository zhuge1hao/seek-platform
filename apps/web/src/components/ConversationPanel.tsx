"use client";

import { memo, useEffect, useState } from "react";
import { Menu, Plus, Trash2 } from "lucide-react";
import { ConfirmDialog } from "@/components/ui/ConfirmDialog";
import type { ConversationSummary } from "@/lib/api";

type ConversationPanelProps = {
  title: string;
  onNewConversation: () => void;
  conversations?: ConversationSummary[];
  selectedConversationId?: string | null;
  loading?: boolean;
  error?: string;
  onSelectConversation?: (conversationId: string) => void;
  collapsedStorageKey?: string;
  onDeleteConversation?: (conversation: ConversationSummary) => Promise<void> | void;
  canDelete?: boolean;
  deleteDisabledMessage?: string;
  getDeleteConfirmMessage?: (conversation: ConversationSummary) => string;
};

const statusText: Record<string, string> = { running: "执行中", completed: "已完成", failed: "失败", cancelled: "已取消" };

const ConversationItem = memo(function ConversationItem({
  conversation,
  selected,
  onSelect,
  onRequestDelete,
  canDelete,
  deleteDisabledMessage,
  canShowDelete,
}: {
  conversation: ConversationSummary;
  selected: boolean;
  onSelect?: (conversationId: string) => void;
  onRequestDelete: (conversation: ConversationSummary) => void;
  canDelete: boolean;
  deleteDisabledMessage: string;
  canShowDelete: boolean;
}) {
  return (
    <div className={["group flex items-stretch rounded-xl transition", selected ? "bg-violet-100 text-violet-900" : "hover:bg-slate-100"].join(" ")}>
      <button className="min-w-0 flex-1 px-3 py-3 text-left" onClick={() => onSelect?.(conversation.conversation_id)} type="button">
        <p className="truncate text-sm font-semibold">{conversation.title}</p>
        <div className="mt-1 flex items-center justify-between gap-2 text-xs text-slate-500">
          <span className="truncate">{conversation.agent_name || conversation.agent_type || "未选择智能体"}</span>
          <span>{statusText[conversation.status || ""] || conversation.status || ""}</span>
        </div>
        <p className="mt-1 truncate text-[11px] text-slate-400">{conversation.updated_at ? new Date(conversation.updated_at).toLocaleString("zh-CN") : ""}</p>
      </button>
      {canShowDelete ? <button
        aria-label="删除记录"
        className="mr-2 self-center rounded-lg p-2 text-slate-400 opacity-70 transition hover:bg-rose-50 hover:text-rose-600 disabled:cursor-not-allowed disabled:opacity-40 group-hover:opacity-100"
        disabled={!canDelete}
        onClick={(event) => {
          event.stopPropagation();
          if (!canDelete) {
            window.alert(deleteDisabledMessage);
            return;
          }
          onRequestDelete(conversation);
        }}
        title={canDelete ? "删除记录" : deleteDisabledMessage}
        type="button"
      >
        <Trash2 className="h-4 w-4" />
      </button> : null}
    </div>
  );
});

export function ConversationPanel({ title, onNewConversation, conversations = [], selectedConversationId, loading, error, onSelectConversation, collapsedStorageKey, onDeleteConversation, canDelete = true, deleteDisabledMessage = "当前账号为只读权限，无法删除对话。", getDeleteConfirmMessage }: ConversationPanelProps) {
  const [collapsed, setCollapsed] = useState(false);
  const [confirming, setConfirming] = useState<ConversationSummary | null>(null);
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    if (!collapsedStorageKey) return;
    setCollapsed(localStorage.getItem(collapsedStorageKey) === "true");
  }, [collapsedStorageKey]);

  const toggleCollapsed = () => {
    const next = !collapsed;
    setCollapsed(next);
    if (collapsedStorageKey) localStorage.setItem(collapsedStorageKey, String(next));
  };

  const confirmDelete = async () => {
    if (!confirming || !onDeleteConversation) return;
    setDeleting(true);
    try {
      await onDeleteConversation(confirming);
      setConfirming(null);
    } finally {
      setDeleting(false);
    }
  };

  if (collapsed) {
    return (
      <section className="flex h-screen w-[52px] shrink-0 flex-col items-center border-r border-slate-200/80 bg-white py-5 transition-all duration-200">
        <button aria-label="展开对话栏" className="flex h-9 w-9 items-center justify-center rounded-xl text-slate-500 transition hover:bg-slate-100 hover:text-slate-950" onClick={toggleCollapsed} title="展开对话栏" type="button">
          <Menu className="h-4 w-4" />
        </button>
      </section>
    );
  }

  return (
    <section className="flex h-screen w-[260px] shrink-0 flex-col border-r border-slate-200/80 bg-white px-4 py-5 transition-all duration-200">
      <div className="mb-5 flex items-center justify-between">
        <h1 className="text-lg font-semibold text-slate-950">{title}</h1>
        <button aria-label="收起对话栏" className="flex h-9 w-9 items-center justify-center rounded-xl text-slate-500 transition hover:bg-slate-100 hover:text-slate-950" onClick={toggleCollapsed} title="收起对话栏" type="button">
          <Menu className="h-4 w-4" />
        </button>
      </div>

      <button className="mb-5 flex h-11 items-center justify-center gap-2 rounded-xl bg-slate-950 px-4 text-sm font-semibold text-white shadow-sm transition hover:bg-slate-800" data-testid="agent-new-conversation" onClick={onNewConversation} type="button">
        <Plus className="h-4 w-4" />
        发起新对话
      </button>

      {loading ? <p className="px-2 py-4 text-sm text-slate-400">正在加载聊天记录…</p> : null}
      {error ? <p className="rounded-xl bg-rose-50 px-3 py-3 text-sm text-rose-600">{error}</p> : null}
      {!loading && conversations.length ? <div className="min-h-0 flex-1 space-y-2 overflow-y-auto">
        {conversations.map((conversation) => <ConversationItem canDelete={canDelete} canShowDelete={Boolean(onDeleteConversation)} conversation={conversation} deleteDisabledMessage={deleteDisabledMessage} key={conversation.conversation_id} onRequestDelete={setConfirming} onSelect={onSelectConversation} selected={selectedConversationId === conversation.conversation_id} />)}
      </div> : null}
      {!loading && !conversations.length ? <div className="mt-16 flex flex-1 flex-col items-center text-center">
        <div className="mb-6 flex h-16 w-16 items-center justify-center rounded-full border border-slate-100 bg-slate-50 text-slate-300">
          <span className="h-3 w-3 rounded-full bg-slate-300" />
        </div>
        <p className="text-sm font-medium text-slate-600">暂无聊天记录</p>
        <p className="mt-3 text-sm leading-6 text-slate-400">开始新对话后会显示在这里</p>
      </div>
      : null}
      <ConfirmDialog
        busy={deleting}
        confirmLabel="删除"
        danger
        message={confirming ? getDeleteConfirmMessage?.(confirming) || "确认删除该对话吗？删除后将不再显示在聊天记录中。" : ""}
        onCancel={() => setConfirming(null)}
        onConfirm={() => void confirmDelete()}
        open={Boolean(confirming)}
        title="删除记录"
      />
    </section>
  );
}
