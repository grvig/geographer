# Architecture

Geographer has four parts. Heavy work happens offline on a developer machine; the deployed site is
static and only reads precomputed JSON.

| Part        | Language          | Runs                | Job                                                |
| ----------- | ----------------- | ------------------- | -------------------------------------------------- |
| `pipeline/` | Python            | locally, with a GPU | fetch imagery, detect objects, match clues, export |
| `web/`      | TypeScript, React | in the browser      | viewer, outlines, hover cards, clue library        |
| `content/`  | YAML, JPEG        | n/a                 | the clue database and reference crops              |
| curation    | Python + React    | locally only        | review matches, confirm labels, add references     |

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

**How a match is scored.** Each candidate clue gets `weight * visual + (1 - weight) * text`: the best
CLIP similarity between the crop and the clue's reference photos, and the similarity between the crop
and the clue's description. A softmax turns the scores into confidences. "None of these" is always a
candidate: its visual score is a fixed floor (what an unrelated object typically scores against a
reference, about 0.70 on Burgundy crops) and its text score is the best of the category's
`negatives`. A clue without reference photos gets the same floor, so it can only win on its
description, which on small crops is weak. In practice a clue needs reference photos to be named.
All the numbers live in `pipeline/matching.yaml`; `eval` reports how a change does.

**Two detectors.** Mapillary's own detections cover classes such as utility poles and street lights.
OWLv2, an open-vocabulary detector, covers objects Mapillary has no class for, such as bollards.
Overlapping boxes (IoU above 0.5) are merged, keeping the Mapillary polygon.

**Decoy prompts.** OWLv2 labels each box with the prompt it matches best. Generic prompts such as
"a roadside bollard" mostly found sign posts, so the detector also asks for "a traffic sign on a
pole" and "a street name sign" and drops the boxes those win. Prompts and thresholds in
`content/categories.yaml` are checked against real imagery with `detect --redo` and `debug`.

**Runs of images, not a scatter.** An analysis area takes runs of up to 40 consecutive images
from a few sequences, so walking along a road in the viewer keeps finding analysed images. Analysed
images with something found in them become the site's start points. Panoramas are skipped for now:
crops from them are distorted.

**Hand-checked data wins.** Exporting an area rewrites its shards, except for images that have a
detection labelled or verified by hand; those entries are kept as they are.

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
