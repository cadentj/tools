import type { Category, OpenTarget, Settings } from "./types";

export function openTargetForUrlCategory(
  category: Category,
  settings: Settings,
): OpenTarget {
  if (category === "bookmarks") return settings.openTargetByCategory.bookmark;
  if (category === "history") return settings.openTargetByCategory.history;
  if (category === "web") return settings.openTargetByCategory.web;
  return "new_tab";
}
