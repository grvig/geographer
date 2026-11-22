import { googleMapsUrl } from "../lib/links";

type Props = {
  lat: number;
  lon: number;
};

export default function GoogleMapsLink({ lat, lon }: Props) {
  return (
    <a
      href={googleMapsUrl(lat, lon)}
      target="_blank"
      rel="noopener noreferrer"
      className="text-sm underline hover:text-stone-300"
    >
      Open in Google Maps
    </a>
  );
}
