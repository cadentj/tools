import tailwindcss from "@tailwindcss/vite";
import preact from "@preact/preset-vite";
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
  const define = { "process.env.NODE_ENV": JSON.stringify("production") };

  if (mode === "background") {
    return {
      define,
      build: {
        lib: {
          entry: resolve(root, "src/background/index.ts"),
          name: "background",
          formats: ["es"],
          fileName: () => "background.js",
        },
        outDir: "dist",
        /** false: concurrent `vite build --watch` modes must not delete each other's outputs */
        emptyOutDir: false,
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
      define,
      plugins: [preact(), tailwindcss()],
      build: {
        lib: {
          entry: resolve(root, "src/content/main.tsx"),
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
      define,
      build: {
        lib: {
          entry: resolve(root, "src/popup/main.tsx"),
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
        preact(),
        tailwindcss(),
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
