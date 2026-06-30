import { agentList, type AgentDefinition } from "@/lib/agents";
import type { AgentConfig, SkillTemplate } from "@/lib/api";

const VIDEO_SESSION_ID = "019dd824-f4bb-7273-8ac3-6e19b195ff82";

export const safeAgentFallback: AgentDefinition[] = agentList.map((agent) => ({ ...agent }));

export function safeAgentConfigFallback(): AgentConfig[] {
  return safeAgentFallback.map((agent) => ({
    agent_type: agent.agent_type,
    name: agent.name,
    enabled: true,
    workflow: agent.agent_type === "video_script_breakdown" ? "video_script_workflow" : agent.workflow || "generic_agent_workflow",
    local_agent_mode: "http",
    session_id: agent.agent_type === "video_script_breakdown" ? VIDEO_SESSION_ID : "",
    payload_style: "protocol",
    accepted_inputs: agent.accepted_inputs,
    default_skill_ids: [],
    output_types: ["text"],
    default_options: {},
    description: agent.description,
    visible: true
  }));
}

export const safeSkillTemplateFallback: SkillTemplate[] = [];

export function isSafeAgentConfig(value: unknown): value is AgentConfig {
  if (!value || typeof value !== "object") return false;
  const item = value as Partial<AgentConfig>;
  return Boolean(item.agent_type && typeof item.agent_type === "string" && typeof item.enabled === "boolean");
}

export function sanitizeAgentConfigs(value: unknown): { configs: AgentConfig[]; usedFallback: boolean } {
  const rawItems = Array.isArray((value as { items?: unknown })?.items) ? (value as { items: unknown[] }).items : Array.isArray(value) ? (value as unknown[]) : null;
  if (!rawItems) return { configs: safeAgentConfigFallback(), usedFallback: true };
  const defaults = new Map(safeAgentConfigFallback().map((config) => [config.agent_type, config]));
  const configs = rawItems.filter(isSafeAgentConfig).map((config) => {
    const fallback = defaults.get(config.agent_type);
    return {
      ...(fallback || {}),
      ...config,
      name: config.name || fallback?.name || config.agent_type,
      accepted_inputs: Array.isArray(config.accepted_inputs) && config.accepted_inputs.length ? config.accepted_inputs : fallback?.accepted_inputs || ["text"],
      output_types: Array.isArray(config.output_types) && config.output_types.length ? config.output_types : fallback?.output_types || ["text"],
      default_skill_ids: Array.isArray(config.default_skill_ids) ? config.default_skill_ids : [],
      default_options: config.default_options && typeof config.default_options === "object" ? config.default_options : {}
    } as AgentConfig;
  });
  return configs.length ? { configs, usedFallback: configs.length !== rawItems.length } : { configs: safeAgentConfigFallback(), usedFallback: true };
}
