import { useEffect, useRef, useState, type ReactElement } from "react";
import Sortable from "sortablejs";
import { MSG } from "../shared/messages";
import type { ExtensionMessage } from "../shared/messages";
import {
  DEFAULT_SETTINGS,
  loadSettings,
  normalizeSettings,
  saveSettings,
} from "../shared/settings";
import type { Category, OpenTarget, Settings } from "../shared/types";

const CATEGORY_LABEL: Record<Category, string> = {
  tabs: "Tabs",
  bookmarks: "Bookmarks",
  history: "History",
  web: "Web",
};

export function App(): ReactElement {
  const [settings, setSettings] = useState<Settings>(() => ({
    ...DEFAULT_SETTINGS,
    categoryPriority: [...DEFAULT_SETTINGS.categoryPriority],
  }));
  const [status, setStatus] = useState("");
  const listRef = useRef<HTMLUListElement>(null);
  const sortableRef = useRef<Sortable | null>(null);

  useEffect(() => {
    void loadSettings().then(setSettings);
  }, []);

  useEffect(() => {
    const el = listRef.current;
    if (!el) return;
    sortableRef.current?.destroy();
    sortableRef.current = Sortable.create(el, {
      animation: 150,
      ghostClass: "sortable-ghost",
    });
    return () => {
      sortableRef.current?.destroy();
      sortableRef.current = null;
    };
  }, [settings.categoryPriority]);

  async function onSave(): Promise<void> {
    const list = listRef.current;
    if (!list) return;
    const priority: Category[] = Array.from(list.querySelectorAll("li"))
      .map((li) => (li as HTMLLIElement).dataset.category as Category)
      .filter(Boolean);

    const next: Settings = normalizeSettings({
      hotkeyPreset: settings.hotkeyPreset,
      categoryPriority: priority.length ? priority : DEFAULT_SETTINGS.categoryPriority,
      maxPerCategory: settings.maxPerCategory || DEFAULT_SETTINGS.maxPerCategory,
      maxTotal: settings.maxTotal || DEFAULT_SETTINGS.maxTotal,
      openTargetByCategory: settings.openTargetByCategory,
    });

    await saveSettings(next);
    setSettings(next);
    try {
      await chrome.runtime.sendMessage({
        type: MSG.SET_HOTKEY_PRESET,
        preset: next.hotkeyPreset,
      } satisfies ExtensionMessage);
    } catch {
      // ignore
    }
    setStatus("Saved.");
    window.setTimeout(() => setStatus(""), 2000);
  }

  return (
    <div className="m-0 w-[360px] bg-[#14141a] font-sans text-[13px] leading-[1.45] text-[#e8e8ee] antialiased">
      <main className="px-4 pb-4 pt-3.5">
        <h1 className="mb-1 text-base font-[650]">Arc Search</h1>
        <p className="mb-3 text-xs text-[#9898a8]">Command bar shortcut and search behavior.</p>

        <label className="mb-3 flex flex-col gap-1.5">
          <span className="text-[11px] uppercase tracking-[0.06em] text-[#9898a8]">Hotkey preset</span>
          <select
            id="hotkey-preset"
            className="w-full rounded-lg border border-white/12 bg-white/5 px-2.5 py-2 text-inherit outline-none"
            value={settings.hotkeyPreset}
            onChange={(e) =>
              setSettings((s) => ({ ...s, hotkeyPreset: e.target.value as Settings["hotkeyPreset"] }))
            }
          >
            <option value="E">⌘/Ctrl + E</option>
            <option value="K">⌘/Ctrl + K</option>
            <option value="T">⌘/Ctrl + T (page override on web pages)</option>
          </select>
        </label>

        <div className="mb-3 flex flex-col gap-1.5">
          <span className="text-[11px] uppercase tracking-[0.06em] text-[#9898a8]">Category priority</span>
          <ul
            ref={listRef}
            id="priority-list"
            className="priority m-0 list-none overflow-hidden rounded-[10px] border border-white/10 p-0 [&_li]:cursor-grab [&_li]:border-b [&_li]:border-white/[0.06] [&_li]:bg-white/[0.04] [&_li]:px-2.5 [&_li]:py-2 [&_li]:text-xs [&_li:last-child]:border-b-0"
          >
            {settings.categoryPriority.map((c) => (
              <li key={c} data-category={c}>
                {CATEGORY_LABEL[c]}
              </li>
            ))}
          </ul>
          <p className="mt-1 text-[11px] text-[#7a7a8c]">Drag to reorder. Lower items have lower priority.</p>
        </div>

        <div className="mb-3 grid grid-cols-2 gap-2.5">
          <label className="flex flex-col gap-1.5">
            <span className="text-[11px] uppercase tracking-[0.06em] text-[#9898a8]">Max / category</span>
            <input
              id="max-per"
              type="number"
              min={0}
              max={50}
              className="w-full rounded-lg border border-white/12 bg-white/5 px-2.5 py-2 text-inherit outline-none"
              value={settings.maxPerCategory}
              onChange={(e) =>
                setSettings((s) => ({ ...s, maxPerCategory: Number(e.target.value) || s.maxPerCategory }))
              }
            />
          </label>
          <label className="flex flex-col gap-1.5">
            <span className="text-[11px] uppercase tracking-[0.06em] text-[#9898a8]">Max total</span>
            <input
              id="max-total"
              type="number"
              min={1}
              max={100}
              className="w-full rounded-lg border border-white/12 bg-white/5 px-2.5 py-2 text-inherit outline-none"
              value={settings.maxTotal}
              onChange={(e) =>
                setSettings((s) => ({ ...s, maxTotal: Number(e.target.value) || s.maxTotal }))
              }
            />
          </label>
        </div>

        <div className="mb-3 flex flex-col gap-2">
          <span className="text-[11px] uppercase tracking-[0.06em] text-[#9898a8]">Open targets</span>
          <label className="flex flex-col gap-1 text-xs text-[#c4c4d4]">
            Bookmarks
            <select
              id="open-bookmark"
              className="w-full rounded-lg border border-white/12 bg-white/5 px-2.5 py-2 text-inherit outline-none"
              value={settings.openTargetByCategory.bookmark}
              onChange={(e) =>
                setSettings((s) => ({
                  ...s,
                  openTargetByCategory: {
                    ...s.openTargetByCategory,
                    bookmark: e.target.value as OpenTarget,
                  },
                }))
              }
            >
              <option value="new_tab">New tab</option>
              <option value="current_tab">Current tab</option>
            </select>
          </label>
          <label className="flex flex-col gap-1 text-xs text-[#c4c4d4]">
            History
            <select
              id="open-history"
              className="w-full rounded-lg border border-white/12 bg-white/5 px-2.5 py-2 text-inherit outline-none"
              value={settings.openTargetByCategory.history}
              onChange={(e) =>
                setSettings((s) => ({
                  ...s,
                  openTargetByCategory: {
                    ...s.openTargetByCategory,
                    history: e.target.value as OpenTarget,
                  },
                }))
              }
            >
              <option value="new_tab">New tab</option>
              <option value="current_tab">Current tab</option>
            </select>
          </label>
          <label className="flex flex-col gap-1 text-xs text-[#c4c4d4]">
            Web search
            <select
              id="open-web"
              className="w-full rounded-lg border border-white/12 bg-white/5 px-2.5 py-2 text-inherit outline-none"
              value={settings.openTargetByCategory.web}
              onChange={(e) =>
                setSettings((s) => ({
                  ...s,
                  openTargetByCategory: {
                    ...s.openTargetByCategory,
                    web: e.target.value as OpenTarget,
                  },
                }))
              }
            >
              <option value="new_tab">New tab</option>
              <option value="current_tab">Current tab</option>
            </select>
          </label>
        </div>

        <button
          id="save"
          type="button"
          className="w-full cursor-pointer rounded-[10px] border-0 bg-gradient-to-b from-[#6ea8ff] to-[#4f87ff] px-3 py-2.5 font-[650] text-[#0b1020] hover:brightness-105"
          onClick={() => void onSave()}
        >
          Save
        </button>
        <p id="status" className="mt-2 min-h-[1.2em] text-xs text-[#8ae88a]" role="status">
          {status}
        </p>
      </main>
    </div>
  );
}
