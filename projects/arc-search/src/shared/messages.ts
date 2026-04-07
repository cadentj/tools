import type { ActionType } from "./types";
import type { HotkeyPreset } from "./types";
import type { ResultItem } from "./types";
import type { Settings } from "./types";

export const MSG = {
  SHOW_PALETTE: "SHOW_PALETTE",
  QUERY_RESULTS: "QUERY_RESULTS",
  QUERY_RESULTS_RESPONSE: "QUERY_RESULTS_RESPONSE",
  EXECUTE_ACTION: "EXECUTE_ACTION",
  EXECUTE_ACTION_RESPONSE: "EXECUTE_ACTION_RESPONSE",
  SET_HOTKEY_PRESET: "SET_HOTKEY_PRESET",
  GET_SETTINGS: "GET_SETTINGS",
  GET_SETTINGS_RESPONSE: "GET_SETTINGS_RESPONSE",
} as const;

export type MessageType = (typeof MSG)[keyof typeof MSG];

export type ExtensionMessage =
  | { type: typeof MSG.SHOW_PALETTE }
  | { type: typeof MSG.QUERY_RESULTS; query: string }
  | {
      type: typeof MSG.QUERY_RESULTS_RESPONSE;
      query: string;
      results: ResultItem[];
      error?: string;
    }
  | {
      type: typeof MSG.EXECUTE_ACTION;
      actionType: ActionType;
      payload: unknown;
    }
  | { type: typeof MSG.EXECUTE_ACTION_RESPONSE; ok: boolean; error?: string }
  | { type: typeof MSG.SET_HOTKEY_PRESET; preset: HotkeyPreset }
  | { type: typeof MSG.GET_SETTINGS }
  | { type: typeof MSG.GET_SETTINGS_RESPONSE; settings: Settings };
