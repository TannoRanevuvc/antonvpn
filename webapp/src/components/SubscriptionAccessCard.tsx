import { useEffect, useRef, useState } from "react";
import { Copy, Check, AlertCircle, Zap } from "lucide-react";
import QRCode from "qrcode";
import "./SubscriptionAccessCard.css";

interface SubscriptionAccessCardProps {
  subscriptionUrl?: string;
}

function maskUrl(url: string): string {
  try {
    const u = new URL(url);
    const path = u.pathname;
    const parts = path.split("/");
    const last = parts[parts.length - 1];
    const masked = last.slice(0, 8) + "•".repeat(Math.max(0, last.length - 8));
    parts[parts.length - 1] = masked;
    return u.hostname + parts.join("/");
  } catch {
    const idx = url.indexOf("/sub/");
    if (idx === -1) return url.slice(0, 30) + "…";
    return url.slice(0, idx + 13) + "•".repeat(8) + "…";
  }
}

async function copyToClipboard(text: string): Promise<void> {
  if (navigator.clipboard?.writeText) {
    await navigator.clipboard.writeText(text);
    return;
  }
  const el = document.createElement("textarea");
  el.value = text;
  el.style.position = "fixed";
  el.style.opacity = "0";
  el.style.top = "-9999px";
  document.body.appendChild(el);
  el.select();
  document.execCommand("copy");
  document.body.removeChild(el);
}

function openHapp(subscriptionUrl: string) {
  const deepLink = `happ://add/${encodeURIComponent(subscriptionUrl)}`;
  // Try Telegram WebApp openLink first, then window.location
  try {
    const tg = (window as any).Telegram?.WebApp;
    if (tg?.openLink) {
      tg.openLink(deepLink);
      return;
    }
  } catch {/* ignore */}
  window.location.href = deepLink;
}

type CopyState = "idle" | "success" | "error";

export function SubscriptionAccessCard({ subscriptionUrl }: SubscriptionAccessCardProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [copyState, setCopyState] = useState<CopyState>("idle");
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    if (!subscriptionUrl || !canvasRef.current) return;
    QRCode.toCanvas(canvasRef.current, subscriptionUrl, {
      width: 200,
      margin: 2,
      color: { dark: "#000000", light: "#ffffff" },
      errorCorrectionLevel: "M",
    }).catch(() => {/* ignore */});
  }, [subscriptionUrl]);

  useEffect(() => {
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, []);

  async function handleCopy() {
    if (!subscriptionUrl) return;
    try {
      await copyToClipboard(subscriptionUrl);
      setCopyState("success");
      timerRef.current = setTimeout(() => setCopyState("idle"), 2000);
    } catch {
      setCopyState("error");
      timerRef.current = setTimeout(() => setCopyState("idle"), 3000);
    }
  }

  if (!subscriptionUrl) {
    return (
      <div className="card access-card">
        <h2 className="access-card__title">Ссылка подписки</h2>
        <div className="access-card__empty">
          <AlertCircle size={24} strokeWidth={1.75} aria-hidden="true" />
          <p>Ссылка подписки недоступна</p>
          <p className="access-card__empty-hint">
            Вернитесь в Telegram-бот или обратитесь за помощью.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="card access-card">
      <h2 className="access-card__title">Ссылка подписки</h2>

      <div className="access-card__qr">
        <canvas ref={canvasRef} aria-label="QR-код подписки" />
      </div>

      <div className="access-card__url-row">
        <span className="access-card__url" title={subscriptionUrl}>
          {maskUrl(subscriptionUrl)}
        </span>
      </div>

      <button
        className={`btn btn-primary${copyState === "success" ? " btn-success" : ""}`}
        onClick={handleCopy}
        disabled={copyState === "success"}
        aria-live="polite"
      >
        {copyState === "success" ? (
          <>
            <Check size={18} strokeWidth={2} aria-hidden="true" />
            Скопировано
          </>
        ) : (
          <>
            <Copy size={18} strokeWidth={1.75} aria-hidden="true" />
            Скопировать ссылку
          </>
        )}
      </button>

      <button
        className="btn btn-happ"
        onClick={() => openHapp(subscriptionUrl)}
        aria-label="Открыть в Happ"
      >
        <Zap size={18} strokeWidth={1.75} aria-hidden="true" />
        Открыть в Happ
      </button>

      {copyState === "error" && (
        <p className="access-card__copy-error" role="alert">
          Не удалось скопировать ссылку. Выделите её вручную.
        </p>
      )}

      <div role="status" aria-live="polite" className="sr-only">
        {copyState === "success" ? "Ссылка скопирована" : ""}
      </div>
    </div>
  );
}
