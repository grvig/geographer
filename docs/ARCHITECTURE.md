# Architecture

Geographer has four parts. Heavy work happens offline on a developer machine; the deployed site is
static and only reads precomputed JSON.

| Part        | Language          | Runs                  | Job                                               |
| ----------- | ----------------- | --------------------- | ------------------------------------------------- |
| `pipeline/` | Python            | locally, with a GPU   | fetch imagery, detect objects, match clues, export |
| `web/`      | TypeScript, React | in the browser        | viewer, outlines, hover cards, clue library       |
| `content/`  | YAML, JPEG        | n/a                   | the clue database and reference crops             |
| curation    | Python + React    | locally only          | review matches, confirm labels, add references    |

## Data flow

```
content/clues/**.yaml ──validate, build──▶ web/public/data/clues.json

Mapillary coverage tiles ──▶ image ids per area
Mapillary Graph API ──▶ image metadata, thumbnails, Mapillary detections
        │
        ▼
data/cache.sqlite ──▶ detect ──▶ crop ──▶ embed (CLIP) ──▶ match ──▶ export
                                                                  │
                     web/public/data/images/<CC>/<sequence>.json ◀┘
                     web/public/data/index/<CC>.json

curation ──▶ content/labels/*.jsonl, content/refs/ ──▶ pipeline rerun
```

Each pipeline stage reads from and writes to the SQLite cache, so stages can be rerun on their own
and an interrupted run resumes where it stopped.

## Key decisions

**Matching is visual.** A detected object is compared with every clue in its category, from every
country. Location is never used to pick or filter candidates. Afterwards, the image's reverse-geocoded
country and region are compared with the winning clue's regions, which sets `consistent` and drives
the look-alike warning.

**Abstain rather than guess.** When the top confidence is low, or the top two are close, the object
is shown as unknown in its category.

**Two detectors.** Mapillary's own detections cover classes such as utility poles and street lights.
OWLv2, an open-vocabulary detector, covers objects Mapillary has no class for, such as bollards.
Overlapping boxes (IoU above 0.5) are merged, keeping the Mapillary polygon.

**Coverage through vector tiles.** The Graph API's bounding-box image search only accepts areas
smaller than 0.01°, so the pipeline lists images in an area through Mapillary's coverage tiles at
zoom 14 and then fetches metadata per image.

**Fits a 4 GB GPU.** Models run in fp16 with small batches, one model loaded at a time.

**Static hosting.** The site is deployed to Vercel from Git. Data files are generated locally and
committed separately from code.

## Conventions

- Shape coordinates are normalised to 0–1 with the origin at the top-left of the image. MapillaryJS
  calls these basic coordinates. Rectangles are `[x0, y0, x1, y1]`; polygons are lists of `[x, y]`.
- Country codes are ISO 3166-1 alpha-2, upper case.
- Clue ids are kebab-case and start with a lower-case country code, for example `in-bollard-...`.

## Attribution

Mapillary imagery is CC-BY-SA 4.0. Wherever an image or crop appears, the site shows the creator,
the licence, the Mapillary logo and a link back to the image on Mapillary.
