export type SubscriptionStatus = "active" | "expiring" | "expired" | "unknown";
export type Platform = "android" | "ios" | "windows" | "macos";
export type Theme = "light" | "dark";

export interface SubscriptionData {
  status: SubscriptionStatus;
  expiresAt?: string;
  daysRemaining?: number;
  subscriptionUrl?: string;
  supportUrl?: string;
}

export interface ClientOption {
  id: string;
  name: string;
  platform: Platform;
  description?: string;
  recommended?: boolean;
  downloadUrl: string;
}

export interface GuideStep {
  id: string;
  text: string;
}
