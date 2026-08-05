import type { ClientOption, Platform, GuideStep } from "./types";

export const CLIENTS: ClientOption[] = [
  // Android — Happ first
  {
    id: "happ-android",
    name: "Happ",
    platform: "android",
    description: "Рекомендуем",
    recommended: true,
    downloadUrl: "https://play.google.com/store/apps/details?id=com.happproxy",
  },
  {
    id: "happ-android-apk",
    name: "Happ APK",
    platform: "android",
    description: "Прямая установка без Google Play",
    downloadUrl: "https://github.com/Happ-proxy/happ-android/releases/latest/download/Happ.apk",
  },
  {
    id: "v2rayng-android",
    name: "v2rayNG",
    platform: "android",
    description: "Альтернативный клиент",
    downloadUrl: "https://github.com/2dust/v2rayNG/releases/download/1.10.31/v2rayNG_1.10.31_universal.apk",
  },

  // iOS — Happ first
  {
    id: "happ-ios",
    name: "Happ",
    platform: "ios",
    description: "Рекомендуем",
    recommended: true,
    downloadUrl: "https://apps.apple.com/ru/app/happ-proxy-utility/id6783623643",
  },
  {
    id: "streisand-ios",
    name: "Streisand",
    platform: "ios",
    description: "Альтернативный клиент",
    downloadUrl: "https://apps.apple.com/ru/app/streisand/id6450534064",
  },

  // Windows — Happ first
  {
    id: "happ-windows",
    name: "Happ",
    platform: "windows",
    description: "Рекомендуем",
    recommended: true,
    downloadUrl: "https://github.com/Happ-proxy/happ-desktop/releases/latest/download/setup-Happ.x64.exe",
  },
  {
    id: "prizrak-windows",
    name: "Prizrak-Box",
    platform: "windows",
    description: "Альтернативный клиент",
    downloadUrl: "https://github.com/legiz-ru/Prizrak-Box/releases/latest/download/windows-amd64.msi",
  },

  // macOS — Happ first
  {
    id: "happ-macos",
    name: "Happ",
    platform: "macos",
    description: "Рекомендуем",
    recommended: true,
    downloadUrl: "https://apps.apple.com/ru/app/happ-proxy-utility/id6783623643",
  },
  {
    id: "prizrak-macos",
    name: "Prizrak-Box",
    platform: "macos",
    description: "Альтернативный клиент",
    downloadUrl: "https://github.com/legiz-ru/Prizrak-Box/releases/latest/download/macos-arm64-dmg.zip",
  },
];

export const DEFAULT_GUIDE: GuideStep[] = [
  { id: "1", text: "Скачайте Happ для своего устройства" },
  { id: "2", text: "Скопируйте ссылку подписки" },
  { id: "3", text: "В Happ нажмите «+» и выберите «Добавить подписку»" },
  { id: "4", text: "Вставьте ссылку и нажмите «Подключить»" },
];

export const PLATFORM_GUIDES: Partial<Record<Platform, GuideStep[]>> = {
  android: [
    { id: "1", text: "Установите Happ из Google Play или скачайте APK" },
    { id: "2", text: "Скопируйте ссылку подписки" },
    { id: "3", text: "В Happ нажмите «+» и выберите «Добавить подписку»" },
    { id: "4", text: "Нажмите «Подключить»" },
  ],
  ios: [
    { id: "1", text: "Установите Happ из App Store" },
    { id: "2", text: "Скопируйте ссылку подписки" },
    { id: "3", text: "В Happ нажмите «+» → «Добавить подписку»" },
    { id: "4", text: "Вставьте ссылку и нажмите «Подключить»" },
  ],
  windows: [
    { id: "1", text: "Скачайте и установите Happ" },
    { id: "2", text: "Скопируйте ссылку подписки" },
    { id: "3", text: "В Happ нажмите «+» и выберите «Добавить подписку»" },
    { id: "4", text: "Вставьте ссылку и нажмите «Подключить»" },
  ],
  macos: [
    { id: "1", text: "Установите Happ из App Store" },
    { id: "2", text: "Скопируйте ссылку подписки" },
    { id: "3", text: "В Happ нажмите «+» → «Добавить подписку»" },
    { id: "4", text: "Вставьте ссылку и нажмите «Подключить»" },
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
