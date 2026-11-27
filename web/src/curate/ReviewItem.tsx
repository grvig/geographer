import { useState } from "react";
import type { Action, ClueOption, QueueItem } from "./api";
import { categoryName } from "./names";

type Props = {
  item: QueueItem;
  // Clues of the item's category, for relabelling.
  options: ClueOption[];
  title: string;
  // The first item in the queue answers to the keyboard shortcuts.
  current: boolean;
  onAct: (action: Action, clue?: string) => void;
  onReference: (clue: string) => void;
};

const BUTTON =
  "rounded border border-stone-600 px-2 py-0.5 hover:border-accent disabled:opacity-40";

export default function ReviewItem(props: Props) {
  const { item, options, title, current, onAct, onReference } = props;
  const [choice, setChoice] = useState(item.clue ?? options[0]?.id ?? "");
  let frame = "border-stone-800";
  if (current) {
    frame = "border-accent";
  }
  return (
    <li className={`flex gap-3 rounded border p-2 ${frame}`}>
      <img
        src={item.crop}
        alt={`${item.category} ${item.detection_id} in image ${item.image_id}`}
        className="h-28 w-20 shrink-0 rounded bg-stone-950 object-contain"
      />
      <div className="space-y-2 text-sm">
        <p className="font-semibold">{title}</p>
        <p className="text-stone-400">
          {Math.round(item.confidence * 100)}% · {item.source} · image{" "}
          {item.image_id}
        </p>
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            className={BUTTON}
            disabled={!item.clue}
            onClick={() => onAct("accept")}
          >
            Right <kbd>A</kbd>
          </button>
          <button
            type="button"
            className={BUTTON}
            onClick={() => onAct("reject")}
          >
            Not a {categoryName(item.category)} <kbd>X</kbd>
          </button>
          <button
            type="button"
            className={BUTTON}
            onClick={() => onAct("unknown")}
          >
            Unknown variant <kbd>U</kbd>
          </button>
        </div>
        {options.length > 0 && (
          <div className="flex flex-wrap items-center gap-2">
            <select
              aria-label="Clue"
              value={choice}
              onChange={(event) => setChoice(event.target.value)}
              className="rounded border border-stone-600 bg-stone-900 px-2 py-0.5"
            >
              {options.map((option) => (
                <option key={option.id} value={option.id}>
                  {option.title}
                </option>
              ))}
            </select>
            <button
              type="button"
              className={BUTTON}
              onClick={() => onAct("relabel", choice)}
            >
              It's this clue
            </button>
            <button
              type="button"
              className={BUTTON}
              onClick={() => onReference(choice)}
            >
              Use as its reference photo
            </button>
          </div>
        )}
      </div>
    </li>
  );
}
