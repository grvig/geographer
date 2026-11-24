import type { ClueLibrary } from "../data/loadClues";
import type { Clue, Region } from "../data/clueSchema";
import type { Detection } from "../data/shardSchema";
import { placeName } from "../lib/places";

const STRENGTH_WORDS: Record<Region["strength"], string> = {
  only: "Only in",
  typical: "Typical of",
  "also-seen": "Also seen in",
};

function percent(confidence: number) {
  return `${Math.round(confidence * 100)}%`;
}

type Props = {
  detection: Detection;
  library: ClueLibrary;
  // Where the image was taken, for the look-alike warning.
  imagePlace: { country: string; admin1: string | null };
};

export default function ClueCard({ detection, library, imagePlace }: Props) {
  const category = library.categories.get(detection.category);
  const categoryLabel = category?.label ?? detection.category;
  let clue: Clue | undefined;
  if (detection.clue) {
    clue = library.clues.get(detection.clue);
  }

  if (!clue) {
    return (
      <article className="space-y-1">
        <h2 className="font-semibold">Unknown {categoryLabel.toLowerCase()}</h2>
        <p className="text-sm text-stone-400">
          It doesn't match any clue in the library closely enough to say where
          it points.
        </p>
      </article>
    );
  }

  const lookalikes = clue.lookalikes
    .map((id) => library.clues.get(id))
    .filter((other) => other !== undefined);
  const alternatives = detection.alternatives.filter((alternative) =>
    library.clues.has(alternative.clue),
  );

  return (
    <article className="space-y-2 text-sm">
      <header>
        <p className="text-xs text-stone-400">{categoryLabel}</p>
        <h2 className="text-base font-semibold">{clue.title}</h2>
        <p className="text-stone-300">
          {percent(detection.confidence)} match
          {detection.verified && " · checked by hand"}
          {clue.status === "draft" && " · draft clue"}
        </p>
      </header>
      {detection.consistent === false && (
        <p role="note" className="rounded bg-amber-900/60 p-2">
          Looks like {clue.title.toLowerCase()} (from{" "}
          {placeName(clue.regions[0]!)}), but you're in {placeName(imagePlace)}:
          a look-alike!
        </p>
      )}
      <ul>
        {clue.regions.map((region) => (
          <li key={`${region.country}-${region.admin1}-${region.area}`}>
            {STRENGTH_WORDS[region.strength]}{" "}
            {region.area && `${region.area}, `}
            {placeName(region)}
          </li>
        ))}
      </ul>
      <p>{clue.signifies}</p>
      <p className="text-stone-400">{clue.visual.features.join(" · ")}</p>
      {clue.references.length === 0 && (
        <p className="text-stone-500">No reference photo yet.</p>
      )}
      {alternatives.length > 0 && (
        <p className="text-stone-300">
          Could also be:{" "}
          {alternatives
            .map(
              (alternative) =>
                `${library.clues.get(alternative.clue)!.title} (${percent(alternative.confidence)})`,
            )
            .join(", ")}
        </p>
      )}
      {lookalikes.length > 0 && (
        <div>
          <p className="text-stone-300">
            Look-alikes: {lookalikes.map((other) => other.title).join(", ")}
          </p>
          {clue.tell_apart && (
            <p className="text-stone-400">{clue.tell_apart}</p>
          )}
        </div>
      )}
      {clue.sources.map((source) => (
        <a
          key={source.url}
          href={source.url}
          target="_blank"
          rel="noreferrer"
          className="block text-accent underline"
        >
          Learn more: {source.title}
        </a>
      ))}
    </article>
  );
}
