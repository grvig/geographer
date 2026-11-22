import { mapillaryImageUrl } from "../lib/links";

type Props = {
  imageId: string;
  creator?: string;
};

// Credit for a Mapillary image or a crop of one (CC-BY-SA 4.0 requires it).
export default function MapillaryCredit({ imageId, creator }: Props) {
  let author = "Mapillary contributor";
  if (creator) {
    author = creator;
  }
  return (
    <p className="text-xs text-stone-400">
      © {author},{" "}
      <a
        className="underline hover:text-stone-200"
        href="https://creativecommons.org/licenses/by-sa/4.0/"
        target="_blank"
        rel="noopener noreferrer"
      >
        CC-BY-SA 4.0
      </a>
      {" · "}
      <a
        className="underline hover:text-stone-200"
        href={mapillaryImageUrl(imageId)}
        target="_blank"
        rel="noopener noreferrer"
      >
        View on Mapillary
      </a>
    </p>
  );
}
