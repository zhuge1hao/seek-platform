"use client";

import { useMemo, useState } from "react";
import {
  BarChart3,
  Crown,
  FileCode2,
  Flower2,
  Gift,
  Image,
  LayoutTemplate,
  Lightbulb,
  ListChecks,
  MapPin,
  MessageSquareText,
  NotebookText,
  PictureInPicture2,
  Radar,
  ScrollText,
  Search,
  Send,
  ShieldCheck,
  Stethoscope,
  Tag,
  Target,
  Text,
  Video,
  WholeWord
} from "lucide-react";
import type { AgentConfig } from "@/lib/api";
import type { AgentDefinition, AgentIconName } from "@/lib/agents";

const iconMap: Record<AgentIconName, typeof BarChart3> = {
  chart: BarChart3,
  word: WholeWord,
  target: Target,
  radar: Radar,
  flower: Flower2,
  message: MessageSquareText,
  tag: Tag,
  scroll: ScrollText,
  image: Image,
  list: ListChecks,
  crown: Crown,
  layout: LayoutTemplate,
  gift: Gift,
  picture: PictureInPicture2,
  bulb: Lightbulb,
  send: Send,
  pin: MapPin,
  stethoscope: Stethoscope,
  video: Video,
  text: Text,
  code: FileCode2,
  shield: ShieldCheck
};

const categoryOrder = ["市场机会", "商品视觉", "内容生成", "数据诊断", "视频脚本", "风险诊断"];

type AgentSelectorPopoverProps = {
  agents: AgentDefinition[];
  agentConfigs?: AgentConfig[];
  selectedAgentId?: string | null;
  onSelect: (agent: AgentDefinition) => void;
  onClose: () => void;
  onDisabledClick?: (agent: AgentDefinition) => void;
};

export function AgentSelectorPopover({ agents, agentConfigs = [], selectedAgentId, onSelect, onClose, onDisabledClick }: AgentSelectorPopoverProps) {
  const [query, setQuery] = useState("");
  const configByType = useMemo(() => new Map(agentConfigs.map((config) => [config.agent_type, config])), [agentConfigs]);

  const groupedAgents = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase();
    const filtered = agents.filter((agent) => {
      if (!normalizedQuery) return true;
      return [agent.name, agent.description, agent.category, agent.agent_type].some((value) => String(value || "").toLowerCase().includes(normalizedQuery));
    });

    const knownGroups = categoryOrder
      .map((category) => ({ category, agents: filtered.filter((agent) => agent.category === category) }))
      .filter((group) => group.agents.length > 0);
    const extraCategories = Array.from(new Set(filtered.map((agent) => agent.category).filter((category) => !categoryOrder.includes(category))));
    const extraGroups = extraCategories.map((category) => ({ category, agents: filtered.filter((agent) => agent.category === category) }));
    return [...knownGroups, ...extraGroups];
  }, [agents, query]);

  return (
    <div className="absolute bottom-12 left-0 z-[80] max-h-[640px] w-[390px] overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-[0_22px_55px_rgba(15,23,42,0.18)]">
      <div className="border-b border-slate-100 p-3">
        <div className="flex items-center gap-2 rounded-xl bg-slate-50 px-3 py-2 text-slate-500">
          <Search className="h-4 w-4" />
          <input className="min-w-0 flex-1 bg-transparent text-sm text-slate-900 outline-none placeholder:text-slate-400" onChange={(event) => setQuery(event.target.value)} placeholder="搜索智能体..." value={query} />
        </div>
      </div>

      <div className="max-h-[560px] overflow-y-auto p-3 [scrollbar-color:#a3a3a3_transparent] [scrollbar-width:thin]">
        {groupedAgents.length ? (
          <div className="space-y-4">
            {groupedAgents.map((group) => (
              <div key={group.category}>
                <p className="mb-2 px-2 text-xs font-semibold text-slate-400">{group.category}</p>
                <div className="space-y-1">
                  {group.agents.map((agent) => {
                    const Icon = agent.icon ? iconMap[agent.icon] : NotebookText;
                    const selected = selectedAgentId === agent.id;
                    const config = configByType.get(agent.agent_type);
                    const enabled = config?.enabled ?? agent.enabled;
                    const configured = Boolean(config?.session_id || config?.default_skill_ids?.length || config?.workflow);
                    const inputTags = config?.accepted_inputs?.length ? config.accepted_inputs : agent.accepted_inputs;
                    const displayName = agent.name || agent.agent_type;

                    return (
                      <button
                        className={[
                          "flex w-full gap-3 rounded-xl px-3 py-2 text-left transition",
                          selected ? "bg-violet-50 text-violet-700" : "text-slate-950 hover:bg-slate-50 hover:text-violet-700",
                          enabled ? "" : "opacity-50"
                        ].join(" ")}
                        key={agent.id}
                        onClick={() => {
                          if (!enabled) {
                            onDisabledClick?.(agent);
                            return;
                          }
                          onSelect(agent);
                          onClose();
                        }}
                        type="button"
                      >
                        <Icon className="mt-0.5 h-5 w-5 shrink-0" strokeWidth={2.2} />
                        <span className="min-w-0 flex-1">
                          <span className="flex items-center justify-between gap-2">
                            <span className="truncate text-sm font-semibold">{displayName}</span>
                            <span className="shrink-0 rounded-full bg-white px-2 py-0.5 text-xs text-slate-500">-{agent.cost}</span>
                          </span>
                          <span className="mt-1 block max-h-10 overflow-hidden text-xs leading-5 text-slate-500">{agent.description}</span>
                          <span className="mt-2 flex flex-wrap gap-1">
                            <span className={["rounded-full px-2 py-0.5 text-[11px]", configured ? "bg-emerald-50 text-emerald-600" : "bg-slate-100 text-slate-500"].join(" ")}>
                              {configured ? "已配置" : "未配置"}
                            </span>
                            {inputTags.slice(0, 3).map((tag) => (
                              <span key={tag} className="rounded-full bg-slate-100 px-2 py-0.5 text-[11px] text-slate-500">{tag}</span>
                            ))}
                            {!enabled ? <span className="rounded-full bg-rose-50 px-2 py-0.5 text-[11px] text-rose-500">未启用</span> : null}
                          </span>
                        </span>
                      </button>
                    );
                  })}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="py-8 text-center text-sm text-slate-400">没有找到匹配的智能体</div>
        )}
      </div>
    </div>
  );
}
