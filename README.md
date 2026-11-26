# Geographer

Learn GeoGuessr-style geography by exploring real street-level imagery.

Drop into a location, look around freely, and see the geography clues in the scene highlighted:
bollards, utility poles, road markings, sign backs, street lights, soil, vegetation and more.
Hover a highlight to learn what it is, where it points to, how confident the match is, and which
look-alikes to watch out for.

This is a learning tool, not a game: no scores, no rounds, no timers.

## How it works

- Imagery comes from [Mapillary](https://www.mapillary.com) (CC-BY-SA 4.0).
- An offline Python pipeline finds objects in the images and matches them visually against a
  hand-written clue database.
- A static React site shows the imagery with the precomputed results.

## Repository layout

| Folder      | What it holds                                        |
| ----------- | ---------------------------------------------------- |
| `web/`      | The static site (TypeScript, React, Vite)            |
| `pipeline/` | The offline detection and matching pipeline (Python) |
| `content/`  | The clue database and reference images               |
| `docs/`     | Roadmap and architecture notes                       |

## Setup

Both parts need a Mapillary client token. Register an application with read access at
<https://www.mapillary.com/dashboard/developers> and copy its client token (it starts with `MLY|`).
Client tokens are meant to be used in the browser, but keep them out of git: the env files below are ignored.

### Website

Needs Node 22.14 or newer.

```sh
cd web
npm install
cp .env.example .env.local   # then set VITE_MAPILLARY_TOKEN
npm run dev
```

`npm run check` runs the type check, lint, format check and tests.

### Pipeline

Needs Python 3.11 or newer. Keep the virtual environment outside any synced folder, since the
machine-learning packages are several gigabytes.

Install PyTorch first, picking the CUDA build for your driver from
<https://pytorch.org/get-started/locally/>. Installing it through `requirements.txt` would pull in
the CPU-only build. Detection runs on a 4 GB laptop GPU, and on the CPU too (slowly).

```sh
python -m venv ~/.venvs/geographer
source ~/.venvs/geographer/bin/activate   # Windows: ~/.venvs/geographer/Scripts/activate
pip install torch --index-url https://download.pytorch.org/whl/cu128
pip install -r pipeline/requirements.txt -r pipeline/requirements-dev.txt
echo "MAPILLARY_TOKEN=MLY|..." > pipeline/.env
```

Run commands from `pipeline/`:

```sh
python -m geographer_pipeline index         # start points for every country in areas.yaml
python -m geographer_pipeline index IN FR   # or just some of them
python -m geographer_pipeline detect saulieu   # find objects in an analysis area
python -m geographer_pipeline match saulieu    # match its objects to clues
python -m geographer_pipeline export saulieu   # write its shards for the site
python -m geographer_pipeline debug 123 456    # draw detections into data/debug/
python -m geographer_pipeline reference fr-bollard-white-black-band 123 d1   # crop -> reference photo
python -m geographer_pipeline eval             # test matching on the reference photos
pytest && ruff check . && ruff format --check .
```

Analysis areas are listed under `analysis:` in `pipeline/areas.yaml`. `detect` keeps everything it
downloads and finds in `data/` (ignored by git), so a second run only does what's missing; add
`--redo` to run the detectors again after changing prompts or thresholds. The first
run also downloads the OWLv2 model weights from Hugging Face.

### Deploying

The site deploys to Vercel with `web/` as the project's root directory. `web/vercel.json` serves
`index.html` for every page route, while files under `/data/` return a real 404 when missing.

## Licences

Code is MIT licensed. Everything under `content/` is CC-BY-SA 4.0.
