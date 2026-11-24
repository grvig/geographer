import { z } from "zod";
import { clueId } from "./clueSchema";

// Written by the pipeline to public/data/images/<CC>/<sequence_id>.json.
// Coordinates are normalised to 0–1 from the image's top-left corner.
export const SHARD_SCHEMA_VERSION = 1;

const unit = z.number().min(0).max(1);
const point = z.tuple([unit, unit]);

export const shapeSchema = z.discriminatedUnion("type", [
  z.object({
    type: z.literal("rect"),
    coords: z.tuple([unit, unit, unit, unit]),
  }),
  z.object({ type: z.literal("polygon"), coords: z.array(point).min(3) }),
]);

const detection = z.object({
  id: z.string().min(1),
  category: z.string().min(1),
  source: z.enum(["mapillary", "owl", "manual"]),
  shape: shapeSchema,
  // null when the matcher abstained: the card shows an unknown object.
  clue: clueId.nullable(),
  confidence: unit,
  alternatives: z
    .array(z.object({ clue: clueId, confidence: unit }))
    .default([]),
  // Whether the clue's regions include the image's location. null when abstained.
  consistent: z.boolean().nullable(),
  verified: z.boolean(),
});

const sceneClue = z.object({
  clue: clueId,
  confidence: unit,
  region: shapeSchema.nullable(),
});

const shardImage = z.object({
  id: z.string().regex(/^\d+$/),
  lat: z.number(),
  lon: z.number(),
  country: z.string().regex(/^[A-Z]{2}$/),
  admin1: z.string().nullable(),
  is_pano: z.boolean(),
  detections: z.array(detection),
  scene: z.array(sceneClue).default([]),
});

export const shardSchema = z.object({
  schema_version: z.literal(SHARD_SCHEMA_VERSION),
  sequence: z.string().min(1),
  images: z.array(shardImage),
});

export type Shape = z.infer<typeof shapeSchema>;
export type Detection = z.infer<typeof detection>;
export type ShardImage = z.infer<typeof shardImage>;
export type Shard = z.infer<typeof shardSchema>;
