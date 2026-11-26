import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Link, useParams, useSearchParams } from "react-router";
import FilterPanel from "../components/FilterPanel";
import FloatingCard, { type CardState } from "../components/FloatingCard";
import GoogleMapsLink from "../components/GoogleMapsLink";
import InViewList from "../components/InViewList";
import MapillaryCredit from "../components/MapillaryCredit";
import Minimap from "../components/Minimap";
import {
  DataError,
  loadCountryIndex,
  pickRandomImage,
} from "../data/loadIndex";
import type { Detection } from "../data/shardSchema";
import { placeCard } from "../lib/cardPlacement";
import {
  DEFAULT_FILTERS,
  filterDetections,
  type Filters,
} from "../lib/filterDetections";
import MapillaryViewer, {
  type Hover,
  type ViewerImage,
} from "../viewer/MapillaryViewer";
import { useAnalysis } from "../viewer/useAnalysis";

const NO_DETECTIONS: Detection[] = [];

export default function ExplorePage() {
  const country = (useParams().country ?? "").toUpperCase();
  const [searchParams, setSearchParams] = useSearchParams();
  const imageId = searchParams.get("image");
  const [failure, setFailure] = useState<"missing" | "offline" | null>(null);
  const [attempt, setAttempt] = useState(0);
  const [image, setImage] = useState<ViewerImage | null>(null);
  const [bearing, setBearing] = useState(0);
  const analysis = useAnalysis(country, image);
  const [filters, setFilters] = useState<Filters>(DEFAULT_FILTERS);
  const [highlightsOn, setHighlightsOn] = useState(true);
  const allDetections = analysis?.image?.detections ?? NO_DETECTIONS;
  const detections = useMemo(
    () => filterDetections(allDetections, filters),
    [allDetections, filters],
  );
  let outlined = NO_DETECTIONS;
  if (highlightsOn) {
    outlined = detections;
  }
  // Only the categories this image has are worth offering as filters.
  const categoriesHere = useMemo(() => {
    const ids = new Set(allDetections.map((detection) => detection.category));
    const known = analysis?.library?.categories;
    return [...ids].flatMap((id) => known?.get(id) ?? []);
  }, [allDetections, analysis]);
  const categoryColours = useMemo(() => {
    const colours = new Map<string, string>();
    for (const category of analysis?.library?.categories.values() ?? []) {
      colours.set(category.id, category.overlay_colour);
    }
    return colours;
  }, [analysis]);
  const [card, setCard] = useState<CardState | null>(null);
  const viewerBoxRef = useRef<HTMLDivElement>(null);

  const cardAt = useCallback((hit: Hover, pinned: boolean): CardState => {
    const box = viewerBoxRef.current;
    const width = box?.clientWidth ?? 0;
    const height = box?.clientHeight ?? 0;
    const style = placeCard(hit.x, hit.y, width, height);
    return { detectionId: hit.detectionId, style, pinned };
  }, []);

  const handleHover = useCallback(
    (hit: Hover | null) => {
      setCard((current) => {
        if (current?.pinned) {
          return current;
        }
        if (!hit) {
          return null;
        }
        return cardAt(hit, false);
      });
    },
    [cardAt],
  );

  // Clicking an outline pins its card; clicking anywhere else lets it go.
  const handleSelect = useCallback(
    (hit: Hover | null) => {
      if (!hit) {
        setCard(null);
        return;
      }
      setCard(cardAt(hit, true));
    },
    [cardAt],
  );

  // Picking from the list has no pointer position, so the card opens in a corner.
  const handleListSelect = useCallback((detectionId: string) => {
    setCard({ detectionId, style: { left: 16, top: 16 }, pinned: true });
  }, []);

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

  // Dropping the image from the URL makes the effect above pick a new one.
  // It is a history push, so Back returns to the previous spot.
  const jumpToRandomSpot = useCallback(() => {
    setSearchParams({});
  }, [setSearchParams]);

  useEffect(() => {
    function handleKey(event: KeyboardEvent) {
      const typing = event.target instanceof HTMLInputElement;
      const modified = event.ctrlKey || event.metaKey || event.altKey;
      if (event.key === "n" && !typing && !modified) {
        jumpToRandomSpot();
      }
      if (event.key === "h" && !typing && !modified) {
        setHighlightsOn((on) => !on);
      }
      if (event.key === "Escape") {
        setCard(null);
      }
    }
    window.addEventListener("keydown", handleKey);
    return () => {
      window.removeEventListener("keydown", handleKey);
    };
  }, [jumpToRandomSpot]);

  // Keep the URL on the current image so the view can be shared or reloaded.
  const handleImageChange = useCallback(
    (next: ViewerImage) => {
      setImage(next);
      setCard(null);
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
      <div ref={viewerBoxRef} className="relative min-w-0 flex-1">
        <MapillaryViewer
          imageId={imageId}
          detections={outlined}
          categoryColours={categoryColours}
          onImageChange={handleImageChange}
          onBearingChange={setBearing}
          onHover={handleHover}
          onSelect={handleSelect}
        />
        {card && analysis?.image && analysis.library && (
          <FloatingCard
            card={card}
            image={analysis.image}
            photo={image?.photo ?? null}
            library={analysis.library}
            onClose={() => setCard(null)}
          />
        )}
      </div>
      {image && (
        <aside className="flex w-72 flex-col gap-3 overflow-y-auto border-l border-stone-800 p-3">
          <div className="h-56 overflow-hidden rounded">
            <Minimap lat={image.lat} lon={image.lon} bearing={bearing} />
          </div>
          <InViewList
            analysis={analysis}
            detections={detections}
            selectedId={card?.detectionId ?? null}
            onSelect={handleListSelect}
          />
          {categoriesHere.length > 0 && (
            <>
              <button
                type="button"
                aria-pressed={!highlightsOn}
                onClick={() => setHighlightsOn(!highlightsOn)}
                className="rounded border border-stone-600 px-3 py-1.5 text-left hover:border-accent"
              >
                Hide highlights <kbd className="text-stone-400">H</kbd>
              </button>
              <FilterPanel
                categories={categoriesHere}
                filters={filters}
                onChange={setFilters}
              />
            </>
          )}
          <button
            type="button"
            onClick={jumpToRandomSpot}
            className="rounded border border-stone-600 px-3 py-1.5 text-left hover:border-accent"
          >
            New random spot <kbd className="text-stone-400">N</kbd>
          </button>
          <GoogleMapsLink lat={image.lat} lon={image.lon} />
          <MapillaryCredit imageId={image.id} creator={image.creator} />
        </aside>
      )}
    </div>
  );
}
