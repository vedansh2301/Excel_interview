interface FeedbackCardProps {
  feedback: string;
}

export function FeedbackCard({ feedback }: FeedbackCardProps) {
  if (!feedback) return null;

  return (
    <div className="rounded-xl border border-brand-600/30 bg-base-900/80 p-4 text-sm text-slate-200 shadow-md">
      <p className="font-medium text-brand-400">Interview Feedback</p>
      <p className="mt-2 whitespace-pre-wrap leading-relaxed">{feedback}</p>
    </div>
  );
}
