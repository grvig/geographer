import { useEffect, useState } from "react";
import {
  loadAreas,
  loadClueOptions,
  loadQueue,
  type ClueOption,
  type QueueItem,
} from "./api";

const NOT_RUNNING =
  "Can't reach the curation server. Start it with `python -m geographer_pipeline curate` in pipeline/.";

// Local-only review page: check the matcher's answers, least sure first.
export default function CuratePage() {
  const [areas, setAreas] = useState<string[]>([]);
  const [area, setArea] = useState("");
  const [clues, setClues] = useState<ClueOption[]>([]);
  const [items, setItems] = useState<QueueItem[] | null>(null);
  const [total, setTotal] = useState(0);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([loadAreas(), loadClueOptions()])
      .then(([found, options]) => {
        setAreas(found.map((entry) => entry.name));
        setArea(found[0]?.name ?? "");
        setClues(options);
      })
      .catch(() => setError(NOT_RUNNING));
  }, []);

  useEffect(() => {
    if (!area) {
      return;
    }
    let cancelled = false;
    loadQueue(area)
      .then((queue) => {
        if (!cancelled) {
          setItems(queue.items);
          setTotal(queue.total);
        }
      })
      .catch((reason: Error) => setError(reason.message));
    return () => {
      cancelled = true;
    };
  }, [area]);

  const titles = new Map(clues.map((clue) => [clue.id, clue.title]));

  return (
    <div className="mx-auto w-full max-w-3xl space-y-4 p-6">
      <h1 className="text-xl font-semibold">Review</h1>
      {error && (
        <p role="alert" className="rounded bg-red-950 p-2 text-red-200">
          {error}
        </p>
      )}
      {areas.length > 0 && (
        <label className="block text-sm">
          Area{" "}
          <select
            value={area}
            onChange={(event) => setArea(event.target.value)}
            className="rounded border border-stone-600 bg-stone-900 px-2 py-1"
          >
            {areas.map((name) => (
              <option key={name}>{name}</option>
            ))}
          </select>
        </label>
      )}
      {items && (
        <p className="text-sm text-stone-400">{total} left to review</p>
      )}
      <ul className="space-y-2">
        {items?.map((item) => (
          <li
            key={`${item.image_id}/${item.detection_id}`}
            className="flex gap-3 rounded border border-stone-800 p-2"
          >
            <img
              src={item.crop}
              alt={`${item.category} ${item.detection_id} in image ${item.image_id}`}
              className="h-28 w-20 shrink-0 rounded bg-stone-950 object-contain"
            />
            <div className="text-sm">
              <p className="font-semibold">
                {titles.get(item.clue ?? "") ?? `Unknown ${item.category}`}
              </p>
              <p className="text-stone-400">
                {Math.round(item.confidence * 100)}% · {item.source} · image{" "}
                {item.image_id}
              </p>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
