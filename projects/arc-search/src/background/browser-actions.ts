import type { BrowserCommandId } from "../shared/types";

export async function runBrowserCommand(command: BrowserCommandId): Promise<void> {
  const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
  const tab = tabs[0];

  switch (command) {
    case "new_tab":
      await chrome.tabs.create({});
      return;
    case "close_tab":
      if (tab?.id != null) await chrome.tabs.remove(tab.id);
      return;
    case "pin_tab":
      if (tab?.id != null) await chrome.tabs.update(tab.id, { pinned: true });
      return;
    case "unpin_tab":
      if (tab?.id != null) await chrome.tabs.update(tab.id, { pinned: false });
      return;
    case "duplicate_tab":
      if (tab?.id != null) await chrome.tabs.duplicate(tab.id);
      return;
    case "new_incognito_window":
      await chrome.windows.create({ incognito: true });
      return;
    case "close_window": {
      const w = await chrome.windows.getCurrent();
      if (w.id != null) await chrome.windows.remove(w.id);
      return;
    }
    default: {
      const _exhaustive: never = command;
      return _exhaustive;
    }
  }
}
