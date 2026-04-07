import styles from "./palette.css?inline";
import { MSG } from "../shared/messages";
import type { ExtensionMessage } from "../shared/messages";
import type { Category, HotkeyPreset, ResultItem } from "../shared/types";

const DEBOUNCE_MS = 120;

const ROW_BASE =
  "flex min-w-0 cursor-pointer items-center gap-3 rounded-lg px-4 py-2.5 transition-colors";
const ROW_IDLE = "bg-transparent hover:bg-white/[0.08]";
const ROW_SELECTED = "bg-[rgba(80,140,255,0.22)]";

let host: HTMLDivElement | null = null;
let shadow: ShadowRoot | null = null;
let wrapEl: HTMLDivElement | null = null;
let inputEl: HTMLInputElement | null = null;
let listEl: HTMLDivElement | null = null;
let visible = false;
let results: ResultItem[] = [];
let selected = 0;
let debounceTimer: ReturnType<typeof setTimeout> | null = null;
let hotkeyPreset: HotkeyPreset = "E";

function isEditableTarget(el: EventTarget | null): boolean {
  if (!el || !(el instanceof HTMLElement)) return false;
  const tag = el.tagName;
  if (tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT") return true;
  return el.isContentEditable;
}

async function refreshHotkeyPreset(): Promise<void> {
  const data = await chrome.storage.sync.get("arcSearchSettings");
  const raw = data.arcSearchSettings as { hotkeyPreset?: HotkeyPreset } | undefined;
  if (raw?.hotkeyPreset) hotkeyPreset = raw.hotkeyPreset;
}

chrome.storage.onChanged.addListener((changes, area) => {
  if (area !== "sync") return;
  if (changes.arcSearchSettings?.newValue) {
    const v = changes.arcSearchSettings.newValue as { hotkeyPreset?: HotkeyPreset };
    if (v?.hotkeyPreset) hotkeyPreset = v.hotkeyPreset;
  }
});

void refreshHotkeyPreset();

/** Middle-truncate URL for single-line display (Arc-style). */
function truncateUrl(url: string, maxLen = 56): string {
  let s = url.replace(/^https?:\/\//i, "").replace(/^www\./i, "");
  if (s.length <= maxLen) return s;
  const slash = s.indexOf("/");
  if (slash === -1) {
    return s.slice(0, Math.max(0, maxLen - 1)) + "…";
  }
  const domain = s.slice(0, slash);
  const path = s.slice(slash + 1);
  const head = 15;
  const tail = 20;
  if (domain.length + 1 + path.length <= maxLen) return s;
  if (path.length <= head + tail) return `${domain}/${path}`;
  return `${domain}/${path.slice(0, head)}…${path.slice(-tail)}`;
}

function svgIconSearch(): SVGElement {
  const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  svg.setAttribute("width", "16");
  svg.setAttribute("height", "16");
  svg.setAttribute("viewBox", "0 0 24 24");
  svg.setAttribute("fill", "none");
  svg.setAttribute("class", "h-5 w-5 shrink-0 text-white/70");
  svg.setAttribute("stroke", "currentColor");
  svg.setAttribute("stroke-width", "2");
  svg.setAttribute("stroke-linecap", "round");
  const c = document.createElementNS("http://www.w3.org/2000/svg", "circle");
  c.setAttribute("cx", "11");
  c.setAttribute("cy", "11");
  c.setAttribute("r", "7");
  const p = document.createElementNS("http://www.w3.org/2000/svg", "path");
  p.setAttribute("d", "m20 20-3-3");
  svg.appendChild(c);
  svg.appendChild(p);
  return svg;
}

function svgIconCommand(): SVGElement {
  const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  svg.setAttribute("width", "16");
  svg.setAttribute("height", "16");
  svg.setAttribute("viewBox", "0 0 24 24");
  svg.setAttribute("fill", "none");
  svg.setAttribute("class", "h-5 w-5 shrink-0 text-white/55");
  svg.setAttribute("stroke", "currentColor");
  svg.setAttribute("stroke-width", "2");
  svg.setAttribute("stroke-linecap", "round");
  svg.setAttribute("stroke-linejoin", "round");
  const poly = document.createElementNS("http://www.w3.org/2000/svg", "polyline");
  poly.setAttribute("points", "4 17 10 11 4 5");
  const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
  line.setAttribute("x1", "12");
  line.setAttribute("y1", "19");
  line.setAttribute("x2", "20");
  line.setAttribute("y2", "19");
  svg.appendChild(poly);
  svg.appendChild(line);
  return svg;
}

function appendRowIcon(row: HTMLElement, r: ResultItem): void {
  if (r.category === "web") {
    row.appendChild(svgIconSearch());
    return;
  }
  if (r.category === "commands") {
    row.appendChild(svgIconCommand());
    return;
  }
  if (r.faviconUrl) {
    const img = document.createElement("img");
    img.className = "h-5 w-5 shrink-0 rounded-sm object-cover";
    img.alt = "";
    img.src = r.faviconUrl;
    img.addEventListener("error", () => {
      img.replaceWith(svgIconSearch());
    });
    row.appendChild(img);
    return;
  }
  row.appendChild(svgIconSearch());
}

function showUrlBesideTitle(category: Category): boolean {
  return category === "tabs" || category === "bookmarks" || category === "history";
}

function ensureHost(): void {
  if (host && shadow) return;
  host = document.createElement("div");
  host.id = "arc-search-root";
  host.style.zIndex = "2147483647";
  shadow = host.attachShadow({ mode: "open" });
  const style = document.createElement("style");
  style.textContent = styles;
  shadow.appendChild(style);

  wrapEl = document.createElement("div");
  wrapEl.className =
    "pointer-events-auto fixed inset-0 z-[2147483646] flex items-center justify-center";
  wrapEl.style.display = "none";

  const backdrop = document.createElement("div");
  backdrop.className = "absolute inset-0 bg-black/40 backdrop-blur-[10px]";
  backdrop.addEventListener("click", () => hidePalette());

  const panel = document.createElement("div");
  panel.className =
    "relative w-[min(640px,92vw)] overflow-hidden rounded-[14px] border border-white/[0.08] bg-[rgba(18,18,22,0.92)] shadow-[0_24px_80px_rgba(0,0,0,0.55),inset_0_0_0_1px_rgba(255,255,255,0.04)]";

  const inputRow = document.createElement("div");
  inputRow.className = "flex items-center gap-3 border-b border-white/[0.08] px-5 py-4";

  const inputSearchIcon = svgIconSearch();
  inputSearchIcon.setAttribute("class", "h-6 w-6 shrink-0 text-white/70");

  inputEl = document.createElement("input");
  inputEl.className =
    "min-w-0 flex-1 border-none bg-transparent text-lg text-white/[0.94] outline-none placeholder:text-white/55";
  inputEl.type = "text";
  inputEl.placeholder = "Search or Enter URL...";
  inputEl.autocomplete = "off";
  inputEl.spellcheck = false;

  inputRow.appendChild(inputSearchIcon);
  inputRow.appendChild(inputEl);

  listEl = document.createElement("div");
  listEl.className = "list-scroll space-y-1 overflow-y-auto p-2";
  listEl.style.maxHeight = "220px";

  panel.appendChild(inputRow);
  panel.appendChild(listEl);

  wrapEl.appendChild(backdrop);
  wrapEl.appendChild(panel);
  shadow.appendChild(wrapEl);
  document.documentElement.appendChild(host);

  inputEl.addEventListener("input", () => scheduleQuery());
  inputEl.addEventListener("keydown", onInputKeydown);

  wrapEl.addEventListener("keydown", trapKeyboard);
  wrapEl.addEventListener("keyup", trapKeyboard);
  wrapEl.addEventListener("keypress", trapKeyboard);
}

function lockScroll(): void {
  document.documentElement.style.overflow = "hidden";
  document.body.style.overflow = "hidden";
}

function unlockScroll(): void {
  document.documentElement.style.overflow = "";
  document.body.style.overflow = "";
}

function showPalette(): void {
  ensureHost();
  visible = true;
  lockScroll();
  wrapEl!.style.display = "flex";
  inputEl!.value = "";
  results = [];
  selected = 0;
  renderResults();
  void queryNow("");
  requestAnimationFrame(() => {
    inputEl?.focus();
    inputEl?.select();
  });
}

function hidePalette(): void {
  visible = false;
  unlockScroll();
  if (wrapEl) wrapEl.style.display = "none";
  if (debounceTimer) {
    clearTimeout(debounceTimer);
    debounceTimer = null;
  }
}

function scheduleQuery(): void {
  if (debounceTimer) clearTimeout(debounceTimer);
  debounceTimer = setTimeout(() => {
    debounceTimer = null;
    void queryNow(inputEl?.value ?? "");
  }, DEBOUNCE_MS);
}

async function queryNow(query: string): Promise<void> {
  const res = (await chrome.runtime.sendMessage({
    type: MSG.QUERY_RESULTS,
    query,
  } satisfies ExtensionMessage)) as ExtensionMessage;
  if (res.type !== MSG.QUERY_RESULTS_RESPONSE) return;
  if (!visible) return;
  results = res.results;
  selected = 0;
  renderResults();
}

function renderResults(): void {
  if (!listEl) return;
  listEl.innerHTML = "";
  if (results.length === 0) {
    const empty = document.createElement("div");
    empty.className = "px-4 py-3.5 text-sm text-white/55";
    empty.textContent = "No matches";
    listEl.appendChild(empty);
    return;
  }
  results.forEach((r, idx) => {
    const row = document.createElement("div");
    row.className = `${ROW_BASE} ${idx === selected ? ROW_SELECTED : ROW_IDLE}`;
    row.setAttribute("role", "option");
    row.setAttribute("aria-selected", idx === selected ? "true" : "false");
    row.addEventListener("click", () => {
      selected = idx;
      void executeSelected();
    });

    appendRowIcon(row, r);

    const label = document.createElement("div");
    label.className = "min-w-0 flex-1 truncate text-[15px]";

    const titleSpan = document.createElement("span");
    titleSpan.className = "font-medium text-white/[0.94]";
    titleSpan.textContent = r.title;

    label.appendChild(titleSpan);

    if (showUrlBesideTitle(r.category) && r.subtitle) {
      const dash = document.createElement("span");
      dash.className = "text-white/40";
      dash.textContent = " — ";
      const urlSpan = document.createElement("span");
      urlSpan.className = "text-white/50";
      urlSpan.textContent = truncateUrl(r.subtitle);
      label.appendChild(dash);
      label.appendChild(urlSpan);
    }

    row.appendChild(label);

    if (r.category === "tabs") {
      const action = document.createElement("span");
      action.className =
        "ml-2 shrink-0 whitespace-nowrap text-xs text-white/45";
      action.textContent = "Switch to Tab →";
      row.appendChild(action);
    }

    listEl!.appendChild(row);
  });

  const row = listEl.children[selected] as HTMLElement | undefined;
  row?.scrollIntoView({ block: "nearest" });
}

function trapKeyboard(ev: Event): void {
  if (visible) ev.stopPropagation();
}

function onInputKeydown(ev: KeyboardEvent): void {
  if (!visible) return;
  if (ev.key === "Escape") {
    ev.preventDefault();
    hidePalette();
    return;
  }
  if (ev.key === "ArrowDown") {
    ev.preventDefault();
    selected = Math.min(results.length - 1, selected + 1);
    renderResults();
    return;
  }
  if (ev.key === "ArrowUp") {
    ev.preventDefault();
    selected = Math.max(0, selected - 1);
    renderResults();
    return;
  }
  if (ev.key === "Enter") {
    ev.preventDefault();
    void executeSelected();
  }
}

async function executeSelected(): Promise<void> {
  const item = results[selected];
  if (!item) return;
  await chrome.runtime.sendMessage({
    type: MSG.EXECUTE_ACTION,
    actionType: item.actionType,
    payload: item.payload,
  } satisfies ExtensionMessage);
  hidePalette();
}

chrome.runtime.onMessage.addListener((message: ExtensionMessage) => {
  if (message.type === MSG.SHOW_PALETTE) {
    showPalette();
  }
});

function onGlobalKeydown(ev: KeyboardEvent): void {
  if (!hotkeyPreset || hotkeyPreset !== "T") return;
  const isMac = navigator.platform.toLowerCase().includes("mac");
  const mod = isMac ? ev.metaKey : ev.ctrlKey;
  if (!mod || ev.key.toLowerCase() !== "t") return;
  if (isEditableTarget(ev.target)) return;
  ev.preventDefault();
  ev.stopPropagation();
  showPalette();
}

window.addEventListener("keydown", onGlobalKeydown, true);
