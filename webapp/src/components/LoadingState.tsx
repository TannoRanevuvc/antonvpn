import "./LoadingState.css";

export function LoadingState() {
  return (
    <div className="loading-state">
      <div className="skeleton skeleton--card" />
      <div className="skeleton skeleton--card skeleton--tall" />
      <div className="skeleton skeleton--card" />
      <p className="loading-state__text">Загружаем данные подписки…</p>
    </div>
  );
}
