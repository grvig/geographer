import type { Clue } from "../data/clueSchema";
import { dataRoot } from "../data/loadIndex";
import MapillaryCredit from "./MapillaryCredit";

type Props = {
  clue: Clue;
};

// The clue's reference photo, so the object in view can be compared with it.
export default function ClueImages({ clue }: Props) {
  const reference = clue.references[0];
  if (!reference) {
    return <p className="text-stone-500">No reference photo yet.</p>;
  }
  return (
    <figure className="space-y-1">
      <div className="flex h-32 items-center justify-center rounded bg-stone-950">
        <img
          src={`${dataRoot}/refs/${reference.file}`}
          alt={`Reference photo: ${clue.title}`}
          className="max-h-full max-w-full object-contain"
        />
      </div>
      <figcaption>
        <MapillaryCredit
          imageId={reference.mapillary_image_id}
          creator={reference.creator}
        />
      </figcaption>
    </figure>
  );
}
