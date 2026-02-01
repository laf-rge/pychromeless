import tailwindPlugin from "bun-plugin-tailwind";
import { join } from "path";
import { readdirSync, existsSync, mkdirSync, statSync } from "fs";

const isDev = process.argv.includes("--dev");

const result = await Bun.build({
  entrypoints: ["./src/main.tsx"],
  outdir: "./dist",
  target: "browser",
  format: "esm",
  splitting: true,
  sourcemap: isDev ? "inline" : "external",
  minify: !isDev,
  publicPath: "/assets/",
  naming: {
    entry: "assets/[name]-[hash].[ext]",
    chunk: "assets/[name]-[hash].[ext]",
    asset: "assets/[name]-[hash].[ext]",
  },
  define: {
    "import.meta.env.DEV": JSON.stringify(isDev),
    "import.meta.env.PROD": JSON.stringify(!isDev),
    "import.meta.env.MODE": JSON.stringify(isDev ? "development" : "production"),
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
  process.exit(1);
}

// Copy public/ files to dist/ (static assets not processed by bundler)
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
  console.log("  Copied public/ assets to dist/");
}

// Copy index.html to dist with updated script references
const indexHtml = await Bun.file("./index.html").text();

// Find the built JS entry file
const jsEntry = result.outputs.find((o) => o.path.endsWith(".js") && o.kind === "entry-point");
const cssEntry = result.outputs.find((o) => o.path.endsWith(".css"));

if (!jsEntry) {
  console.error("No JS entry point found in build outputs");
  process.exit(1);
}

// Get relative paths from dist directory
const jsPath = jsEntry.path.replace(process.cwd() + "/dist", "");
const cssPath = cssEntry ? cssEntry.path.replace(process.cwd() + "/dist", "") : null;

// Update index.html with correct asset paths
let updatedHtml = indexHtml
  .replace(
    '<script type="module" src="/src/main.tsx"></script>',
    `<script type="module" src="${jsPath}"></script>`
  );

// Add CSS link if we have one
if (cssPath) {
  updatedHtml = updatedHtml.replace(
    "</head>",
    `  <link rel="stylesheet" href="${cssPath}">\n  </head>`
  );
}

await Bun.write("./dist/index.html", updatedHtml);

console.log(isDev ? "Development build complete" : "Production build complete");
console.log(`  JS: ${jsPath}`);
if (cssPath) {
  console.log(`  CSS: ${cssPath}`);
}
