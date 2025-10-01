import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { nanoid } from "nanoid/non-secure";

import { OpenAIRealtimeClient, type RealtimeEvent } from "../lib/realtimeClient";

export type ChatRole = "agent" | "candidate" | "system";

export interface ChatMessage {
  id: string;
  role: ChatRole;
  content: string;
  createdAt: Date;
}

export interface QuestionPayload {
  id: string;
  skill: string;
  difficulty: number;
  type: string;
  prompt: string;
  weight: number;
  meta: Record<string, unknown>;
}

interface UseRealtimeInterviewResult {
  sessionId: string;
  messages: ChatMessage[];
  currentQuestion: QuestionPayload | null;
  isRealtimeConnected: boolean;
  isConnecting: boolean;
  error: string | null;
  audioRef: React.MutableRefObject<HTMLAudioElement | null>;
  startSession: () => Promise<void>;
  disconnectSession: () => void;
  sendCandidateMessage: (content: string) => Promise<void>;
  advanceToNextQuestion: () => Promise<void>;
  ratingSummary: Record<string, number>;
  isComplete: boolean;
  requestFeedback: () => Promise<void>;
  feedback: string | null;
  isFeedbackLoading: boolean;
}

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL ?? "http://localhost:8000";

export function useRealtimeInterview(): UseRealtimeInterviewResult {
  const [sessionId] = useState(() => crypto.randomUUID());
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [currentQuestion, setCurrentQuestion] = useState<QuestionPayload | null>(null);
  const [isRealtimeConnected, setIsRealtimeConnected] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [ratingSummary, setRatingSummary] = useState<Record<string, number>>({});
  const [isComplete, setIsComplete] = useState(false);
  const [feedback, setFeedback] = useState<string | null>(null);
  const [isFeedbackLoading, setIsFeedbackLoading] = useState(false);

  const audioRef = useRef<HTMLAudioElement | null>(null);
  const realtimeClientRef = useRef<OpenAIRealtimeClient | null>(null);
  const lastAnswerRef = useRef<string>("");

  const appendMessage = useCallback((partial: Omit<ChatMessage, "id" | "createdAt"> & Partial<Pick<ChatMessage, "id" | "createdAt">>) => {
    setMessages((prev) => [
      ...prev,
      {
        id: partial.id ?? nanoid(),
        content: partial.content,
        role: partial.role,
        createdAt: partial.createdAt ?? new Date(),
      },
    ]);
  }, []);

  const handleRealtimeEvent = useCallback(
    (event: RealtimeEvent) => {
      const isTextDelta =
        event.type === "response.output_text.delta" || event.type === "response.message.delta";
      if (isTextDelta && typeof event.payload === "string") {
        appendMessage({
          role: "agent",
          content: event.payload,
        });
      }
    },
    [appendMessage]
  );

  const fetchNextQuestion = useCallback(async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/v1/tools/get_next_question`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: sessionId }),
      });
      if (!response.ok) {
        throw new Error(`Failed to fetch next question: ${response.status}`);
      }
      const data = await response.json();
      setRatingSummary(data.rating_summary ?? {});

      if (data.completed && !data.question) {
        setIsComplete(true);
        setCurrentQuestion(null);
        appendMessage({
          role: "agent",
          content: "That concludes our planned questions. Let me know if you have closing thoughts before we wrap up.",
        });
        return;
      }

      const question = data.question ? (data.question as QuestionPayload) : null;
      if (question) {
        setIsComplete(Boolean(data.completed));
        setCurrentQuestion(question);
        lastAnswerRef.current = "";
        appendMessage({
          role: "agent",
          content: question.prompt,
        });
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  }, [appendMessage, sessionId]);

  const startSession = useCallback(async () => {
    setIsConnecting(true);
    setError(null);
    setFeedback(null);
    setRatingSummary({});
    setIsComplete(false);
    setMessages([]);
    lastAnswerRef.current = "";
    try {
      const tokenResponse = await fetch(`${BACKEND_URL}/api/v1/realtime/session-token`, {
        method: "POST",
      });
      if (!tokenResponse.ok) {
        throw new Error(`Failed to create session token: ${tokenResponse.status}`);
      }
      const tokenPayload = await tokenResponse.json();
      const clientSecret = tokenPayload.client_secret;
      if (!clientSecret) {
        throw new Error("Realtime session token missing client_secret");
      }

      const realtimeClient = new OpenAIRealtimeClient({
        audioElement: audioRef,
        onEvent: handleRealtimeEvent,
        onOpen: () => setIsRealtimeConnected(true),
        onClose: () => setIsRealtimeConnected(false),
        onError: (err) => {
          console.error("Realtime error", err);
          setError(String(err));
        },
      });

      realtimeClientRef.current = realtimeClient;
      await realtimeClient.connect(clientSecret);

      appendMessage({
        role: "system",
        content: "Realtime session established. The interviewer is greeting you now.",
      });

      await fetchNextQuestion();
    } catch (err) {
      console.error(err);
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setIsConnecting(false);
    }
  }, [appendMessage, fetchNextQuestion, handleRealtimeEvent]);

  const disconnectSession = useCallback(() => {
    realtimeClientRef.current?.close();
    realtimeClientRef.current = null;
    setIsRealtimeConnected(false);
    setCurrentQuestion(null);
    setIsComplete(false);
    setRatingSummary({});
    lastAnswerRef.current = "";
    appendMessage({
      role: "system",
      content: "Interview disconnected by candidate.",
    });
  }, [appendMessage]);

  const evaluateAnswer = useCallback(
    async (content: string, question: QuestionPayload) => {
      let gradeScore = 60;
      let objective: Record<string, unknown> | undefined;
      let autoFeedback: string | undefined;

      if (content.trim()) {
        try {
          const gradeResponse = await fetch(`${BACKEND_URL}/api/v1/tools/grade_answer`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              session_id: sessionId,
              question_id: question.id,
              answer_payload: {
                text: content,
                question_prompt: question.prompt,
                skill: question.skill,
              },
            }),
          });

          if (gradeResponse.ok) {
            const gradeData = await gradeResponse.json();
            gradeScore = Number(gradeData.score ?? gradeScore);
            objective = gradeData.objective;
            autoFeedback = gradeData.auto_feedback ?? gradeData.notes;
            if (autoFeedback) {
              appendMessage({ role: "agent", content: autoFeedback });
            }
          }
        } catch (err) {
          console.error("Failed to grade answer", err);
        }
      }

      const normalizedScore = Math.min(1, Math.max(0, gradeScore > 1 ? gradeScore / 100 : gradeScore));

      try {
        const response = await fetch(`${BACKEND_URL}/api/v1/tools/record_outcome`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            session_id: sessionId,
            question_id: question.id,
            score: normalizedScore,
            time_ms: 60000,
            difficulty: question.difficulty,
            meta: {
              skill: question.skill,
              answer_payload: { text: content },
              strengths: objective && (objective as any).strengths,
              improvements: objective && (objective as any).improvements,
            },
          }),
        });

        if (response.ok) {
          const outcome = await response.json();
          setRatingSummary(outcome.rating_summary ?? {});
        }
      } catch (err) {
        console.error("Failed to update rating", err);
      }
    },
    [sessionId, appendMessage]
  );

  const sendCandidateMessage = useCallback(
    async (content: string) => {
      if (!content.trim()) return;
      appendMessage({ role: "candidate", content });
      lastAnswerRef.current = content;

      try {
        realtimeClientRef.current?.send({
          type: "input_text.delta",
          payload: {
            content,
            metadata: { sessionId },
          },
        });
        realtimeClientRef.current?.send({ type: "input_text.commit" });
      } catch (err) {
        console.warn("Realtime send failed", err);
      }
    },
    [appendMessage, sessionId]
  );

  useEffect(() => {
    return () => {
      realtimeClientRef.current?.close();
    };
  }, []);

  const requestFeedback = useCallback(async () => {
    setIsFeedbackLoading(true);
    try {
      const response = await fetch(`${BACKEND_URL}/api/v1/tools/finalize_session`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: sessionId }),
      });
      if (!response.ok) {
        throw new Error(`Failed to fetch feedback: ${response.status}`);
      }
      const data = await response.json();
      setFeedback(data.summary);
      appendMessage({
        role: "agent",
        content: "Here is a brief summary of your performance. Thanks for your time today!",
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setIsFeedbackLoading(false);
    }
  }, [appendMessage, sessionId]);

  const memoizedCurrentQuestion = useMemo(() => currentQuestion, [currentQuestion]);

  const advanceToNextQuestion = useCallback(async () => {
    if (memoizedCurrentQuestion && lastAnswerRef.current.trim()) {
      await evaluateAnswer(lastAnswerRef.current, memoizedCurrentQuestion);
      lastAnswerRef.current = "";
    } else if (memoizedCurrentQuestion && !lastAnswerRef.current.trim()) {
      appendMessage({
        role: "agent",
        content: "I'll mark this question as skipped and move us forward.",
      });
    }
    await fetchNextQuestion();
  }, [appendMessage, evaluateAnswer, fetchNextQuestion, memoizedCurrentQuestion]);

  return {
    sessionId,
    messages,
    currentQuestion: memoizedCurrentQuestion,
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
  };
}
