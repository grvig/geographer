import type { Detection } from "../data/shardSchema";
import type { Analysis } from "../viewer/useAnalysis";

type Props = {
  analysis: Analysis | null;
  // The detections left after filtering, in the order to list them.
  detections: Detection[];
  selectedId: string | null;
  onSelect: (detectionId: string) => void;
};

function Message({ children }: { children: string }) {
  return <p className="text-sm text-stone-400">{children}</p>;
}

function Body({ analysis, detections, selectedId, onSelect }: Props) {
  if (!analysis) {
    return <Message>Checking this image…</Message>;
  }
  if (analysis.failed) {
    return <Message>The analysis for this image didn't load.</Message>;
  }
  if (!analysis.image || !analysis.library) {
    return <Message>No analysis for this image yet.</Message>;
  }
  if (analysis.image.detections.length === 0) {
    return <Message>Nothing recognised in this image.</Message>;
  }
  if (detections.length === 0) {
    return <Message>Everything here is hidden by the filters.</Message>;
  }
  const { clues, categories } = analysis.library;
  return (
    <ul className="space-y-1">
      {detections.map((detection) => {
        const category = categories.get(detection.category);
        const label = category?.label ?? detection.category;
        let name = `Unknown ${label.toLowerCase()}`;
        const clue = detection.clue && clues.get(detection.clue);
        if (clue) {
          name = clue.title;
        }
        return (
          <li key={detection.id}>
            <button
              type="button"
              aria-pressed={detection.id === selectedId}
              onClick={() => onSelect(detection.id)}
              className="flex w-full items-center gap-2 rounded px-2 py-1 text-left text-sm hover:bg-stone-800 aria-pressed:bg-stone-800"
            >
              <span
                aria-hidden="true"
                className="size-2.5 shrink-0 rounded-full"
                style={{ background: category?.overlay_colour }}
              />
              <span className="flex-1">{name}</span>
              <span className="text-stone-400">
                {Math.round(detection.confidence * 100)}%
              </span>
            </button>
          </li>
        );
      })}
    </ul>
  );
}

export default function InViewList(props: Props) {
  return (
    <section aria-labelledby="in-view-heading" className="space-y-2">
      <h2 id="in-view-heading" className="text-sm font-semibold">
        In view
      </h2>
      <Body {...props} />
    </section>
  );
}
