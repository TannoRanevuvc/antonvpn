import { useEffect, useState, useCallback } from "react";
import { AppHeader } from "./components/AppHeader";
import { SubscriptionStatusCard } from "./components/SubscriptionStatusCard";
import { SubscriptionAccessCard } from "./components/SubscriptionAccessCard";
import { DeviceSection } from "./components/DeviceSection";
import { SupportSection } from "./components/SupportSection";
import { LoadingState } from "./components/LoadingState";
import { ErrorState } from "./components/ErrorState";
import { useTheme } from "./useTheme";
import { fetchSubscription } from "./api";
import { detectPlatform } from "./clients";
import type { SubscriptionData } from "./types";
import "./App.css";

function getShortUuid(): string {
  const parts = window.location.pathname.split("/").filter(Boolean);
  return parts[parts.length - 1] ?? "";
}

type AppState = "loading" | "loaded" | "error";

export default function App() {
  const { theme, toggleTheme } = useTheme();
  const [appState, setAppState] = useState<AppState>("loading");
  const [data, setData] = useState<SubscriptionData | null>(null);
  const platform = detectPlatform();

  const load = useCallback(async () => {
    setAppState("loading");
    try {
      const shortUuid = getShortUuid();
      if (!shortUuid) throw new Error("no uuid");
      const result = await fetchSubscription(shortUuid);
      setData(result);
      setAppState("loaded");
    } catch {
      setAppState("error");
    }
  }, []);

  useEffect(() => {
    try {
      const tg = (window as any).Telegram?.WebApp;
      if (tg) {
        tg.ready();
        tg.expand?.();
      }
    } catch {/* ignore */}
    load();
  }, [load]);

  return (
    <div className="app" data-theme={theme}>
      <div className="page">
        <AppHeader theme={theme} onToggleTheme={toggleTheme} />

        <main className="main-content">
          <div className="container content-stack">
            {appState === "loading" && <LoadingState />}
            {appState === "error" && <ErrorState onRetry={load} />}
            {appState === "loaded" && data && (
              <>
                <SubscriptionStatusCard data={data} />
                <SubscriptionAccessCard subscriptionUrl={data.subscriptionUrl} />

                <section>
                  <h2 className="section-heading">Выберите устройство</h2>
                  <DeviceSection initialPlatform={platform} />
                </section>

                <SupportSection supportUrl={data.supportUrl} />
              </>
            )}
          </div>
        </main>
      </div>
    </div>
  );
}
