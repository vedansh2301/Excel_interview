import { useState } from "react";
import clsx from "clsx";

import type { ChatMessage } from "../hooks/useRealtimeInterview";

interface ChatPaneProps {
  messages: ChatMessage[];
  onSend: (content: string) => Promise<void>;
  disabled?: boolean;
}

export function ChatPane({ messages, onSend, disabled }: ChatPaneProps) {
  const [draft, setDraft] = useState("");
  const [isSending, setIsSending] = useState(false);

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!draft.trim()) return;
    setIsSending(true);
    try {
      await onSend(draft);
      setDraft("");
    } finally {
      setIsSending(false);
    }
  };

  return (
    <div className="flex h-full flex-col rounded-xl border border-brand-600/30 bg-base-900/80 shadow-lg">
      <div className="flex-1 overflow-y-auto space-y-2 p-4">
        {messages.map((message) => (
          <div
            key={message.id}
            className={clsx("max-w-[80%] px-3 py-2 rounded-lg", {
              "ml-auto bg-brand-500 text-white": message.role === "candidate",
              "bg-brand-600/20 text-brand-400": message.role === "agent",
              "mx-auto bg-accent-400/10 text-accent-400": message.role === "system",
            })}
          >
            <p className="text-sm whitespace-pre-wrap leading-relaxed">{message.content}</p>
            <p className="mt-1 text-[11px] uppercase tracking-wide text-slate-400">
              {message.role.toUpperCase()} · {message.createdAt.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
            </p>
          </div>
        ))}
      </div>
      <form onSubmit={handleSubmit} className="border-t border-brand-600/30 bg-base-900/90 p-4">
        <div className="flex items-center gap-2">
          <input
            className="flex-1 rounded-lg border border-brand-600/30 bg-base-900 px-3 py-2 text-sm text-slate-100 focus:border-brand-500 focus:outline-none"
            placeholder="Type your answer or message..."
            value={draft}
            disabled={disabled || isSending}
            onChange={(event) => setDraft(event.target.value)}
          />
          <button
            type="submit"
            disabled={disabled || isSending}
            className="rounded-lg bg-brand-500 px-4 py-2 text-sm font-medium text-white hover:bg-brand-600 disabled:opacity-50"
          >
            {isSending ? "Sending" : "Send"}
          </button>
        </div>
      </form>
    </div>
  );
}
