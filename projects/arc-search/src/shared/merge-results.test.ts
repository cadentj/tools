import { describe, expect, it } from "vitest";
import type { Category, ResultItem } from "./types";
import { mergeForTest } from "./merge-results";

function item(
  id: string,
  category: Category,
  title: string,
): ResultItem {
  return {
    id,
    category,
    title,
    subtitle: "",
    score: 1,
    actionType: "open_url",
    payload: {},
  };
}

describe("mergeAndTruncate", () => {
  it("respects category priority order", () => {
    const map = new Map<Category, ResultItem[]>([
      ["tabs", [item("t1", "tabs", "a")]],
      ["bookmarks", [item("b1", "bookmarks", "b")]],
    ]);
    const out = mergeForTest(
      map,
      {
        categoryPriority: ["bookmarks", "tabs"],
        maxPerCategory: 4,
        maxTotal: 16,
      },
      "q",
    );
    const nonWeb = out.filter((r) => r.category !== "web");
    expect(nonWeb[0]?.category).toBe("bookmarks");
    expect(nonWeb[1]?.category).toBe("tabs");
  });

  it("applies per-category and global limits", () => {
    const map = new Map<Category, ResultItem[]>([
      ["tabs", [item("t1", "tabs", "a"), item("t2", "tabs", "b")]],
      ["bookmarks", [item("b1", "bookmarks", "c")]],
    ]);
    const out = mergeForTest(
      map,
      {
        categoryPriority: ["tabs", "bookmarks"],
        maxPerCategory: 1,
        maxTotal: 2,
      },
      "q",
    );
    expect(out.filter((r) => r.category === "tabs").length).toBe(1);
    expect(out.filter((r) => r.category === "bookmarks").length).toBe(0);
    expect(out.some((r) => r.category === "web")).toBe(true);
  });

  it("keeps web-search fallback at bottom", () => {
    const map = new Map<Category, ResultItem[]>([
      ["tabs", [item("t1", "tabs", "a")]],
    ]);
    const out = mergeForTest(
      map,
      {
        categoryPriority: ["tabs"],
        maxPerCategory: 4,
        maxTotal: 16,
      },
      "hello",
    );
    expect(out[out.length - 1]?.category).toBe("web");
    expect(out[out.length - 1]?.actionType).toBe("web_search");
  });

  it("appends literal Google row then suggestion rows", () => {
    const map = new Map<Category, ResultItem[]>([
      ["tabs", [item("t1", "tabs", "a")]],
    ]);
    const out = mergeForTest(
      map,
      {
        categoryPriority: ["tabs"],
        maxPerCategory: 4,
        maxTotal: 32,
      },
      "hello",
      ["hello world", "hello kitty"],
    );
    const web = out.filter((r) => r.category === "web");
    expect(web.length).toBe(3);
    expect(web[0]?.id).toBe("web-search-literal");
    expect(web[0]?.title).toContain("Search Google");
    expect(web[1]?.title).toBe("hello world");
    expect(web[2]?.title).toBe("hello kitty");
  });
});
