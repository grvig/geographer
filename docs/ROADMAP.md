# Roadmap

Built in vertical slices so something visible works early. Each milestone lists what "done" means.

## M0: Scaffold

- [x] Gitignore, editorconfig, gitattributes, README stub
- [x] Licences: MIT for code, CC-BY-SA 4.0 for `content/`
- [x] Vite + React + TypeScript app runs, with Tailwind and React Router
- [x] ESLint, Prettier, type-check and Vitest wired into `npm run check`
- [x] Python package `geographer_pipeline` with a CLI entry point
- [x] pytest and ruff run green
- [x] Content skeleton and architecture doc

## M1: Walk around

- [x] App layout, not-found page
- [x] Country index schema and loader
- [x] Country picker
- [x] Random start point, and a new random spot on demand (N)
- [x] MapillaryJS viewer with a clear missing-token state
- [x] Minimap (MapLibre + OpenFreeMap) with position and heading
- [x] Mapillary attribution and "Open in Google Maps" link
- [x] Explore page with the image id in the URL
- [x] Pipeline command that builds `index/<CC>.json` from Mapillary coverage tiles
- [x] Loading and error states, keyboard access
- [x] Start points for India, the US, Brazil, Russia and France

## M2: Fake highlights

- [x] Clue and category JSON Schemas
- [x] Matching zod schemas in the site
- [x] `content validate` and `content build` commands, with admin1 spelling checks
- [x] First draft clues (Indian milestones, French bollard)
- [x] Hand-written sample shard
- [x] Outlines drawn with the TagComponent, colour-coded by category
- [x] Hover card: descriptor, meaning, regions, confidence, look-alikes, location warning
- [ ] Reference photo next to the scene crop in the card (needs references from M5)
- [x] Click to pin a card
- [x] "In view" sidebar
- [x] Filters: categories, minimum confidence, verified only
- [x] Keyboard shortcut H toggles highlights
- [x] "No analysis for this image yet" state

## M3: Real detections

- [x] Mapillary client with retries, backoff and rate limiting
- [x] SQLite cache for images and detections (embeddings join it in M4)
- [x] Area fetch through coverage tiles, image download
- [x] Detection decoding (vector tile to normalised polygons), with a visual check
- [x] OWLv2 detector with per-category thresholds, NMS and minimum size
- [x] Merging Mapillary and OWLv2 detections
- [x] Crops from `thumb_2048_url` with 15% padding
- [x] Shard export for one area, with a schema version
- [x] Analysed images used as start points on the site

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
