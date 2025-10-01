interface SessionHeaderProps {
  sessionId: string;
  isConnected: boolean;
  isConnecting: boolean;
  onStart: () => Promise<void>;
  onDisconnect: () => void;
}

export function SessionHeader({ sessionId, isConnected, isConnecting, onStart, onDisconnect }: SessionHeaderProps) {
  return (
    <header className="rounded-xl border border-brand-600/30 bg-base-900/90 px-5 py-4 text-slate-100 shadow-lg">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-semibold text-brand-400">Agentic Interview Sandbox</h1>
          <p className="text-xs text-slate-400">Session: {sessionId}</p>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 text-sm">
            <span
              className="inline-flex h-2.5 w-2.5 rounded-full"
              style={{ backgroundColor: isConnected ? "#34d399" : "#f87171" }}
            />
            <span>{isConnected ? "Realtime Connected" : "Disconnected"}</span>
          </div>
          {isConnected ? (
            <button
              className="rounded-lg border border-brand-500 px-4 py-2 text-sm font-medium text-brand-400 hover:bg-brand-500/10"
              onClick={onDisconnect}
            >
              Disconnect
            </button>
          ) : (
            <button
              className="rounded-lg bg-brand-500 px-4 py-2 text-sm font-medium text-white hover:bg-brand-600 disabled:opacity-50"
              onClick={onStart}
              disabled={isConnecting}
            >
              {isConnecting ? "Connecting..." : "Start Session"}
            </button>
          )}
        </div>
      </div>
    </header>
  );
}
