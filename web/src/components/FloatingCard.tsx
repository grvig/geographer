import type { CSSProperties } from "react";
import type { ClueLibrary } from "../data/loadClues";
import type { ShardImage } from "../data/shardSchema";
import ClueCard from "./ClueCard";

export type CardState = {
  detectionId: string;
  style: CSSProperties;
  pinned: boolean;
};

type Props = {
  card: CardState;
  image: ShardImage;
  library: ClueLibrary;
  onClose: () => void;
};

export default function FloatingCard({ card, image, library, onClose }: Props) {
  const detection = image.detections.find(
    (candidate) => candidate.id === card.detectionId,
  );
  if (!detection) {
    return null;
  }
  // A hovering card ignores the pointer so it can't steal the hover from the
  // outline underneath. A pinned card takes clicks, for its links.
  let pointer = "pointer-events-none";
  if (card.pinned) {
    pointer = "pointer-events-auto";
  }
  return (
    <div
      style={card.style}
      className={`absolute z-10 max-h-[70%] w-80 overflow-y-auto rounded border border-stone-700 bg-stone-900/95 p-3 shadow-lg ${pointer}`}
    >
      {card.pinned && (
        <button
          type="button"
          onClick={onClose}
          aria-label="Close card"
          className="float-right px-1 text-stone-400 hover:text-stone-100"
        >
          ✕
        </button>
      )}
      <ClueCard
        detection={detection}
        library={library}
        imagePlace={{ country: image.country, admin1: image.admin1 }}
      />
    </div>
  );
}
