/**
 * Carousel generation stage.
 *
 * Consumes asset specs produced by the Python pipeline and renders carousel
 * images via an image generation API, then uploads them to the asset host
 * using the collision-safe filenames already assigned upstream.
 *
 * The prompt construction and any brand-specific templating used in production
 * are proprietary and are stubbed here. What remains is the orchestration:
 * how specs are turned into hosted assets, how filenames are honoured, and how
 * failures are isolated so one bad slide does not sink an entire run.
 */

import process from "node:process";

const IMAGE_API_URL = process.env.IMAGE_API_URL || "https://example.com/image";
const HOST_UPLOAD_URL = process.env.HOST_UPLOAD_URL || "https://example.com/upload";

/**
 * Build the generation prompt for a single asset.
 *
 * Production prompt logic omitted. The shipped version applies brand voice,
 * layout rules and templating that are specific to the business. This baseline
 * keeps the interface intact so the stage runs end to end.
 *
 * @param {object} spec
 * @returns {string}
 */
function buildPrompt(spec) {
  // Production prompt construction omitted.
  const caption = (spec.caption || "").slice(0, 120);
  return `Carousel slide for content "${caption}" (placeholder prompt).`;
}

/**
 * Generate one image from a prompt. Returns raw bytes (mocked here).
 * @param {string} prompt
 * @returns {Promise<Buffer>}
 */
async function generateImage(prompt) {
  const res = await fetch(IMAGE_API_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ prompt }),
  });
  if (!res.ok) {
    throw new Error(`image API failed: ${res.status}`);
  }
  return Buffer.from(await res.arrayBuffer());
}

/**
 * Upload bytes to the asset host under a pre-assigned, collision-safe name.
 * @param {Buffer} bytes
 * @param {string} filename
 * @returns {Promise<string>} hosted URL
 */
async function uploadAsset(bytes, filename) {
  const res = await fetch(HOST_UPLOAD_URL, {
    method: "POST",
    headers: { "Content-Type": "application/octet-stream", "X-Filename": filename },
    body: bytes,
  });
  if (!res.ok) {
    throw new Error(`upload failed for ${filename}: ${res.status}`);
  }
  const data = await res.json();
  return data.url;
}

/**
 * Process a batch of asset specs into hosted assets.
 * Failures are isolated per spec so one error does not abort the run.
 * @param {object[]} specs
 * @returns {Promise<object[]>}
 */
export async function generateCarousels(specs) {
  const results = [];
  for (const spec of specs) {
    try {
      const prompt = buildPrompt(spec);
      const bytes = await generateImage(prompt);
      const hostedUrl = await uploadAsset(bytes, spec.filename);
      results.push({ ...spec, hostedUrl, status: "ok" });
    } catch (err) {
      results.push({ ...spec, hostedUrl: null, status: "error", error: String(err) });
    }
  }
  return results;
}

// Allow running as a standalone step: reads specs JSON from stdin.
if (import.meta.url === `file://${process.argv[1]}`) {
  let input = "";
  process.stdin.on("data", (chunk) => (input += chunk));
  process.stdin.on("end", async () => {
    const { assets = [] } = JSON.parse(input || "{}");
    const out = await generateCarousels(assets);
    process.stdout.write(JSON.stringify({ assets: out }, null, 2) + "\n");
  });
}
