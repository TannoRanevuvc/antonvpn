import type { SubscriptionData, SubscriptionStatus } from "./types";

interface ApiResponse {
  status: string;
  expires_at?: string;
  days_remaining?: number;
  subscription_url?: string;
  support_url?: string;
}

function normalizeStatus(raw: string): SubscriptionStatus {
  const s = raw.toLowerCase();
  if (s === "active") return "active";
  if (s === "expiring") return "expiring";
  if (s === "disabled" || s === "expired") return "expired";
  return "unknown";
}

export async function fetchSubscription(shortUuid: string): Promise<SubscriptionData> {
  const resp = await fetch(`/sub/api/${shortUuid}`, {
    headers: { Accept: "application/json" },
  });
  if (!resp.ok) {
    throw new Error(`HTTP ${resp.status}`);
  }
  const data: ApiResponse = await resp.json();
  return {
    status: normalizeStatus(data.status),
    expiresAt: data.expires_at,
    daysRemaining: data.days_remaining,
    subscriptionUrl: data.subscription_url,
    supportUrl: data.support_url,
  };
}
