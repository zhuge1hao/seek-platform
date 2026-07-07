import type { AgentDefinition } from "@/lib/agents";
import { API_BASE_URL, apiFetch, parseJsonResponse } from "./core";
import type { AgentConfig, VideoAgentStatus, SkillTemplate } from "./types";

export async function getAgents(): Promise<{ agents: AgentDefinition[] }> {
  const response = await apiFetch(`${API_BASE_URL}/api/agents`);
  return parseJsonResponse<{ agents: AgentDefinition[] }>(response);
}

export async function getVideoAgentStatus(): Promise<VideoAgentStatus> {
  return parseJsonResponse(await apiFetch(`${API_BASE_URL}/api/agents/video-script/status`));
}

export async function getAgentConfigs(): Promise<{ items: AgentConfig[] }> {
  const response = await apiFetch(`${API_BASE_URL}/api/agent-configs`);
  return parseJsonResponse<{ items: AgentConfig[] }>(response);
}

export async function updateAgentConfig(agentType: string, payload: Partial<AgentConfig>): Promise<AgentConfig> {
  const response = await apiFetch(`${API_BASE_URL}/api/agent-configs/${agentType}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  return parseJsonResponse<AgentConfig>(response);
}

export async function getSkillTemplates(agentType?: string): Promise<{ items: SkillTemplate[] }> {
  const query = agentType ? `?agent_type=${encodeURIComponent(agentType)}` : "";
  const response = await apiFetch(`${API_BASE_URL}/api/skills/templates${query}`);
  return parseJsonResponse<{ items: SkillTemplate[] }>(response);
}

export async function getSkillTemplate(skillId: string): Promise<SkillTemplate> {
  const response = await apiFetch(`${API_BASE_URL}/api/skills/templates/${skillId}`);
  return parseJsonResponse<SkillTemplate>(response);
}

export async function saveSkillTemplate(payload: SkillTemplate): Promise<SkillTemplate> {
  const response = await apiFetch(`${API_BASE_URL}/api/skills/templates`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  return parseJsonResponse<SkillTemplate>(response);
}

export async function deleteSkillTemplate(skillId: string): Promise<SkillTemplate> {
  const response = await apiFetch(`${API_BASE_URL}/api/skills/templates/${skillId}`, { method: "DELETE" });
  return parseJsonResponse<SkillTemplate>(response);
}
