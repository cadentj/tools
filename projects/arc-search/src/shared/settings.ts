import type { Category, Settings } from "./types";

export const DEFAULT_CATEGORY_PRIORITY: Category[] = [
  "tabs",
  "bookmarks",
  "history",
  "web",
];

export const DEFAULT_SETTINGS: Settings = {
  hotkeyPreset: "E",
  categoryPriority: [...DEFAULT_CATEGORY_PRIORITY],
  maxPerCategory: 4,
  maxTotal: 16,
  openTargetByCategory: {
    bookmark: "new_tab",
    history: "new_tab",
    web: "new_tab",
  },
};

const SETTINGS_KEY = "arcSearchSettings";

export async function loadSettings(): Promise<Settings> {
  const data = await chrome.storage.sync.get(SETTINGS_KEY);
  const raw = data[SETTINGS_KEY] as Partial<Settings> | undefined;
  if (!raw) return { ...DEFAULT_SETTINGS, categoryPriority: [...DEFAULT_CATEGORY_PRIORITY] };
  return normalizeSettings(raw);
}

export async function saveSettings(settings: Settings): Promise<void> {
  await chrome.storage.sync.set({ [SETTINGS_KEY]: settings });
}

export function normalizeSettings(partial: Partial<Settings>): Settings {
  const priority =
    partial.categoryPriority && partial.categoryPriority.length > 0
      ? mergeCategoryOrder(partial.categoryPriority)
      : [...DEFAULT_CATEGORY_PRIORITY];
  return {
    ...DEFAULT_SETTINGS,
    hotkeyPreset: partial.hotkeyPreset ?? DEFAULT_SETTINGS.hotkeyPreset,
    categoryPriority: priority,
    maxPerCategory: partial.maxPerCategory ?? DEFAULT_SETTINGS.maxPerCategory,
    maxTotal: partial.maxTotal ?? DEFAULT_SETTINGS.maxTotal,
    openTargetByCategory: {
      ...DEFAULT_SETTINGS.openTargetByCategory,
      ...partial.openTargetByCategory,
    },
  };
}

function mergeCategoryOrder(userOrder: Category[]): Category[] {
  const seen = new Set<Category>();
  const out: Category[] = [];
  for (const c of userOrder) {
    if (DEFAULT_CATEGORY_PRIORITY.includes(c) && !seen.has(c)) {
      seen.add(c);
      out.push(c);
    }
  }
  for (const c of DEFAULT_CATEGORY_PRIORITY) {
    if (!seen.has(c)) out.push(c);
  }
  return out;
}
