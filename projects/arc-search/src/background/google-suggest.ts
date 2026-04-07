const SUGGEST_BASE =
  "https://suggestqueries.google.com/complete/search?client=chrome&q=";

const MAX_SUGGESTIONS = 5;

/**
 * Fetches Google autocomplete suggestions (same endpoint Chrome's omnibox uses).
 * Returns up to {@link MAX_SUGGESTIONS} strings; [] on empty query or failure.
 */
export async function fetchGoogleSuggestions(query: string): Promise<string[]> {
  const q = query.trim();
  if (!q) return [];
  try {
    const res = await fetch(`${SUGGEST_BASE}${encodeURIComponent(q)}`);
    if (!res.ok) return [];
    const data = (await res.json()) as unknown;
    if (!Array.isArray(data) || data.length < 2) return [];
    const second = data[1];
    if (!Array.isArray(second)) return [];
    const strings = second
      .filter((x): x is string => typeof x === "string")
      .slice(0, MAX_SUGGESTIONS);
    return strings;
  } catch {
    return [];
  }
}
