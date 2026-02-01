import tailwindPlugin from "bun-plugin-tailwind";
import { watch, readdirSync, existsSync, mkdirSync, statSync } from "fs";
import { join } from "path";

const PORT = 3000;

// Build the application
async function build() {
  const result = await Bun.build({
    entrypoints: ["./src/main.tsx"],
    outdir: "./dist",
    target: "browser",
    format: "esm",
    splitting: true,
    sourcemap: "inline",
    minify: false,
    naming: {
      entry: "assets/[name]-[hash].[ext]",
      chunk: "assets/[name]-[hash].[ext]",
      asset: "assets/[name]-[hash].[ext]",
    },
    define: {
      "import.meta.env.DEV": "true",
      "import.meta.env.PROD": "false",
      "import.meta.env.MODE": '"development"',
      "import.meta.env.BUN_E2E_MODE": JSON.stringify(process.env.BUN_E2E_MODE || "false"),
    },
    plugins: [tailwindPlugin],
    loader: {
      ".svg": "file",
      ".png": "file",
      ".jpg": "file",
      ".gif": "file",
      ".woff": "file",
      ".woff2": "file",
    },
  });

  if (!result.success) {
    console.error("Build failed:");
    for (const log of result.logs) {
      console.error(log);
    }
    return false;
  }

  // Copy public/ files to dist/
  const publicDir = join(process.cwd(), "public");
  if (existsSync(publicDir)) {
    const distDir = join(process.cwd(), "dist");
    async function copyDir(src: string, dest: string) {
      if (!existsSync(dest)) mkdirSync(dest, { recursive: true });
      for (const entry of readdirSync(src)) {
        const srcPath = join(src, entry);
        const destPath = join(dest, entry);
        if (statSync(srcPath).isDirectory()) {
          await copyDir(srcPath, destPath);
        } else {
          await Bun.write(destPath, Bun.file(srcPath));
        }
      }
    }
    await copyDir(publicDir, distDir);
  }

  // Update index.html with correct asset paths
  const indexHtml = await Bun.file("./index.html").text();
  const jsEntry = result.outputs.find((o) => o.path.endsWith(".js") && o.kind === "entry-point");
  const cssEntry = result.outputs.find((o) => o.path.endsWith(".css"));

  if (!jsEntry) {
    console.error("No JS entry point found");
    return false;
  }

  const jsPath = jsEntry.path.replace(process.cwd() + "/dist", "");
  const cssPath = cssEntry ? cssEntry.path.replace(process.cwd() + "/dist", "") : null;

  let updatedHtml = indexHtml.replace(
    '<script type="module" src="/src/main.tsx"></script>',
    `<script type="module" src="${jsPath}"></script>`
  );

  if (cssPath) {
    updatedHtml = updatedHtml.replace(
      "</head>",
      `  <link rel="stylesheet" href="${cssPath}">\n  </head>`
    );
  }

  await Bun.write("./dist/index.html", updatedHtml);
  return true;
}

// Initial build
console.log("Building...");
const buildSuccess = await build();
if (!buildSuccess) {
  process.exit(1);
}

// Start the server
const server = Bun.serve({
  port: PORT,
  async fetch(req) {
    const url = new URL(req.url);
    let path = url.pathname;

    // API proxy could be added here if needed

    // Serve static files from dist
    if (path === "/" || !path.includes(".")) {
      path = "/index.html";
    }

    const filePath = join(process.cwd(), "dist", path);
    const file = Bun.file(filePath);

    if (await file.exists()) {
      // Set appropriate content type
      const ext = path.split(".").pop();
      const contentTypes: Record<string, string> = {
        html: "text/html",
        js: "application/javascript",
        css: "text/css",
        json: "application/json",
        png: "image/png",
        jpg: "image/jpeg",
        jpeg: "image/jpeg",
        gif: "image/gif",
        svg: "image/svg+xml",
        ico: "image/x-icon",
        woff: "font/woff",
        woff2: "font/woff2",
      };

      return new Response(file, {
        headers: {
          "Content-Type": contentTypes[ext || ""] || "application/octet-stream",
        },
      });
    }

    // SPA fallback - serve index.html for client-side routing
    return new Response(Bun.file(join(process.cwd(), "dist", "index.html")), {
      headers: { "Content-Type": "text/html" },
    });
  },
});

console.log(`Dev server running at http://localhost:${server.port}`);

// Watch for file changes and rebuild
let buildTimeout: ReturnType<typeof setTimeout> | null = null;

const watcher = watch("./src", { recursive: true }, async (event, filename) => {
  if (buildTimeout) {
    clearTimeout(buildTimeout);
  }

  buildTimeout = setTimeout(async () => {
    console.log(`\nFile changed: ${filename}`);
    console.log("Rebuilding...");
    const success = await build();
    if (success) {
      console.log("Rebuild complete. Refresh your browser.");
    }
  }, 100);
});

// Cleanup on exit
process.on("SIGINT", () => {
  watcher.close();
  process.exit(0);
});
