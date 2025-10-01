import { useMemo } from "react";

import { ChatPane } from "./components/ChatPane";
import { QuestionCard } from "./components/QuestionCard";
import { SessionHeader } from "./components/SessionHeader";
import { StatusBanner } from "./components/StatusBanner";
import { RatingPanel } from "./components/RatingPanel";
import { FeedbackCard } from "./components/FeedbackCard";
import { useRealtimeInterview } from "./hooks/useRealtimeInterview";

function App() {
  const {
    sessionId,
    messages,
    currentQuestion,
    isRealtimeConnected,
    isConnecting,
    error,
    audioRef,
    startSession,
    disconnectSession,
    sendCandidateMessage,
    advanceToNextQuestion,
    ratingSummary,
    isComplete,
    requestFeedback,
    feedback,
    isFeedbackLoading,
  } = useRealtimeInterview();

  const infoMessage = useMemo(() => {
    if (isRealtimeConnected) {
      return "Connected to OpenAI Realtime. Use the chat to interact with the interviewer agent.";
    }
    if (isConnecting) {
      return "Initialising realtime session...";
    }
    return "Click 'Start Session' to request an ephemeral token and open a realtime connection.";
  }, [isConnecting, isRealtimeConnected]);

  return (
    <div className="min-h-screen bg-base-900 bg-gradient-to-br from-base-900 via-brand-600/5 to-accent-400/10 px-6 py-10 text-slate-100">
      <div className="mx-auto flex w-full max-w-6xl flex-col gap-6">
        <SessionHeader
          sessionId={sessionId}
          isConnected={isRealtimeConnected}
          isConnecting={isConnecting}
          onStart={startSession}
          onDisconnect={disconnectSession}
        />

        <StatusBanner message={error ?? infoMessage} tone={error ? "error" : "info"} />

        <main className="grid grid-cols-1 gap-6 md:grid-cols-[3fr,2fr]">
          <ChatPane
            messages={messages}
            onSend={sendCandidateMessage}
            disabled={!isRealtimeConnected}
          />
          <div className="flex flex-col gap-4">
            <QuestionCard
              question={currentQuestion}
              onRefresh={advanceToNextQuestion}
              isConnected={isRealtimeConnected}
              isComplete={isComplete}
            />
            <RatingPanel ratingSummary={ratingSummary} />
            <div className="rounded-xl border border-brand-600/30 bg-base-900/80 p-4 text-sm text-slate-300 shadow-md">
              <p className="font-medium text-brand-400">Voice Output</p>
              <p className="mt-1 text-xs text-slate-400">
                If the realtime model streams audio, it will play through the hidden audio element below.
              </p>
              <audio ref={audioRef} className="mt-4 hidden" controls />
            </div>
            <button
              className="rounded-lg border border-brand-500 px-4 py-2 text-sm font-medium text-brand-400 hover:bg-brand-500/10 disabled:opacity-40"
              onClick={requestFeedback}
              disabled={!isComplete || isFeedbackLoading}
            >
              {isFeedbackLoading ? "Preparing feedback..." : "View Interview Feedback"}
            </button>
            <FeedbackCard feedback={feedback ?? ""} />
          </div>
        </main>
      </div>
    </div>
  );
}

export default App;
