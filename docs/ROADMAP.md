# Roadmap

Built in vertical slices so something visible works early. Each milestone lists what "done" means.

## M0: Scaffold

- [ ] Gitignore, editorconfig, gitattributes, README stub
- [ ] Licences: MIT for code, CC-BY-SA 4.0 for `content/`
- [ ] Vite + React + TypeScript app runs, with Tailwind and React Router
- [ ] ESLint, Prettier, type-check and Vitest wired into `npm run check`
- [ ] Python package `geographer_pipeline` with a CLI entry point
- [ ] pytest and ruff run green
- [ ] Content skeleton and architecture doc

## M1: Walk around

- [ ] App layout, not-found page
- [ ] Country index schema and loader
- [ ] Country picker, random start point
- [ ] MapillaryJS viewer with a clear missing-token state
- [ ] Minimap (MapLibre + OpenFreeMap) with position and heading
- [ ] Mapillary attribution and "Open in Google Maps" link
- [ ] Explore page with the image id in the URL
- [ ] Pipeline command that builds `index/<CC>.json` from Mapillary coverage tiles
- [ ] Loading and error states, keyboard access

## M2: Fake highlights

- [ ] Clue JSON Schema and matching zod schemas
- [ ] `content validate` and `content build` commands
- [ ] Hand-written sample shard
- [ ] Outlines drawn with the TagComponent, colour-coded by category
- [ ] Hover card: descriptor, meaning, regions, confidence, reference, look-alikes
- [ ] Click to pin a card
- [ ] "In view" sidebar
- [ ] Filters: categories, minimum confidence, verified only
- [ ] Keyboard shortcut H toggles highlights
- [ ] "No analysis for this image yet" state

## M3: Real detections

- [ ] Mapillary client with retries, backoff and rate limiting
- [ ] SQLite cache for images, detections, crops and embeddings
- [ ] Area fetch through coverage tiles, image download
- [ ] Detection decoding (vector tile to normalised polygons), with a visual check
- [ ] OWLv2 detector with per-category thresholds, NMS and minimum size
- [ ] Merging Mapillary and OWLv2 detections
- [ ] Crops from `thumb_2048_url` with 15% padding
- [ ] Shard export for one area, with a schema version

## M4: Real matching

- [ ] CLIP embeddings for crops, references and clue descriptions
- [ ] Visual + text scoring with configurable weight
- [ ] Softmax confidence and abstaining
- [ ] Offline reverse geocoding and the look-alike flag
- [ ] Alternatives shown in the card
- [ ] **MVP:** India plus about 3 more countries; bollards, utility poles and 1–2 more categories

## M5: Curation tool

- [ ] Local FastAPI server and dev-only review route
- [ ] Review queue, lowest confidence first
- [ ] Accept, relabel, reject, unknown variant, use as reference
- [ ] Reference authoring into `content/refs/`
- [ ] Verified flag flowing into shards
- [ ] `ATTRIBUTION.md` generated from reference metadata

## M6: Eval and probe

- [ ] Held-out split and eval script
- [ ] Report: per-category top-1 accuracy, abstention rate, most-confused pairs
- [ ] Threshold, margin, temperature and weight tuning
- [ ] Logistic-regression probe per category once there are enough labels

## M7: Scene clues

- [ ] Whole-image and segment comparison against scene clues
- [ ] "Notice here" panel with the top three
- [ ] Region outlines from Mapillary segments

## M8: Clue library

- [ ] Browse by country, region and category
- [ ] Clue pages with references, regions, look-alikes and sources
- [ ] Look-alike side-by-side comparison
- [ ] Search

## M9: Polish and ship

- [ ] Lazy shard loading and code splitting
- [ ] Empty and error states everywhere
- [ ] Accessibility audit and fixes
- [ ] Performance budget and Lighthouse pass
- [ ] Browser end-to-end smoke tests
- [ ] About and credits page
- [ ] README with GIFs and setup instructions
- [ ] Live on Vercel

## M10: Stretch

- [ ] In-browser analysis with transformers.js (OWLv2 + CLIP, WebGPU) and a fallback
- [ ] Upload your own photo and get the same highlights
