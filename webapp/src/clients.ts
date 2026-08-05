import type { ClientOption, Platform, GuideStep } from "./types";

export const CLIENTS: ClientOption[] = [
  {
    id: "hiddify-android",
    name: "Hiddify",
    platform: "android",
    description: "Рекомендуем",
    recommended: true,
    downloadUrl: "https://play.google.com/store/apps/details?id=app.hiddify.com",
  },
  {
    id: "v2rayng-android",
    name: "v2rayNG",
    platform: "android",
    description: "Альтернативный клиент",
    downloadUrl: "https://play.google.com/store/apps/details?id=com.v2ray.ang",
  },
  {
    id: "streisand-ios",
    name: "Streisand",
    platform: "ios",
    description: "Рекомендуем, бесплатный",
    recommended: true,
    downloadUrl: "https://apps.apple.com/app/streisand/id6450534064",
  },
  {
    id: "shadowrocket-ios",
    name: "Shadowrocket",
    platform: "ios",
    description: "Альтернативный клиент, $2.99",
    downloadUrl: "https://apps.apple.com/app/shadowrocket/id932747118",
  },
  {
    id: "hiddify-windows",
    name: "Hiddify",
    platform: "windows",
    description: "Рекомендуем",
    recommended: true,
    downloadUrl: "https://github.com/hiddify/hiddify-app/releases/latest",
  },
  {
    id: "nekoray-windows",
    name: "NekoRay",
    platform: "windows",
    description: "Альтернативный клиент",
    downloadUrl: "https://github.com/MatsuriDayo/nekoray/releases/latest",
  },
  {
    id: "hiddify-macos",
    name: "Hiddify",
    platform: "macos",
    description: "Рекомендуем",
    recommended: true,
    downloadUrl: "https://github.com/hiddify/hiddify-app/releases/latest",
  },
  {
    id: "streisand-macos",
    name: "Streisand",
    platform: "macos",
    description: "Альтернативный клиент",
    downloadUrl: "https://apps.apple.com/app/streisand/id6450534064",
  },
];

export const DEFAULT_GUIDE: GuideStep[] = [
  { id: "1", text: "Скачайте клиент для своего устройства" },
  { id: "2", text: "Скопируйте ссылку подписки" },
  { id: "3", text: "Откройте клиент и выберите «Добавить подписку»" },
  { id: "4", text: "Вставьте ссылку и подключитесь" },
];

export const PLATFORM_GUIDES: Partial<Record<Platform, GuideStep[]>> = {
  android: [
    { id: "1", text: "Установите Hiddify из Google Play" },
    { id: "2", text: "Скопируйте ссылку подписки" },
    { id: "3", text: "В Hiddify нажмите «+» и выберите «Добавить из буфера обмена»" },
    { id: "4", text: "Нажмите «Подключить»" },
  ],
  ios: [
    { id: "1", text: "Установите Streisand из App Store" },
    { id: "2", text: "Скопируйте ссылку подписки" },
    { id: "3", text: "В Streisand нажмите «+» → «Добавить подписку»" },
    { id: "4", text: "Вставьте ссылку и нажмите «Подключить»" },
  ],
  windows: [
    { id: "1", text: "Скачайте Hiddify с GitHub" },
    { id: "2", text: "Скопируйте ссылку подписки" },
    { id: "3", text: "В Hiddify нажмите «+» и выберите «Добавить ссылку»" },
    { id: "4", text: "Вставьте ссылку и нажмите «Подключить»" },
  ],
  macos: [
    { id: "1", text: "Установите Hiddify или Streisand" },
    { id: "2", text: "Скопируйте ссылку подписки" },
    { id: "3", text: "Откройте клиент и добавьте подписку" },
    { id: "4", text: "Выберите сервер и нажмите «Подключить»" },
  ],
};

export function detectPlatform(): Platform {
  if (typeof navigator === "undefined") return "android";
  const ua = navigator.userAgent.toLowerCase();
  if (/iphone|ipad|ipod/.test(ua)) return "ios";
  if (/macintosh|mac os x/.test(ua)) return "macos";
  if (/windows/.test(ua)) return "windows";
  return "android";
}
