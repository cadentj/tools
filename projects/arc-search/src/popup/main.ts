import "./popup.css";
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
  commands: "Commands",
  web: "Web",
};

function $(id: string): HTMLElement {
  const el = document.getElementById(id);
  if (!el) throw new Error(`Missing #${id}`);
  return el;
}

async function init(): Promise<void> {
  const settings = await loadSettings();

  const preset = $("hotkey-preset") as HTMLSelectElement;
  preset.value = settings.hotkeyPreset;

  const maxPer = $("max-per") as HTMLInputElement;
  maxPer.value = String(settings.maxPerCategory);

  const maxTotal = $("max-total") as HTMLInputElement;
  maxTotal.value = String(settings.maxTotal);

  const ob = $("open-bookmark") as HTMLSelectElement;
  const oh = $("open-history") as HTMLSelectElement;
  const ow = $("open-web") as HTMLSelectElement;
  ob.value = settings.openTargetByCategory.bookmark;
  oh.value = settings.openTargetByCategory.history;
  ow.value = settings.openTargetByCategory.web;

  const list = $("priority-list") as HTMLUListElement;
  list.innerHTML = "";
  for (const c of settings.categoryPriority) {
    const li = document.createElement("li");
    li.dataset.category = c;
    li.textContent = CATEGORY_LABEL[c];
    list.appendChild(li);
  }

  Sortable.create(list, {
    animation: 150,
    ghostClass: "sortable-ghost",
  });

  const status = $("status");

  $("save").addEventListener("click", async () => {
    const priority: Category[] = Array.from(list.querySelectorAll("li"))
      .map((li) => (li as HTMLLIElement).dataset.category as Category)
      .filter(Boolean);

    const next: Settings = normalizeSettings({
      hotkeyPreset: preset.value as Settings["hotkeyPreset"],
      categoryPriority: priority.length ? priority : DEFAULT_SETTINGS.categoryPriority,
      maxPerCategory: Number(maxPer.value) || DEFAULT_SETTINGS.maxPerCategory,
      maxTotal: Number(maxTotal.value) || DEFAULT_SETTINGS.maxTotal,
      openTargetByCategory: {
        bookmark: ob.value as OpenTarget,
        history: oh.value as OpenTarget,
        web: ow.value as OpenTarget,
      },
    });

    await saveSettings(next);
    try {
      await chrome.runtime.sendMessage({
        type: MSG.SET_HOTKEY_PRESET,
        preset: next.hotkeyPreset,
      } satisfies ExtensionMessage);
    } catch {
      // ignore
    }
    status.textContent = "Saved.";
    setTimeout(() => {
      status.textContent = "";
    }, 2000);
  });
}

void init();
