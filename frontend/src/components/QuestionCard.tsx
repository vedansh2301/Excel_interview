import type { QuestionPayload } from "../hooks/useRealtimeInterview";

interface QuestionCardProps {
  question: QuestionPayload | null;
  onRefresh: () => Promise<void>;
  isConnected: boolean;
  isComplete?: boolean;
}

export function QuestionCard({ question, onRefresh, isConnected, isComplete }: QuestionCardProps) {
  return (
    <div className="rounded-xl border border-brand-600/30 bg-base-900/80 p-5 text-slate-100 shadow-md">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-brand-400">Current Question</h2>
          <p className="text-xs text-slate-400">The interviewer leads the conversation—respond as you would in a live interview.</p>
        </div>
        <button
          className="rounded-lg border border-brand-500 px-3 py-1 text-sm text-brand-400 hover:bg-brand-500/10 disabled:opacity-40"
          onClick={onRefresh}
          disabled={!isConnected || isComplete || !question}
        >
          Submit & Next
        </button>
      </div>
      <div className="mt-4 space-y-2">
        {question ? (
          <>
            <div className="flex flex-wrap gap-3 text-xs uppercase tracking-wide text-slate-400">
              <span>Skill · {question.skill}</span>
              <span>Difficulty · {question.difficulty}</span>
              <span>Type · {question.type}</span>
            </div>
            <p className="text-base leading-relaxed whitespace-pre-wrap">{question.prompt}</p>
          </>
        ) : isComplete ? (
          <p className="text-sm text-slate-400">We have wrapped the planned questions for this interview. You can request feedback or add final thoughts.</p>
        ) : (
          <p className="text-sm text-slate-400">No question loaded yet. Start the session to fetch the first question.</p>
        )}
      </div>
    </div>
  );
}
