// Run the standalone production server locally, as the Docker image does.
// `next start` is not supported with `output: "standalone"`. Run after
// `npm run build`; honours PORT (default 3000).
import { cpSync, existsSync } from "node:fs";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const standalone = path.join(root, ".next", "standalone");

if (!existsSync(path.join(standalone, "server.js"))) {
  console.error("No standalone build found. Run `npm run build` first.");
  process.exit(1);
}

// server.js serves public/ and .next/static only from inside standalone/.
cpSync(path.join(root, "public"), path.join(standalone, "public"), {
  recursive: true,
});
cpSync(
  path.join(root, ".next", "static"),
  path.join(standalone, ".next", "static"),
  { recursive: true },
);

process.chdir(standalone);
await import(pathToFileURL(path.join(standalone, "server.js")).href);
