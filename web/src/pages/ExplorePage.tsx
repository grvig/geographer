import { useCallback, useEffect, useState } from "react";
import { useParams, useSearchParams } from "react-router";
import GoogleMapsLink from "../components/GoogleMapsLink";
import MapillaryCredit from "../components/MapillaryCredit";
import Minimap from "../components/Minimap";
import { loadCountryIndex, pickRandomImage } from "../data/loadIndex";
import MapillaryViewer, { type ViewerImage } from "../viewer/MapillaryViewer";

export default function ExplorePage() {
  const country = (useParams().country ?? "").toUpperCase();
  const [searchParams, setSearchParams] = useSearchParams();
  const imageId = searchParams.get("image");
  const [error, setError] = useState<string | null>(null);
  const [image, setImage] = useState<ViewerImage | null>(null);
  const [bearing, setBearing] = useState(0);

  // Without an image in the URL, start at a random processed image of the country.
  useEffect(() => {
    if (imageId) {
      return;
    }
    let cancelled = false;
    loadCountryIndex(country)
      .then((index) => {
        if (!cancelled) {
          setSearchParams({ image: pickRandomImage(index) }, { replace: true });
        }
      })
      .catch(() => {
        if (!cancelled) {
          setError(`There is no explorable imagery for "${country}" yet.`);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [country, imageId, setSearchParams]);

  // Keep the URL on the current image so the view can be shared or reloaded.
  const handleImageChange = useCallback(
    (next: ViewerImage) => {
      setImage(next);
      setSearchParams({ image: next.id }, { replace: true });
    },
    [setSearchParams],
  );

  if (error) {
    return (
      <p role="alert" className="m-auto p-6 text-stone-300">
        {error}
      </p>
    );
  }
  if (!imageId) {
    return (
      <p role="status" className="m-auto p-6 text-stone-400">
        Picking a starting point…
      </p>
    );
  }
  return (
    <div className="flex min-h-0 flex-1">
      <div className="min-w-0 flex-1">
        <MapillaryViewer
          imageId={imageId}
          onImageChange={handleImageChange}
          onBearingChange={setBearing}
        />
      </div>
      {image && (
        <aside className="flex w-72 flex-col gap-3 border-l border-stone-800 p-3">
          <div className="h-56 overflow-hidden rounded">
            <Minimap lat={image.lat} lon={image.lon} bearing={bearing} />
          </div>
          <GoogleMapsLink lat={image.lat} lon={image.lon} />
          <MapillaryCredit imageId={image.id} creator={image.creator} />
        </aside>
      )}
    </div>
  );
}
