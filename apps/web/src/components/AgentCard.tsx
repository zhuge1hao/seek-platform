import { Sparkles } from "lucide-react";

type AgentCardProps = {
  title: string;
  index: number;
  active?: boolean;
  onClick?: () => void;
};

const rotations = ["-rotate-2", "rotate-1", "-rotate-1", "rotate-2"];
const gradients = [
  "from-violet-50 via-white to-pink-50",
  "from-sky-50 via-white to-violet-50",
  "from-rose-50 via-white to-slate-50",
  "from-emerald-50 via-white to-sky-50"
];

export function AgentCard({ title, index, active = false, onClick }: AgentCardProps) {
  return (
    <button
      className={[
        "group flex h-28 min-w-[150px] flex-col justify-between rounded-2xl border border-white/80 bg-gradient-to-br p-4 text-left shadow-soft transition hover:-translate-y-1 hover:rotate-0",
        active ? "ring-2 ring-violet-300 ring-offset-2 ring-offset-transparent" : "",
        rotations[index % rotations.length],
        gradients[index % gradients.length]
      ].join(" ")}
      data-testid={`agent-card-${index}`}
      onClick={onClick}
      type="button"
    >
      <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-white text-violet-600 shadow-sm">
        <Sparkles className="h-4 w-4" />
      </div>
      <div className="text-base font-semibold text-slate-950">{title}</div>
    </button>
  );
}
