import { RefreshCw } from "lucide-react";
import "./ErrorState.css";

interface ErrorStateProps {
  onRetry: () => void;
}

export function ErrorState({ onRetry }: ErrorStateProps) {
  return (
    <div className="error-state">
      <p className="error-state__title">Не удалось загрузить данные</p>
      <p className="error-state__desc">
        Проверьте соединение и попробуйте ещё раз.
      </p>
      <button className="btn btn-secondary error-state__btn" onClick={onRetry}>
        <RefreshCw size={18} strokeWidth={1.75} aria-hidden="true" />
        Попробовать ещё раз
      </button>
    </div>
  );
}
