export const locales = [
  "en",
  "es",
  "fr",
  "de",
  "pt",
  "zh-CN",
  "zh-TW",
  "ja",
  "ko",
  "ar",
  "hi",
  "ru",
  "it",
  "nl",
  "tr",
] as const;

export type Locale = (typeof locales)[number];

export const defaultLocale: Locale = "en";
