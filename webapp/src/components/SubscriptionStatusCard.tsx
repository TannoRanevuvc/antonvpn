import type { SubscriptionData } from "../types";
import "./SubscriptionStatusCard.css";

const EXPIRING_THRESHOLD_DAYS = 3;

function formatDate(iso: string): string {
  try {
    const dt = new Date(iso);
    return dt.toLocaleDateString("ru-RU", {
      day: "numeric",
      month: "long",
      year: "numeric",
    });
  } catch {
    return iso.slice(0, 10);
  }
}

function formatDaysLeft(days: number): string {
  if (days <= 0) return "истекла";
  if (days === 1) return "1 день";
  if (days < 5) return `${days} дня`;
  return `${days} дней`;
}

interface SubscriptionStatusCardProps {
  data: SubscriptionData;
}

export function SubscriptionStatusCard({ data }: SubscriptionStatusCardProps) {
  const { status, expiresAt, daysRemaining } = data;
  const days = daysRemaining ?? 0;
  const isExpiring = status === "expiring" || (status === "active" && days <= EXPIRING_THRESHOLD_DAYS);
  const dateStr = expiresAt ? formatDate(expiresAt) : null;

  if (status === "unknown") {
    return (
      <div className="card status-card status-card--unknown">
        <p className="status-card__headline">Не удалось определить статус</p>
        <p className="status-card__secondary">Обновите страницу или вернитесь в Telegram-бот.</p>
      </div>
    );
  }

  if (status === "expired") {
    return (
      <div className="card status-card status-card--expired">
        <div className="status-card__badge status-card__badge--error">Неактивна</div>
        <p className="status-card__headline">Подписка неактивна</p>
        <p className="status-card__secondary">
          Вернитесь в Telegram-бот, чтобы проверить доступ.
        </p>
      </div>
    );
  }

  if (isExpiring) {
    return (
      <div className="card status-card status-card--expiring">
        <div className="status-card__badge status-card__badge--warning">Активна</div>
        <p className="status-card__headline">Подписка скоро закончится</p>
        {dateStr && <p className="status-card__date">Активна до {dateStr}</p>}
        {days > 0 && (
          <p className="status-card__days status-card__days--warning">
            Осталось {formatDaysLeft(days)}
          </p>
        )}
      </div>
    );
  }

  // active
  return (
    <div className="card status-card status-card--active">
      <div className="status-card__badge status-card__badge--success">Активна</div>
      <p className="status-card__headline">Всё спокойно</p>
      <p className="status-card__secondary">Подписка активна</p>
      {dateStr && <p className="status-card__date">До {dateStr}</p>}
      {days > 0 && (
        <p className="status-card__days">Осталось {formatDaysLeft(days)}</p>
      )}
    </div>
  );
}
