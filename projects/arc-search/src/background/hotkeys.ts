import type { HotkeyPreset } from "../shared/types";

/** Chrome accepts Ctrl+…; on macOS this maps to Command+… for extension shortcuts. */
const SHORTCUT_BY_PRESET: Record<HotkeyPreset, string> = {
  E: "Ctrl+E",
  K: "Ctrl+K",
  T: "Ctrl+T",
};

export async function applyHotkeyPreset(preset: HotkeyPreset): Promise<void> {
  const shortcut = SHORTCUT_BY_PRESET[preset];
  try {
    await chrome.commands.update({
      name: "toggle-palette",
      shortcut,
    });
  } catch {
    // Ctrl+T may be rejected on some channels; content script handles preset T on http(s) pages.
  }
}
