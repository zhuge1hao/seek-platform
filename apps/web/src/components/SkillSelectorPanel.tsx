"use client";

import { useEffect, useState } from "react";
import { Check, Plus, X } from "lucide-react";
import { getSkillTemplates, type SkillTemplate } from "@/lib/api";

type SkillSelectorPanelProps = {
  agentType: string;
  selectedSkillIds: string[];
  onSelectedSkillIdsChange: (ids: string[]) => void;
  onInsertTemplate: (template: SkillTemplate) => void;
  onClose?: () => void;
};

export function SkillSelectorPanel({
  agentType,
  selectedSkillIds,
  onSelectedSkillIdsChange,
  onInsertTemplate,
  onClose
}: SkillSelectorPanelProps) {
  const [templates, setTemplates] = useState<SkillTemplate[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    setIsLoading(true);
    setError("");
    getSkillTemplates(agentType)
      .then((result) => {
        if (!cancelled) setTemplates(result.items || []);
      })
      .catch((err) => {
        if (!cancelled) setError(err instanceof Error ? err.message : "技能模板加载失败。");
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [agentType]);

  const toggleTemplate = (skillId: string) => {
    if (selectedSkillIds.includes(skillId)) {
      onSelectedSkillIdsChange(selectedSkillIds.filter((id) => id !== skillId));
    } else {
      onSelectedSkillIdsChange([...selectedSkillIds, skillId]);
    }
  };

  return (
    <div className="mt-3 rounded-2xl border border-violet-100 bg-white p-4 shadow-sm">
      <div className="mb-3 flex items-center justify-between gap-3">
        <p className="text-sm font-semibold text-slate-900">技能模板</p>
        {onClose ? (
          <button className="rounded-full p-1 text-slate-400 transition hover:bg-slate-100 hover:text-slate-700" onClick={onClose} type="button">
            <X className="h-4 w-4" />
          </button>
        ) : null}
      </div>

      {isLoading ? <p className="text-sm text-slate-500">正在加载技能模板...</p> : null}
      {error ? <p className="rounded-xl bg-rose-50 px-3 py-2 text-sm text-rose-600">{error}</p> : null}
      {!isLoading && !error && templates.length === 0 ? <p className="text-sm text-slate-500">当前智能体暂无可用技能模板。</p> : null}

      <div className="space-y-3">
        {templates.map((template) => {
          const selected = selectedSkillIds.includes(template.id);
          return (
            <div key={template.id} className={["rounded-2xl border p-3", selected ? "border-violet-200 bg-violet-50" : "border-slate-100 bg-white"].join(" ")}>
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="text-sm font-semibold text-slate-900">{template.name}</p>
                  <p className="mt-1 text-xs leading-5 text-slate-500">{template.description}</p>
                </div>
                <button
                  className={["inline-flex shrink-0 items-center gap-1 rounded-full px-3 py-1 text-xs font-medium", selected ? "bg-violet-600 text-white" : "bg-slate-100 text-slate-600"].join(" ")}
                  onClick={() => toggleTemplate(template.id)}
                  type="button"
                >
                  {selected ? <Check className="h-3 w-3" /> : <Plus className="h-3 w-3" />}
                  {selected ? "已选" : "选择"}
                </button>
              </div>
              <div className="mt-3 flex flex-wrap gap-2">
                <button
                  className="rounded-full border border-violet-200 bg-white px-3 py-1.5 text-xs font-medium text-violet-700 transition hover:bg-violet-50"
                  onClick={() => onInsertTemplate(template)}
                  type="button"
                >
                  插入模板到提示词
                </button>
                <span className="rounded-full bg-slate-100 px-2 py-1 text-xs text-slate-500">{template.output_format}</span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
