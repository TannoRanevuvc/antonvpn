import { useState } from "react";
import { ExternalLink } from "lucide-react";
import { CLIENTS, DEFAULT_GUIDE, PLATFORM_GUIDES } from "../clients";
import type { Platform } from "../types";
import "./DeviceSection.css";

const PLATFORMS: { id: Platform; label: string }[] = [
  { id: "android", label: "Android" },
  { id: "ios", label: "iOS" },
  { id: "windows", label: "Windows" },
  { id: "macos", label: "macOS" },
];

function openLink(url: string) {
  try {
    const tg = (window as any).Telegram?.WebApp;
    if (tg?.openLink) {
      tg.openLink(url);
      return;
    }
  } catch {/* ignore */}
  window.open(url, "_blank", "noopener,noreferrer");
}

interface DeviceSectionProps {
  initialPlatform: Platform;
}

export function DeviceSection({ initialPlatform }: DeviceSectionProps) {
  const [platform, setPlatform] = useState<Platform>(initialPlatform);

  const clients = CLIENTS.filter((c) => c.platform === platform);
  const guide = PLATFORM_GUIDES[platform] ?? DEFAULT_GUIDE;

  return (
    <section>
      {/* Platform tabs */}
      <div className="platform-tabs" role="tablist" aria-label="Выберите устройство">
        {PLATFORMS.map((p) => (
          <button
            key={p.id}
            role="tab"
            aria-selected={platform === p.id}
            aria-controls={`panel-${p.id}`}
            className={`platform-tab${platform === p.id ? " platform-tab--active" : ""}`}
            onClick={() => setPlatform(p.id)}
          >
            {p.label}
          </button>
        ))}
      </div>

      {/* Client list */}
      <div
        id={`panel-${platform}`}
        role="tabpanel"
        aria-label={`Клиенты для ${platform}`}
        className="client-list"
      >
        {clients.length === 0 ? (
          <div className="client-list__empty">
            <p>Для этой платформы клиент пока не указан.</p>
            <p>Обратитесь за помощью в Telegram.</p>
          </div>
        ) : (
          clients.map((client) => (
            <button
              key={client.id}
              className="client-card"
              onClick={() => openLink(client.downloadUrl)}
              aria-label={`Скачать ${client.name}${client.recommended ? " (рекомендуем)" : ""}`}
            >
              <div className="client-card__info">
                <span className="client-card__name">{client.name}</span>
                {client.description && (
                  <span className="client-card__desc">{client.description}</span>
                )}
              </div>
              <ExternalLink size={18} strokeWidth={1.75} aria-hidden="true" className="client-card__icon" />
            </button>
          ))
        )}
      </div>

      {/* Connection guide */}
      <section className="guide-section">
        <h2 className="guide-section__title">Как подключиться</h2>
        <ol className="guide-steps" aria-label="Инструкция по подключению">
          {guide.map((step, i) => (
            <li key={step.id} className="guide-step">
              <span className="guide-step__num" aria-hidden="true">
                {String(i + 1).padStart(2, "0")}
              </span>
              <span className="guide-step__text">{step.text}</span>
            </li>
          ))}
        </ol>
      </section>
    </section>
  );
}
