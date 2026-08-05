import { Moon, Sun } from "lucide-react";
import { PortalMark } from "./PortalMark";
import type { Theme } from "../types";
import "./AppHeader.css";

interface AppHeaderProps {
  theme: Theme;
  onToggleTheme: () => void;
}

export function AppHeader({ theme, onToggleTheme }: AppHeaderProps) {
  return (
    <header className="app-header">
      <div className="container app-header__inner">
        <div className="app-header__brand">
          <div className="app-header__logo">
            <PortalMark size={32} color="var(--color-accent-dark)" />
          </div>
          <div>
            <div className="app-header__name">AntonVPN</div>
            <div className="app-header__sub">Ваша подписка</div>
          </div>
        </div>
        <button
          className="btn-icon"
          onClick={onToggleTheme}
          aria-label={theme === "dark" ? "Включить светлую тему" : "Включить тёмную тему"}
        >
          {theme === "dark" ? <Sun size={20} strokeWidth={1.75} /> : <Moon size={20} strokeWidth={1.75} />}
        </button>
      </div>
    </header>
  );
}
