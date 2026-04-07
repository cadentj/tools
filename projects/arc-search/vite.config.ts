import tailwindcss from "@tailwindcss/vite";
import { defineConfig } from "vite";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { copyFileSync, mkdirSync, existsSync } from "node:fs";

const root = fileURLToPath(new URL(".", import.meta.url));

function copyManifest() {
  const out = resolve(root, "dist");
  if (!existsSync(out)) mkdirSync(out, { recursive: true });
  copyFileSync(resolve(root, "src/manifest.json"), resolve(out, "manifest.json"));
}

/** Static popup shell (no Vite HTML entry): avoids Rollup resolving `#/index.html` when the project path contains `#`. */
function copyPopupHtml() {
  const out = resolve(root, "dist");
  if (!existsSync(out)) mkdirSync(out, { recursive: true });
  copyFileSync(resolve(root, "popup.html"), resolve(out, "popup.html"));
}

export default defineConfig(({ mode }) => {
  if (mode === "background") {
    return {
      build: {
        lib: {
          entry: resolve(root, "src/background/index.ts"),
          name: "background",
          formats: ["es"],
          fileName: () => "background.js",
        },
        outDir: "dist",
        emptyOutDir: true,
        rollupOptions: {
          output: {
            inlineDynamicImports: true,
          },
        },
      },
      plugins: [
        {
          name: "copy-manifest-after-bg",
          closeBundle() {
            copyManifest();
          },
        },
      ],
    };
  }

  if (mode === "content") {
    return {
      plugins: [tailwindcss()],
      build: {
        lib: {
          entry: resolve(root, "src/content/main.ts"),
          name: "content",
          formats: ["iife"],
          fileName: () => "content.js",
        },
        outDir: "dist",
        emptyOutDir: false,
        rollupOptions: {
          output: {
            inlineDynamicImports: true,
          },
        },
      },
    };
  }

  if (mode === "popup") {
    return {
      build: {
        lib: {
          entry: resolve(root, "src/popup/main.ts"),
          name: "popup",
          formats: ["es"],
          fileName: () => "popup.js",
        },
        outDir: "dist",
        emptyOutDir: false,
        rollupOptions: {
          output: {
            inlineDynamicImports: true,
            /** Single CSS bundle for popup; stable name for static popup.html */
            assetFileNames: "assets/popup[extname]",
          },
        },
      },
      plugins: [
        {
          name: "copy-popup-html",
          closeBundle() {
            copyPopupHtml();
          },
        },
      ],
    };
  }

  return {};
});
