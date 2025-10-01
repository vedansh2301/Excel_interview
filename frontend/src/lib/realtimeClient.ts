import type { MutableRefObject } from "react";

export type RealtimeEvent = {
  type: string;
  payload?: unknown;
};

export interface RealtimeClientOptions {
  baseUrl?: string;
  model?: string;
  audioElement?: MutableRefObject<HTMLAudioElement | null> | null;
  onEvent?: (event: RealtimeEvent) => void;
  onOpen?: () => void;
  onClose?: (event?: Event) => void;
  onError?: (error: unknown) => void;
}

export class OpenAIRealtimeClient {
  private pc: RTCPeerConnection | null = null;
  private dc: RTCDataChannel | null = null;
  private localStream: MediaStream | null = null;
  private readonly options: RealtimeClientOptions;

  constructor(options: RealtimeClientOptions = {}) {
    this.options = options;
  }

  async connect(clientSecret: string): Promise<void> {
    try {
      const pc = new RTCPeerConnection();
      this.pc = pc;

      pc.onconnectionstatechange = () => {
        if (pc.connectionState === "connected") {
          this.options.onOpen?.();
        }
        if (pc.connectionState === "failed" || pc.connectionState === "disconnected") {
          this.options.onClose?.();
        }
      };

      pc.ontrack = (event) => {
        const audioEl = this.options.audioElement?.current;
        if (!audioEl || event.streams.length === 0) return;
        // Attach remote audio to the element so users can hear LLM voice.
        audioEl.srcObject = event.streams[0];
        audioEl.play().catch((error) => {
          if (error.name !== "NotAllowedError") {
            this.options.onError?.(error);
          }
        });
      };

      const dc = pc.createDataChannel("oai-events");
      this.dc = dc;

      dc.onopen = () => {
        this.options.onOpen?.();
      };

      dc.onclose = (event) => {
        this.options.onClose?.(event);
      };

      dc.onerror = (event) => {
        this.options.onError?.(event);
      };

      dc.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          this.options.onEvent?.(data);
        } catch (error) {
          this.options.onError?.(error);
        }
      };

      await this.attachAudioStream(pc);

      const offer = await pc.createOffer();
      await pc.setLocalDescription(offer);

      const response = await fetch(this.getRealtimeUrl(), {
        method: "POST",
        headers: {
          Authorization: `Bearer ${clientSecret}`,
          "Content-Type": "application/sdp",
        },
        body: offer.sdp ?? "",
      });

      if (!response.ok) {
        throw new Error(`Realtime handshake failed: ${response.status} ${await response.text()}`);
      }

      const answer = {
        type: "answer",
        sdp: await response.text(),
      } as RTCSessionDescriptionInit;

      await pc.setRemoteDescription(answer);
    } catch (error) {
      this.options.onError?.(error);
      throw error;
    }
  }

  send(event: RealtimeEvent): void {
    if (!this.dc || this.dc.readyState !== "open") {
      throw new Error("Realtime data channel is not open");
    }
    this.dc.send(JSON.stringify(event));
  }

  close(): void {
    this.dc?.close();
    this.pc?.close();
    this.dc = null;
    this.pc = null;
    if (this.localStream) {
      this.localStream.getTracks().forEach((track) => track.stop());
      this.localStream = null;
    }
  }

  private getRealtimeUrl(): string {
    const baseUrl = this.options.baseUrl ?? "https://api.openai.com/v1/realtime/calls";
    const model = this.options.model ?? import.meta.env.VITE_REALTIME_MODEL ?? "gpt-4o-realtime-preview";
    return `${baseUrl}?model=${model}`;
  }

  private async attachAudioStream(pc: RTCPeerConnection): Promise<void> {
    try {
      this.localStream = await navigator.mediaDevices.getUserMedia({ audio: true });
      this.localStream.getAudioTracks().forEach((track) => {
        if (this.localStream) {
          pc.addTrack(track, this.localStream);
        }
      });
    } catch (error) {
      // If mic access denied/unavailable, at least negotiate audio so the model can stream.
      pc.addTransceiver("audio", { direction: "recvonly" });
      console.warn("Realtime client: microphone not available, falling back to recvonly audio", error);
    }

    // Ensure the agent can send audio even if we didn't get mic input.
    if (!pc.getTransceivers().some((t) => t.kind === "audio")) {
      pc.addTransceiver("audio", { direction: "sendrecv" });
    }
  }
}
