import { useCallback, useEffect, useState } from "react";
import { Link, useParams, useSearchParams } from "react-router";
import GoogleMapsLink from "../components/GoogleMapsLink";
import MapillaryCredit from "../components/MapillaryCredit";
import Minimap from "../components/Minimap";
import {
  DataError,
  loadCountryIndex,
  pickRandomImage,
} from "../data/loadIndex";
import MapillaryViewer, { type ViewerImage } from "../viewer/MapillaryViewer";

export default function ExplorePage() {
  const country = (useParams().country ?? "").toUpperCase();
  const [searchParams, setSearchParams] = useSearchParams();
  const imageId = searchParams.get("image");
  const [failure, setFailure] = useState<"missing" | "offline" | null>(null);
  const [attempt, setAttempt] = useState(0);
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
      .catch((error: unknown) => {
        if (cancelled) {
          return;
        }
        // A missing file can come back as the app's HTML page, which fails to parse.
        if (error instanceof DataError || error instanceof SyntaxError) {
          setFailure("missing");
        } else {
          setFailure("offline");
        }
      });
    return () => {
      cancelled = true;
    };
  }, [country, imageId, setSearchParams, attempt]);

  function retry() {
    setFailure(null);
    setAttempt(attempt + 1);
  }

  // Keep the URL on the current image so the view can be shared or reloaded.
  const handleImageChange = useCallback(
    (next: ViewerImage) => {
      setImage(next);
      setSearchParams({ image: next.id }, { replace: true });
    },
    [setSearchParams],
  );

  if (failure === "missing") {
    return (
      <div role="alert" className="m-auto p-6 text-stone-300">
        <p>There is no imagery to explore for "{country}" yet.</p>
        <Link to="/" className="text-accent underline">
          Choose another country
        </Link>
      </div>
    );
  }
  if (failure === "offline") {
    return (
      <div role="alert" className="m-auto p-6 text-stone-300">
        <p>The starting points didn't load. Check your connection.</p>
        <button
          type="button"
          onClick={retry}
          className="mt-2 rounded border border-stone-600 px-3 py-1 hover:border-accent"
        >
          Try again
        </button>
      </div>
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
