import {
  cluesFileSchema,
  type Category,
  type Clue,
  type CluesFile,
} from "./clueSchema";
import { dataRoot, fetchJson } from "./loadIndex";

export type ClueLibrary = {
  clues: Map<string, Clue>;
  categories: Map<string, Category>;
};

let cached: Promise<ClueLibrary> | null = null;

function toLibrary(file: CluesFile): ClueLibrary {
  const clues = new Map<string, Clue>();
  for (const clue of file.clues) {
    clues.set(clue.id, clue);
  }
  const categories = new Map<string, Category>();
  for (const category of file.categories) {
    categories.set(category.id, category);
  }
  return { clues, categories };
}

// clues.json is shared by every image, so it is fetched once per session.
export function loadClues(): Promise<ClueLibrary> {
  if (!cached) {
    const loading = fetchJson(`${dataRoot}/clues.json`, cluesFileSchema).then(
      toLibrary,
    );
    // A failed load is forgotten, so the next call tries again.
    loading.catch(() => {
      cached = null;
    });
    cached = loading;
  }
  return cached;
}

export function clearClueCache() {
  cached = null;
}
