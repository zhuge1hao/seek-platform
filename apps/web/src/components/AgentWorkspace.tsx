"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { AgentSelectorPopover } from "@/components/AgentSelectorPopover";
import { ChatInput } from "@/components/ChatInput";
import { GenericAgentPanel } from "@/components/GenericAgentPanel";
import { VideoScriptAgentPanel } from "@/components/VideoScriptAgentPanel";
import { agentList, findAgentById, type AgentDefinition, type AgentToolId } from "@/lib/agents";
import { getAgentConfigs, getAgents, type AgentConfig, type AgentRunStatus } from "@/lib/api";
import { safeAgentFallback, sanitizeAgentConfigs } from "@/lib/safeFallbacks";

type AgentWorkspaceProps = {
  selectedAgentId: AgentToolId | null;
  inputValue: string;
  isSending?: boolean;
  showAgentButton?: boolean;
  configRefreshKey?: number;
  onInputChange: (value: string) => void;
  onSend: () => void;
  onAgentSelect?: (agent: AgentDefinition) => void;
  conversationId?: string | null;
  initialRun?: AgentRunStatus | null;
  onConversationChange?: (conversationId: string) => void;
  onRunChange?: (run: AgentRunStatus) => void;
};

export function AgentWorkspace({
  selectedAgentId,
  inputValue,
  isSending = false,
  showAgentButton = true,
  configRefreshKey = 0,
  onInputChange,
  onSend,
  onAgentSelect,
  conversationId,
  initialRun,
  onConversationChange,
  onRunChange
}: AgentWorkspaceProps) {
  const [agents, setAgents] = useState<AgentDefinition[]>(agentList);
  const [agentConfigs, setAgentConfigs] = useState<AgentConfig[]>([]);
  const [notice, setNotice] = useState("");
  const [isAgentSelectorOpen, setIsAgentSelectorOpen] = useState(false);
  const [hasRunningTask, setHasRunningTask] = useState(false);
  const workspaceRef = useRef<HTMLDivElement>(null);
  const selectedAgent = useMemo(() => findAgentById(selectedAgentId, agents), [agents, selectedAgentId]);
  const selectedConfig = useMemo(() => agentConfigs.find((config) => config.agent_type === selectedAgent?.agent_type), [agentConfigs, selectedAgent]);

  useEffect(() => {
    let cancelled = false;
    getAgents()
      .then((result) => {
        if (cancelled) return;
        const sourceAgents = Array.isArray(result.agents) && result.agents.length ? result.agents : safeAgentFallback;
        const validAgents = sourceAgents.filter((agent) => agent && typeof agent.agent_type === "string" && typeof agent.id === "string");
        const merged = validAgents.map((agent) => ({
          ...agent,
          name: agent.name || agent.agent_type,
          enabled: typeof agent.enabled === "boolean" ? agent.enabled : true,
          accepted_inputs: Array.isArray(agent.accepted_inputs) ? agent.accepted_inputs : ["text"],
          icon: agentList.find((localAgent) => localAgent.id === agent.id || localAgent.agent_type === agent.agent_type)?.icon
        }));
        setAgents(merged.length ? merged : safeAgentFallback);
        if (!Array.isArray(result.agents) || validAgents.length !== result.agents.length) {
          setNotice("后端智能体列表异常，当前已切换为前端安全默认配置。");
        }
      })
      .catch(() => {
        if (!cancelled) {
          setAgents(safeAgentFallback);
          setNotice("智能体列表加载失败，已使用本地配置。");
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    let cancelled = false;
    getAgentConfigs()
      .then((result) => {
        if (!cancelled) {
          const { configs, usedFallback } = sanitizeAgentConfigs(result);
          setAgentConfigs(configs);
          if (usedFallback) setNotice("后端智能体配置异常，当前已切换为前端安全默认配置。");
        }
      })
      .catch(() => {
        if (!cancelled) {
          setAgentConfigs(sanitizeAgentConfigs(null).configs);
          setNotice("后端智能体配置异常，当前已切换为前端安全默认配置。");
        }
      });
    return () => {
      cancelled = true;
    };
  }, [configRefreshKey]);

  useEffect(() => {
    if (!isAgentSelectorOpen) return;
    const handlePointerDown = (event: PointerEvent) => {
      if (!workspaceRef.current?.contains(event.target as Node)) {
        setIsAgentSelectorOpen(false);
      }
    };
    document.addEventListener("pointerdown", handlePointerDown);
    return () => document.removeEventListener("pointerdown", handlePointerDown);
  }, [isAgentSelectorOpen]);

  const handleSelectAgent = (agent: AgentDefinition) => {
    if (hasRunningTask && selectedAgentId !== agent.id) {
      const confirmed = window.confirm("当前任务正在执行，切换不会取消任务。是否继续？");
      if (!confirmed) {
        setIsAgentSelectorOpen(false);
        return;
      }
    }
    onAgentSelect?.(agent);
    setIsAgentSelectorOpen(false);
  };

  const handleOpenAgentSelector = () => setIsAgentSelectorOpen((open) => !open);

  return (
    <div className="relative mx-auto w-full max-w-[880px]" ref={workspaceRef}>
      {isAgentSelectorOpen ? (
        <AgentSelectorPopover
          agentConfigs={agentConfigs}
          agents={agents}
          onClose={() => setIsAgentSelectorOpen(false)}
          onDisabledClick={() => setNotice("该智能体未启用。")}
          onSelect={handleSelectAgent}
          selectedAgentId={selectedAgentId}
        />
      ) : null}

      {notice ? <p className="mb-3 rounded-xl bg-amber-50 px-4 py-3 text-sm font-medium text-amber-700">{notice}</p> : null}
      {selectedAgent ? <BlueprintSummary agent={selectedAgent} /> : null}

      {selectedAgentId === "video-script-breakdown" ? (
        <VideoScriptAgentPanel conversationId={conversationId} initialPrompt={inputValue} initialRun={initialRun} onConversationChange={onConversationChange} onOpenAgentSelector={handleOpenAgentSelector} onRunActiveChange={setHasRunningTask} onRunChange={onRunChange} selectedAgentId={selectedAgentId} />
      ) : selectedAgent ? (
        <GenericAgentPanel
          agent={selectedAgent}
          agentConfig={selectedConfig}
          onOpenAgentSelector={handleOpenAgentSelector}
          onPromptChange={onInputChange}
          onRunActiveChange={setHasRunningTask}
          promptValue={inputValue}
          conversationId={conversationId}
          initialRun={initialRun}
          onConversationChange={onConversationChange}
          onRunChange={onRunChange}
        />
      ) : (
        <ChatInput
          isSending={isSending}
          onChange={onInputChange}
          onOpenAgentSelector={handleOpenAgentSelector}
          onSend={onSend}
          selectedAgentId={selectedAgentId}
          showAgentButton={showAgentButton}
          value={inputValue}
        />
      )}
    </div>
  );
}

function BlueprintSummary({ agent }: { agent: AgentDefinition }) {
  if (agent.blueprint_status !== "published") return null;
  const steps = agent.blueprint_methodology_summary?.steps || [];
  const outputs = agent.blueprint_output_summary?.sections || [];
  return (
    <section className="mb-3 rounded-xl border border-violet-100 bg-violet-50/50 px-4 py-3 text-sm text-slate-700">
      <div className="flex flex-wrap items-center gap-2">
        <span className="font-semibold text-violet-700">蓝图 v{agent.blueprint_version || "-"}</span>
        <span>最近测试：{agent.blueprint_last_test_status || "-"}</span>
        <span>方法论步骤：{agent.blueprint_methodology_summary?.step_count || 0}</span>
        <span>输出区块：{agent.blueprint_output_summary?.section_count || 0}</span>
      </div>
      {(steps.length || outputs.length) ? <p className="mt-2 text-xs text-slate-500">方法论：{steps.join(" / ") || "-"}；输出：{outputs.join(" / ") || "-"}</p> : null}
    </section>
  );
}
