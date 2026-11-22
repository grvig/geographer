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

| Folder      | What it holds                                         |
| ----------- | ----------------------------------------------------- |
| `web/`      | The static site (TypeScript, React, Vite)             |
| `pipeline/` | The offline detection and matching pipeline (Python)  |
| `content/`  | The clue database and reference images                |
| `docs/`     | Roadmap and architecture notes                        |

Setup instructions will follow as each part lands.

## Licences

Code is MIT licensed. Everything under `content/` is CC-BY-SA 4.0.
