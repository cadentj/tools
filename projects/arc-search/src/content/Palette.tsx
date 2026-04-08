import { Search } from "lucide-react";
import {
  useCallback,
  useEffect,
  useRef,
  useState,
  type ChangeEvent,
  type KeyboardEvent,
  type ReactElement,
} from "react";
import { MSG } from "../shared/messages";
import type { ExtensionMessage } from "../shared/messages";
import type { HotkeyPreset, ResultItem } from "../shared/types";
import { ResultRow } from "./ResultRow";

const DEBOUNCE_MS = 120;

function isEditableTarget(el: EventTarget | null): boolean {
  if (!el || !(el instanceof HTMLElement)) return false;
  const tag = el.tagName;
  if (tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT") return true;
  return el.isContentEditable;
}

export function Palette(): ReactElement {
  const [visible, setVisible] = useState(false);
  const visibleRef = useRef(false);
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<ResultItem[]>([]);
  const [selected, setSelected] = useState(0);
  const [hotkeyPreset, setHotkeyPreset] = useState<HotkeyPreset>("E");
  const inputRef = useRef<HTMLInputElement>(null);
  const listRef = useRef<HTMLDivElement>(null);
  const debounceTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    visibleRef.current = visible;
  }, [visible]);

  const clearDebounce = useCallback(() => {
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current);
      debounceTimerRef.current = null;
    }
  }, []);

  const refreshHotkeyPreset = useCallback(async () => {
    const data = await chrome.storage.sync.get("arcSearchSettings");
    const raw = data.arcSearchSettings as { hotkeyPreset?: HotkeyPreset } | undefined;
    if (raw?.hotkeyPreset) setHotkeyPreset(raw.hotkeyPreset);
  }, []);

  useEffect(() => {
    void refreshHotkeyPreset();
  }, [refreshHotkeyPreset]);

  useEffect(() => {
    const onStorage = (
      changes: Record<string, chrome.storage.StorageChange>,
      area: string,
    ): void => {
      if (area !== "sync") return;
      if (changes.arcSearchSettings?.newValue) {
        const v = changes.arcSearchSettings.newValue as { hotkeyPreset?: HotkeyPreset };
        if (v?.hotkeyPreset) setHotkeyPreset(v.hotkeyPreset);
      }
    };
    chrome.storage.onChanged.addListener(onStorage);
    return () => chrome.storage.onChanged.removeListener(onStorage);
  }, []);

  const lockScroll = useCallback(() => {
    document.documentElement.style.overflow = "hidden";
    document.body.style.overflow = "hidden";
  }, []);

  const unlockScroll = useCallback(() => {
    document.documentElement.style.overflow = "";
    document.body.style.overflow = "";
  }, []);

  const queryNow = useCallback(async (q: string) => {
    const res = (await chrome.runtime.sendMessage({
      type: MSG.QUERY_RESULTS,
      query: q,
    } satisfies ExtensionMessage)) as ExtensionMessage;
    if (res.type !== MSG.QUERY_RESULTS_RESPONSE) return;
    if (!visibleRef.current) return;
    setResults(res.results);
    setSelected(0);
  }, []);

  const hidePalette = useCallback(() => {
    clearDebounce();
    setVisible(false);
    unlockScroll();
  }, [clearDebounce, unlockScroll]);

  const showPalette = useCallback(() => {
    clearDebounce();
    setVisible(true);
    lockScroll();
    setQuery("");
    setResults([]);
    setSelected(0);
    void queryNow("");
    requestAnimationFrame(() => {
      inputRef.current?.focus();
      inputRef.current?.select();
    });
  }, [clearDebounce, lockScroll, queryNow]);

  useEffect(() => {
    const onMsg = (message: ExtensionMessage): void => {
      if (message.type === MSG.SHOW_PALETTE) showPalette();
    };
    chrome.runtime.onMessage.addListener(onMsg);
    return () => chrome.runtime.onMessage.removeListener(onMsg);
  }, [showPalette]);

  useEffect(() => {
    const onGlobalKeydown = (ev: Event): void => {
      if (!hotkeyPreset || hotkeyPreset !== "T") return;
      const kev = ev as globalThis.KeyboardEvent;
      const isMac = navigator.platform.toLowerCase().includes("mac");
      const mod = isMac ? kev.metaKey : kev.ctrlKey;
      if (!mod || kev.key.toLowerCase() !== "t") return;
      if (isEditableTarget(kev.target)) return;
      kev.preventDefault();
      kev.stopPropagation();
      showPalette();
    };
    window.addEventListener("keydown", onGlobalKeydown, true);
    return () => window.removeEventListener("keydown", onGlobalKeydown, true);
  }, [hotkeyPreset, showPalette]);

  useEffect(() => {
    if (!listRef.current) return;
    const row = listRef.current.children[selected] as HTMLElement | undefined;
    row?.scrollIntoView({ block: "nearest" });
  }, [selected, results]);

  const handleInputChange = useCallback(
    (e: ChangeEvent<HTMLInputElement>) => {
      const v = e.target.value;
      setQuery(v);
      clearDebounce();
      debounceTimerRef.current = setTimeout(() => {
        debounceTimerRef.current = null;
        void queryNow(v);
      }, DEBOUNCE_MS);
    },
    [clearDebounce, queryNow],
  );

  const executeAt = useCallback(
    async (idx: number) => {
      const item = results[idx];
      if (!item) return;
      await chrome.runtime.sendMessage({
        type: MSG.EXECUTE_ACTION,
        actionType: item.actionType,
        payload: item.payload,
      } satisfies ExtensionMessage);
      hidePalette();
    },
    [results, hidePalette],
  );

  const onRowActivate = useCallback(
    (idx: number) => {
      void executeAt(idx);
    },
    [executeAt],
  );

  const onInputKeydown = useCallback(
    (ev: KeyboardEvent<HTMLInputElement>) => {
      if (!visible) return;
      if (ev.key === "Escape") {
        ev.preventDefault();
        hidePalette();
        return;
      }
      if (ev.key === "ArrowDown") {
        ev.preventDefault();
        if (results.length === 0) return;
        setSelected((s) => Math.min(results.length - 1, s + 1));
        return;
      }
      if (ev.key === "ArrowUp") {
        ev.preventDefault();
        if (results.length === 0) return;
        setSelected((s) => Math.max(0, s - 1));
        return;
      }
      if (ev.key === "Enter") {
        ev.preventDefault();
        void executeAt(selected);
      }
    },
    [visible, hidePalette, results.length, executeAt, selected],
  );

  const trapKeyboard = useCallback((ev: KeyboardEvent<HTMLDivElement>) => {
    if (visibleRef.current) ev.stopPropagation();
  }, []);

  return (
    <div
      className="pointer-events-auto fixed inset-0 z-[2147483646] flex items-center justify-center"
      style={{ display: visible ? "flex" : "none" }}
      onKeyDown={trapKeyboard}
      onKeyUp={trapKeyboard}
    >
      <div
        className="absolute inset-0 bg-black/40 backdrop-blur-[10px]"
        onClick={() => hidePalette()}
        aria-hidden
      />
      <div className="origin-center scale-115">
        <div className="relative w-[min(640px,92vw)] overflow-hidden rounded-[14px] border border-solid border-white/20 bg-zinc-950/90 shadow-2xl shadow-black/50 ring-1 ring-inset ring-white/10 px-2">
          {/* Search Bar */}
          <div className="flex items-center gap-3 border-b border-solid border-white/15 px-3 py-4">
            <Search className="size-3 stroke-3 bold shrink-0 text-white" aria-hidden />
            <input
              ref={inputRef}
              className="min-w-0 flex-1 border-none bg-transparent text-lg text-white/95 outline-none placeholder:text-white/55"
              type="text"
              placeholder="Search or Enter URL..."
              autoComplete="off"
              spellCheck={false}
              value={query}
              onChange={handleInputChange}
              onKeyDown={onInputKeydown}
            />
          </div>
          <div
            ref={listRef}
            className="list-scroll space-y-1 overflow-y-auto"
            style={{ maxHeight: "252px" }}
          >
            {results.length === 0 ? (
              <div className="px-4 py-3.5 text-sm text-white/55">No matches</div>
            ) : (
              results.map((r, idx) => (
                <ResultRow
                  key={r.id}
                  r={r}
                  idx={idx}
                  selected={idx === selected}
                  onActivate={onRowActivate}
                />
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
