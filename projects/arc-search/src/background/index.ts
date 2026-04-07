import { applyHotkeyPreset } from "./hotkeys";
import { queryResults } from "./search-pipeline";
import { MSG, type ExtensionMessage } from "../shared/messages";
import { loadSettings, normalizeSettings } from "../shared/settings";
import type { ActionType, Category, Settings } from "../shared/types";
import { openTargetForUrlCategory } from "../shared/open-target";

async function initHotkeyFromStorage(): Promise<void> {
  const s = await loadSettings();
  await applyHotkeyPreset(s.hotkeyPreset);
}

chrome.runtime.onInstalled.addListener(() => {
  void initHotkeyFromStorage();
});

chrome.runtime.onStartup.addListener(() => {
  void initHotkeyFromStorage();
});

chrome.storage.onChanged.addListener((changes, area) => {
  if (area !== "sync") return;
  if (changes.arcSearchSettings?.newValue) {
    const s = normalizeSettings(
      changes.arcSearchSettings.newValue as Partial<Settings>,
    );
    void applyHotkeyPreset(s.hotkeyPreset);
  }
});

chrome.commands.onCommand.addListener((command) => {
  if (command !== "toggle-palette") return;
  void (async () => {
    const tab = (await chrome.tabs.query({ active: true, currentWindow: true }))[0];
    if (tab?.id == null) return;
    try {
      await chrome.tabs.sendMessage(tab.id, { type: MSG.SHOW_PALETTE } satisfies ExtensionMessage);
    } catch {
      // No content script (e.g. chrome:// or restricted page).
    }
  })();
});

async function executeAction(
  actionType: ActionType,
  payload: unknown,
  settings: Settings,
): Promise<void> {
  switch (actionType) {
    case "switch_tab": {
      const { tabId, windowId } = payload as { tabId: number; windowId?: number };
      await chrome.tabs.update(tabId, { active: true });
      if (windowId != null) await chrome.windows.update(windowId, { focused: true });
      return;
    }
    case "open_url": {
      const { url, category } = payload as { url: string; category: Category };
      const target = openTargetForUrlCategory(category, settings);
      if (target === "current_tab") {
        const t = (await chrome.tabs.query({ active: true, currentWindow: true }))[0];
        if (t?.id != null) await chrome.tabs.update(t.id, { url });
      } else {
        await chrome.tabs.create({ url });
      }
      return;
    }
    case "web_search": {
      const { url } = payload as { url: string };
      const target = openTargetForUrlCategory("web", settings);
      if (target === "current_tab") {
        const t = (await chrome.tabs.query({ active: true, currentWindow: true }))[0];
        if (t?.id != null) await chrome.tabs.update(t.id, { url });
      } else {
        await chrome.tabs.create({ url });
      }
      return;
    }
    default: {
      const _exhaustive: never = actionType;
      return _exhaustive;
    }
  }
}

chrome.runtime.onMessage.addListener((message: ExtensionMessage, _sender, sendResponse) => {
  void (async () => {
    try {
      if (message.type === MSG.QUERY_RESULTS) {
        const settings = await loadSettings();
        const results = await queryResults(message.query, settings);
        sendResponse({
          type: MSG.QUERY_RESULTS_RESPONSE,
          query: message.query,
          results,
        } satisfies ExtensionMessage);
        return;
      }
      if (message.type === MSG.EXECUTE_ACTION) {
        const settings = await loadSettings();
        await executeAction(message.actionType, message.payload, settings);
        sendResponse({
          type: MSG.EXECUTE_ACTION_RESPONSE,
          ok: true,
        } satisfies ExtensionMessage);
        return;
      }
      if (message.type === MSG.SET_HOTKEY_PRESET) {
        await applyHotkeyPreset(message.preset);
        sendResponse({ applied: true });
        return;
      }
      if (message.type === MSG.GET_SETTINGS) {
        const settings = await loadSettings();
        sendResponse({
          type: MSG.GET_SETTINGS_RESPONSE,
          settings,
        } satisfies ExtensionMessage);
        return;
      }
    } catch (e) {
      const err = e instanceof Error ? e.message : String(e);
      if (message.type === MSG.QUERY_RESULTS) {
        sendResponse({
          type: MSG.QUERY_RESULTS_RESPONSE,
          query: message.query,
          results: [],
          error: err,
        } satisfies ExtensionMessage);
        return;
      }
      if (message.type === MSG.EXECUTE_ACTION) {
        sendResponse({
          type: MSG.EXECUTE_ACTION_RESPONSE,
          ok: false,
          error: err,
        } satisfies ExtensionMessage);
        return;
      }
    }
  })();
  return true;
});

