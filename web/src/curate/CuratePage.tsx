import { useEffect, useEffectEvent, useState } from "react";
import {
  loadAreas,
  loadClueOptions,
  loadQueue,
  sendLabel,
  addReference,
  type Action,
  type ClueOption,
  type QueueItem,
} from "./api";
import { categoryName } from "./names";
import ReviewItem from "./ReviewItem";

const SHORTCUTS: Record<string, Action> = {
  a: "accept",
  x: "reject",
  u: "unknown",
};

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

  // Each verdict is saved, then the item leaves the queue.
  async function settle(item: QueueItem, save: () => Promise<unknown>) {
    try {
      await save();
      setError(null);
      setItems((current) => current?.filter((other) => other !== item) ?? null);
      setTotal((count) => count - 1);
    } catch (reason) {
      setError((reason as Error).message);
    }
  }

  function target(item: QueueItem) {
    return { area, image_id: item.image_id, detection_id: item.detection_id };
  }

  const handleKey = useEffectEvent((event: KeyboardEvent) => {
    const action = SHORTCUTS[event.key];
    const first = items?.[0];
    const typing = event.target instanceof HTMLSelectElement;
    if (!action || !first || typing || event.ctrlKey || event.metaKey) {
      return;
    }
    if (action === "accept" && !first.clue) {
      return;
    }
    void settle(first, () => sendLabel(target(first), action));
  });

  useEffect(() => {
    window.addEventListener("keydown", handleKey);
    return () => {
      window.removeEventListener("keydown", handleKey);
    };
  }, []);

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
        {items?.map((item, index) => (
          <ReviewItem
            key={`${item.image_id}/${item.detection_id}`}
            item={item}
            options={clues.filter((clue) => clue.category === item.category)}
            title={
              titles.get(item.clue ?? "") ??
              `Unknown ${categoryName(item.category)}`
            }
            current={index === 0}
            onAct={(action, clue) =>
              settle(item, () => sendLabel(target(item), action, clue))
            }
            onReference={(clue) =>
              settle(item, () => addReference(target(item), clue))
            }
          />
        ))}
      </ul>
    </div>
  );
}
