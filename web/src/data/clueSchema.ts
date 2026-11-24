import { z } from "zod";

// Mirrors content/schema/clue.schema.json. clues.json is written by
// `python -m geographer_pipeline.content build`; bump both versions together.
export const CLUES_SCHEMA_VERSION = 1;

export const clueId = z
  .string()
  .regex(/^[a-z]{2}-[a-z0-9]+(-[a-z0-9]+)*$/, "clue id");

const region = z.object({
  country: z.string().regex(/^[A-Z]{2}$/),
  admin1: z.string().min(1).optional(),
  area: z.string().min(1).optional(),
  strength: z.enum(["only", "typical", "also-seen"]),
});

const reference = z.object({
  file: z.string().min(1),
  mapillary_image_id: z.string().regex(/^\d+$/),
  creator: z.string().min(1),
  captured_at: z.string(),
});

const clue = z.object({
  id: clueId,
  category: z.string().min(1),
  title: z.string().min(1),
  visual: z.object({
    description: z.string().min(1),
    features: z.array(z.string().min(1)).min(1),
  }),
  signifies: z.string().min(1),
  regions: z.array(region).min(1),
  lookalikes: z.array(clueId).default([]),
  tell_apart: z.string().min(1).optional(),
  references: z.array(reference).default([]),
  sources: z.array(z.object({ title: z.string(), url: z.url() })).default([]),
  status: z.enum(["draft", "reviewed"]),
});

const category = z.object({
  id: z.string().min(1),
  label: z.string().min(1),
  overlay_colour: z.string().regex(/^#[0-9a-f]{6}$/),
  scene: z.boolean(),
});

export const cluesFileSchema = z.object({
  schema_version: z.literal(CLUES_SCHEMA_VERSION),
  categories: z.array(category),
  clues: z.array(clue),
});

export type Clue = z.infer<typeof clue>;
export type Category = z.infer<typeof category>;
export type Region = z.infer<typeof region>;
export type CluesFile = z.infer<typeof cluesFileSchema>;
