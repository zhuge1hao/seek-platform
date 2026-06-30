type MockAnswerProps = {
  answer: string;
  title?: string;
};

export function MockAnswer({ answer, title = "meizhaiseek 助手" }: MockAnswerProps) {
  return (
    <div className="mx-auto mt-6 w-full max-w-3xl whitespace-pre-line rounded-2xl border border-white/80 bg-white/85 p-5 text-sm leading-7 text-slate-700 shadow-soft backdrop-blur">
      <div className="mb-2 text-sm font-semibold text-slate-950">{title}</div>
      {answer}
    </div>
  );
}
