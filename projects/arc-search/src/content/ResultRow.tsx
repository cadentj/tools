import { Search, ArrowRight } from "lucide-react";
import { useState, type ReactElement } from "react";
import { cn } from "../lib/utils";
import type { Category, ResultItem } from "../shared/types";

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

function showUrlBesideTitle(category: Category): boolean {
  return category === "bookmarks" || category === "history";
}

function RowIcon({
  r,
  selected,
}: {
  r: ResultItem;
  selected: boolean;
}): ReactElement {
  const [imgFailed, setImgFailed] = useState(false);

  if (r.category === "web") {
    return <Search className="h-5 w-5 shrink-0 text-white/70" aria-hidden />;
  }
  if (r.faviconUrl && !imgFailed) {
    return (
      <div
        data-favicon-wrap=""
        className={cn(
          "flex shrink-0 items-center justify-center rounded-md p-1",
          selected ? "bg-white" : "bg-transparent",
        )}
      >
        <img
          className="h-4 w-4 rounded-sm object-cover"
          alt=""
          src={r.faviconUrl}
          onError={() => setImgFailed(true)}
        />
      </div>
    );
  }
  return <Search className="h-5 w-5 shrink-0 text-white/70" aria-hidden />;
}

export function ResultRow({
  r,
  idx,
  selected,
  onActivate,
}: {
  r: ResultItem;
  idx: number;
  selected: boolean;
  onActivate: (idx: number) => void;
}): ReactElement {
  return (
    <div
      className={cn(
        "flex min-w-0 cursor-pointer items-center gap-3 rounded-lg px-4 py-3",
        selected ? "bg-blue-500/20" : "bg-transparent hover:bg-white/8",
      )}
      role="option"
      aria-selected={selected}
      onClick={() => onActivate(idx)}
    >
      <RowIcon r={r} selected={selected} />
      <div className="min-w-0 flex-1 truncate text-[15px]">
        <span className="font-medium text-white/95">{r.title}</span>
        {showUrlBesideTitle(r.category) && r.subtitle ? (
          <>
            <span className="text-white/40"> — </span>
            <span className="text-white/50">{truncateUrl(r.subtitle)}</span>
          </>
        ) : null}
      </div>
      {r.category === "tabs" ? (
        <div className="flex items-center gap-2">
          <span className="ml-2 shrink-0 whitespace-nowrap text-xs text-white/45">Switch to Tab</span>
          <div
            className={cn(
              "flex shrink-0 items-center justify-center rounded-md p-1",
              selected ? "bg-white" : "bg-white/10",
            )}
          >
            <ArrowRight
              className={cn("h-4 w-4", selected ? "text-neutral-900" : "text-white/70")}
              aria-hidden
            />
          </div>
        </div>
      ) : null}
    </div>
  );
}
