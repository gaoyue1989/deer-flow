import { formatDistanceToNow } from "date-fns";
import { enUS as dateFnsEnUS, zhCN as dateFnsZhCN } from "date-fns/locale";

import { detectLocale, type Locale } from "@/core/i18n";
import { getLocaleFromCookie } from "@/core/i18n/cookies";

function getDateFnsLocale(locale: Locale) {
  switch (locale) {
    case "zh-CN":
      return dateFnsZhCN;
    case "en-US":
    default:
      return dateFnsEnUS;
  }
}

export function formatTimeAgo(date: Date | string | number, locale?: Locale) {
  // Guard against invalid dates
  if (!date || (typeof date === "string" && date.trim() === "")) {
    return "";
  }

  const parsedDate =
    typeof date === "number" ? new Date(date * 1000) : new Date(date);
  if (isNaN(parsedDate.getTime())) {
    return "";
  }

  const effectiveLocale =
    locale ??
    (getLocaleFromCookie() as Locale | null) ??
    // Fallback when cookie is missing (or on first render)
    detectLocale();
  return formatDistanceToNow(parsedDate, {
    addSuffix: true,
    locale: getDateFnsLocale(effectiveLocale),
  });
}
