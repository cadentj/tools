export type Category = "tabs" | "bookmarks" | "history" | "commands" | "web";

export type ActionType =
  | "switch_tab"
  | "open_url"
  | "run_browser_command"
  | "web_search";

export type OpenTarget = "new_tab" | "current_tab";

export type HotkeyPreset = "E" | "K" | "T";

export interface ResultItem {
  id: string;
  category: Category;
  title: string;
  subtitle: string;
  score: number;
  actionType: ActionType;
  payload: unknown;
  /** `chrome-extension://…/_favicon/` URL for tabs/bookmarks/history with http(s) pages */
  faviconUrl?: string;
}

export type BrowserCommandId =
  | "new_tab"
  | "close_tab"
  | "pin_tab"
  | "unpin_tab"
  | "duplicate_tab"
  | "new_incognito_window"
  | "close_window";

export interface Settings {
  hotkeyPreset: HotkeyPreset;
  categoryPriority: Category[];
  maxPerCategory: number;
  maxTotal: number;
  openTargetByCategory: {
    bookmark: OpenTarget;
    history: OpenTarget;
    web: OpenTarget;
  };
}
