import type { Clue } from "../data/clueSchema";
import { dataRoot } from "../data/loadIndex";
import type { Shape } from "../data/shardSchema";
import { cropStyle, type Photo } from "../lib/sceneCrop";
import MapillaryCredit from "./MapillaryCredit";

type Props = {
  clue: Clue;
  // Where the object is in the current photo, and the photo itself if loaded.
  shape: Shape;
  photo: Photo | null;
};

const FRAME = "flex h-32 items-center justify-center rounded bg-stone-950";

// The object in view next to the clue's reference photo, for comparing them.
export default function ClueImages({ clue, shape, photo }: Props) {
  const reference = clue.references[0];
  return (
    <div className="grid grid-cols-2 gap-2">
      {photo && (
        <figure className="space-y-1">
          <div className={FRAME}>
            <div
              role="img"
              aria-label="This object, cut from the current image"
              className="h-full max-w-full bg-no-repeat"
              style={cropStyle(photo, shape)}
            />
          </div>
          <figcaption className="text-xs text-stone-400">Here</figcaption>
        </figure>
      )}
      {reference && (
        <figure className="space-y-1">
          <div className={FRAME}>
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
      )}
      {!reference && (
        <p className="self-center text-stone-500">No reference photo yet.</p>
      )}
    </div>
  );
}
