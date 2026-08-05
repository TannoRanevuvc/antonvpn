import { Send } from "lucide-react";
import "./SupportSection.css";

interface SupportSectionProps {
  supportUrl?: string;
}

function openLink(url: string) {
  try {
    const tg = (window as any).Telegram?.WebApp;
    if (tg?.openTelegramLink) {
      tg.openTelegramLink(url);
      return;
    }
    if (tg?.openLink) {
      tg.openLink(url);
      return;
    }
  } catch {/* ignore */}
  window.open(url, "_blank", "noopener,noreferrer");
}

export function SupportSection({ supportUrl }: SupportSectionProps) {
  if (!supportUrl) return null;

  return (
    <section className="support-section">
      <h2 className="support-section__title">Нужна помощь?</h2>
      <p className="support-section__desc">
        Если подключиться не получилось, опишите проблему в Telegram.
      </p>
      <button
        className="btn btn-secondary"
        onClick={() => openLink(supportUrl)}
        aria-label="Открыть помощь в Telegram"
      >
        <Send size={18} strokeWidth={1.75} aria-hidden="true" />
        Открыть помощь в Telegram
      </button>
    </section>
  );
}
