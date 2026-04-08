import uFuzzy from "@leeoniya/ufuzzy";
import type { Category, ResultItem, Settings } from "../shared/types";
import { mergeAndTruncate } from "../shared/merge-results";
import { fetchGoogleSuggestions } from "./google-suggest";

const uf = new uFuzzy();

type Candidate = {
  id: string;
  category: Category;
  title: string;
  subtitle: string;
  actionType: ResultItem["actionType"];
  payload: unknown;
  faviconUrl?: string;
};

function googleFaviconUrl(pageUrl: string): string | undefined {
  try {
    const { hostname } = new URL(pageUrl);
    if (!hostname) return undefined;
    return `https://www.google.com/s2/favicons?domain=${encodeURIComponent(hostname)}&sz=32`;
  } catch {
    return undefined;
  }
}

function rankIndices(haystack: string[], needle: string): number[] {
  const q = needle.trim();
  if (!q) return haystack.map((_, i) => i);
  const result = uf.search(haystack, q);
  const idxs = result[0];
  if (!idxs?.length) return [];
  const info = result[1];
  const order = result[2];
  if (info && order) return order.map((i) => idxs[i]!);
  return idxs;
}

function toResult(
  c: Candidate,
  score: number,
): ResultItem {
  return {
    id: c.id,
    category: c.category,
    title: c.title,
    subtitle: c.subtitle,
    score,
    actionType: c.actionType,
    payload: c.payload,
    faviconUrl: c.faviconUrl,
  };
}

function isInternalUrl(url: string): boolean {
  return /^(chrome|edge|brave|about|chrome-extension):\/\//i.test(url);
}

async function collectTabs(): Promise<Candidate[]> {
  const tabs = await chrome.tabs.query({});
  const out: Candidate[] = [];
  for (const t of tabs) {
    if (t.id == null) continue;
    const url = t.url || "";
    if (isInternalUrl(url)) continue;
    const title = t.title || "Untitled";
    out.push({
      id: `tab-${t.id}`,
      category: "tabs",
      title,
      subtitle: url,
      actionType: "switch_tab",
      payload: { tabId: t.id, windowId: t.windowId },
      faviconUrl: t.favIconUrl || googleFaviconUrl(url),
    });
  }
  return out;
}

async function collectBookmarks(): Promise<Candidate[]> {
  const flat = await flattenBookmarks();
  return flat.map((b) => ({
    id: `bm-${b.id}`,
    category: "bookmarks" as const,
    title: b.title || b.url || "Bookmark",
    subtitle: b.url,
    actionType: "open_url" as const,
    payload: { url: b.url, category: "bookmarks" as const },
    faviconUrl: googleFaviconUrl(b.url),
  }));
}

async function flattenBookmarks(): Promise<{ id: string; title: string; url: string }[]> {
  const tree = await chrome.bookmarks.getTree();
  const out: { id: string; title: string; url: string }[] = [];
  const walk = (nodes: chrome.bookmarks.BookmarkTreeNode[]) => {
    for (const n of nodes) {
      if (n.url) out.push({ id: n.id, title: n.title, url: n.url });
      if (n.children) walk(n.children);
    }
  };
  walk(tree);
  return out.slice(0, 2000);
}

async function collectHistory(): Promise<Candidate[]> {
  const items = await chrome.history.search({
    text: "",
    maxResults: 10000,
    startTime: Date.now() - 90 * 24 * 60 * 60 * 1000,
  });
  return items
    .filter((h) => h.url && !isInternalUrl(h.url))
    .map((h) => ({
      id: `hist-${h.url}-${h.lastVisitTime}`,
      category: "history" as const,
      title: h.title || h.url || "History",
      subtitle: h.url || "",
      actionType: "open_url" as const,
      payload: { url: h.url, category: "history" as const },
      faviconUrl: h.url ? googleFaviconUrl(h.url) : undefined,
    }));
}

function scoreFromRankIndex(len: number, rankIndex: number): number {
  if (len <= 1) return 1;
  return 1 - rankIndex / (len - 1);
}

export async function queryResults(
  rawQuery: string,
  settings: Settings,
): Promise<ResultItem[]> {
  const query = rawQuery.trim();
  const [tabs, bookmarks, history, suggestions] = await Promise.all([
    collectTabs(),
    collectBookmarks(),
    collectHistory(),
    fetchGoogleSuggestions(query),
  ]);

  const tabHay = tabs.map((t) => `${t.title}\n${t.subtitle}`);
  const bmHay = bookmarks.map((b) => `${b.title}\n${b.subtitle}`);
  const histHay = history.map((h) => `${h.title}\n${h.subtitle}`);

  const tabOrder = rankIndices(tabHay, query);
  const bmOrder = rankIndices(bmHay, query);
  const histOrder = rankIndices(histHay, query);

  const byCategory = new Map<Category, ResultItem[]>();

  function pushRanked(
    category: Category,
    candidates: Candidate[],
    order: number[],
  ) {
    if (order.length === 0) {
      byCategory.set(category, []);
      return;
    }
    const items: ResultItem[] = order.map((idx, rankIdx) => {
      const c = candidates[idx]!;
      return toResult(c, scoreFromRankIndex(order.length, rankIdx));
    });
    byCategory.set(category, items);
  }

  pushRanked("tabs", tabs, tabOrder);
  pushRanked("bookmarks", bookmarks, bmOrder);
  pushRanked("history", history, histOrder);

  return mergeAndTruncate(byCategory, settings, query, suggestions);
}
