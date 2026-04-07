import { describe, expect, it } from "vitest";
import type { Settings } from "./types";
import { openTargetForUrlCategory } from "./open-target";

const base: Settings = {
  hotkeyPreset: "E",
  categoryPriority: ["tabs", "bookmarks", "history", "commands", "web"],
  maxPerCategory: 4,
  maxTotal: 16,
  openTargetByCategory: {
    bookmark: "new_tab",
    history: "current_tab",
    web: "new_tab",
  },
};

describe("openTargetForUrlCategory", () => {
  it("routes bookmark/history/web from settings", () => {
    expect(openTargetForUrlCategory("bookmarks", base)).toBe("new_tab");
    expect(openTargetForUrlCategory("history", base)).toBe("current_tab");
    expect(openTargetForUrlCategory("web", base)).toBe("new_tab");
  });

  it("defaults tabs and commands to new_tab", () => {
    expect(openTargetForUrlCategory("tabs", base)).toBe("new_tab");
    expect(openTargetForUrlCategory("commands", base)).toBe("new_tab");
  });
});
