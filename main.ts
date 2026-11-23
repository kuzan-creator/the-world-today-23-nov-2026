// The World Today — Monday 23 November 2026: 44 stories.
// Entrypoint: copy the pre-generated entry.png to the output dir.
// No dependencies, no network, deterministic: the output bytes are
// exactly the bytes of the image the repository holds.
//
// Usage:  node main.ts
// Writes: <MAKEFUN_OUTPUT_DIR | OUTPUT_DIR | /output>/entry.png
import { copyFileSync, existsSync, mkdirSync, readFileSync } from "node:fs";
import { createHash } from "node:crypto";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const src = join(here, "entry.png");
if (!existsSync(src)) {
  console.error(`missing ${src}`);
  process.exit(1);
}
const outDir =
  process.env.MAKEFUN_OUTPUT_DIR || process.env.OUTPUT_DIR || "/output";
mkdirSync(outDir, { recursive: true });
const dst = join(outDir, "entry.png");
copyFileSync(src, dst);
const bytes = readFileSync(dst);
const srcBytes = readFileSync(src);
if (!bytes.equals(srcBytes)) {
  console.error("copy mismatch: output differs from entry.png");
  process.exit(1);
}
const sha = createHash("sha256").update(bytes).digest("hex");
console.log(`wrote ${dst}  1024x1024  ${bytes.length} bytes  sha256=${sha}`);
console.log("stories: 44");
