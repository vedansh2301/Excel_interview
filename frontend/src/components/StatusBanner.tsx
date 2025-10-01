interface StatusBannerProps {
  message?: string | null;
  tone?: "info" | "error";
}

export function StatusBanner({ message, tone = "info" }: StatusBannerProps) {
  if (!message) return null;
  const base =
    tone === "error"
      ? "bg-rose-500/10 text-rose-200 border border-rose-400/40"
      : "bg-brand-500/10 text-brand-400 border border-brand-500/40";

  return (
    <div className={`rounded-lg px-4 py-3 text-sm ${base}`}>
      {message}
    </div>
  );
}
