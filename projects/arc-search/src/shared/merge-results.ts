import type { Category, ResultItem, Settings } from "./types";

const WEB_CATEGORY: Category = "web";

const GOOGLE_HOST = "www.google.com";

function buildGoogleSearchUrl(searchQuery: string): string {
  return `https://www.google.com/search?q=${encodeURIComponent(searchQuery)}`;
}

/** Literal query row + autocomplete suggestions (deduped, max 5 from API). */
function buildWebItems(query: string, suggestions: string[]): ResultItem[] {
  const literal = makeWebSearchLiteralItem(query);
  const q = query.trim();
  const seen = new Set<string>();
  seen.add(q.toLowerCase());

  const suggestionRows: ResultItem[] = [];
  let idx = 0;
  for (const s of suggestions) {
    const t = s.trim();
    if (!t) continue;
    const k = t.toLowerCase();
    if (seen.has(k)) continue;
    seen.add(k);
    suggestionRows.push(makeWebSuggestionItem(t, idx));
    idx += 1;
  }

  return [literal, ...suggestionRows];
}

export function makeWebSearchLiteralItem(query: string): ResultItem {
  const q = query.trim();
  const url = buildGoogleSearchUrl(q || " ");

  return {
    id: "web-search-literal",
    category: WEB_CATEGORY,
    title: q || "…",
    subtitle: GOOGLE_HOST,
    score: 0,
    actionType: "web_search",
    payload: { url, query: q },
  };
}

function makeWebSuggestionItem(suggestionText: string, index: number): ResultItem {
  const url = buildGoogleSearchUrl(suggestionText);
  return {
    id: `web-suggest-${index}`,
    category: WEB_CATEGORY,
    title: suggestionText,
    subtitle: GOOGLE_HOST,
    score: 0,
    actionType: "web_search",
    payload: { url, query: suggestionText },
  };
}

export function mergeAndTruncate(
  byCategory: Map<Category, ResultItem[]>,
  settings: Settings,
  query: string,
  suggestions: string[],
): ResultItem[] {
  const maxPer = Math.max(0, settings.maxPerCategory);
  const maxTotal = Math.max(0, settings.maxTotal);
  const priority = settings.categoryPriority;

  const trimmed: ResultItem[] = [];
  for (const cat of priority) {
    if (cat === WEB_CATEGORY) continue;
    const list = byCategory.get(cat) ?? [];
    const slice = list.slice(0, maxPer);
    trimmed.push(...slice);
  }

  const webItems = buildWebItems(query, suggestions);
  const withWeb = [...trimmed, ...webItems];

  if (withWeb.length <= maxTotal) return withWeb;

  const nonWeb = withWeb.filter((r) => r.category !== WEB_CATEGORY);
  const web = withWeb.filter((r) => r.category === WEB_CATEGORY);
  const budget = Math.max(0, maxTotal - web.length);
  return [...nonWeb.slice(0, budget), ...web];
}

/** For tests: merge with the same rules as runtime. */
export function mergeForTest(
  byCategory: Map<Category, ResultItem[]>,
  settings: Partial<Settings> &
    Pick<Settings, "categoryPriority" | "maxPerCategory" | "maxTotal">,
  query: string,
  suggestions: string[] = [],
): ResultItem[] {
  const full: Settings = {
    hotkeyPreset: settings.hotkeyPreset ?? "E",
    categoryPriority: settings.categoryPriority,
    maxPerCategory: settings.maxPerCategory,
    maxTotal: settings.maxTotal,
    openTargetByCategory: {
      bookmark: "new_tab",
      history: "new_tab",
      web: "new_tab",
      ...settings.openTargetByCategory,
    },
  };
  return mergeAndTruncate(byCategory, full, query, suggestions);
}
