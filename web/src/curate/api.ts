import { z } from "zod";

// Talks to the local curation server (`python -m geographer_pipeline curate`),
// which the dev server proxies at /api. None of this ships in the built site.

const alternative = z.object({ clue: z.string(), confidence: z.number() });

const queueItem = z.object({
  image_id: z.string(),
  detection_id: z.string(),
  category: z.string(),
  source: z.string(),
  box: z.tuple([z.number(), z.number(), z.number(), z.number()]),
  clue: z.string().nullable(),
  confidence: z.number(),
  alternatives: z.array(alternative),
  crop: z.string(),
});

const queue = z.object({ total: z.number().int(), items: z.array(queueItem) });
const areas = z.array(z.object({ name: z.string(), country: z.string() }));
const clueOptions = z.array(
  z.object({ id: z.string(), category: z.string(), title: z.string() }),
);
const reference = z.object({ file: z.string() });

export type QueueItem = z.infer<typeof queueItem>;
export type ClueOption = z.infer<typeof clueOptions>[number];
export type Action = "accept" | "relabel" | "reject" | "unknown";

async function call<T>(path: string, schema: z.ZodType<T>, body?: object) {
  let init: RequestInit | undefined;
  if (body) {
    init = {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    };
  }
  const response = await fetch(path, init);
  const data: unknown = await response.json().catch(() => null);
  if (!response.ok) {
    // The server explains refusals in FastAPI's usual `detail` field.
    let message = `The curation server answered HTTP ${response.status}`;
    const detail = z.object({ detail: z.string() }).safeParse(data);
    if (detail.success) {
      message = detail.data.detail;
    }
    throw new Error(message);
  }
  return schema.parse(data);
}

export function loadAreas() {
  return call("/api/areas", areas);
}

export function loadQueue(area: string) {
  return call(`/api/queue?area=${encodeURIComponent(area)}`, queue);
}

export function loadClueOptions() {
  return call("/api/clues", clueOptions);
}

type Target = { area: string; image_id: string; detection_id: string };

export function sendLabel(target: Target, action: Action, clue?: string) {
  return call("/api/labels", z.unknown(), { ...target, action, clue });
}

export function useAsReference(target: Target, clue: string) {
  return call("/api/references", reference, { ...target, clue });
}
