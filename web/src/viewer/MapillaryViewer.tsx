import { useEffect, useEffectEvent, useRef, useState } from "react";
import {
  CancelMapillaryError,
  Viewer,
  type Image as MapillaryImage,
  type TagComponent,
} from "mapillary-js";
import "mapillary-js/dist/mapillary.css";
import type { Detection } from "../data/shardSchema";
import { toTags } from "./detectionTags";

export type ViewerImage = {
  id: string;
  // Analysis files are stored per sequence, so this picks the file to load.
  sequenceId: string;
  lat: number;
  lon: number;
  creator: string;
};

type Props = {
  imageId: string;
  // Outlined in the current image, coloured by category id.
  detections?: Detection[];
  categoryColours?: Map<string, string>;
  onImageChange: (image: ViewerImage) => void;
  onBearingChange: (bearing: number) => void;
  // Called when the pointer moves onto or off an outline, with viewer pixels.
  onHover?: (hover: Hover | null) => void;
  // Called on click with the outline under the pointer, or null.
  onSelect?: (detectionId: string | null) => void;
};

export type Hover = { detectionId: string; x: number; y: number };

const NO_DETECTIONS: Detection[] = [];
const NO_COLOURS = new Map<string, string>();

export default function MapillaryViewer(props: Props) {
  const { imageId, onImageChange, onBearingChange } = props;
  const detections = props.detections ?? NO_DETECTIONS;
  const categoryColours = props.categoryColours ?? NO_COLOURS;
  const accessToken = import.meta.env.VITE_MAPILLARY_TOKEN;
  const containerRef = useRef<HTMLDivElement>(null);
  const viewerRef = useRef<Viewer | null>(null);
  // The image the viewer is showing, so walking around does not trigger a reload.
  const shownIdRef = useRef<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleImage = useEffectEvent((image: MapillaryImage) => {
    shownIdRef.current = image.id;
    setError(null);
    onImageChange({
      id: image.id,
      sequenceId: image.sequenceId,
      lat: image.lngLat.lat,
      lon: image.lngLat.lng,
      creator: image.creatorUsername,
    });
  });
  const handleBearing = useEffectEvent(onBearingChange);
  // Only report hover changes, so moving within one outline doesn't re-render.
  const hoveredRef = useRef<string | null>(null);
  const handleHover = useEffectEvent((hover: Hover | null) => {
    const id = hover?.detectionId ?? null;
    if (id === hoveredRef.current) {
      return;
    }
    hoveredRef.current = id;
    const container = containerRef.current;
    if (container && id) {
      container.style.cursor = "pointer";
    } else if (container) {
      container.style.cursor = "";
    }
    props.onHover?.(hover);
  });
  const handleSelect = useEffectEvent((id: string | null) => {
    props.onSelect?.(id);
  });

  useEffect(() => {
    const container = containerRef.current;
    if (!container || !accessToken) {
      return;
    }
    const viewer = new Viewer({
      accessToken,
      container,
      component: { tag: true },
    });
    viewer.on("image", (event) => handleImage(event.image));
    viewer.on("pov", async () => {
      const pov = await viewer.getPointOfView();
      handleBearing(pov.bearing);
    });
    const tagIdAt = async (pixelPoint: number[]) => {
      const tags = viewer.getComponent<TagComponent>("tag");
      const ids = await tags.getTagIdsAt(pixelPoint);
      return ids[0] ?? null;
    };
    viewer.on("mousemove", async (event) => {
      const id = await tagIdAt(event.pixelPoint);
      if (id) {
        const [x = 0, y = 0] = event.pixelPoint;
        handleHover({ detectionId: id, x, y });
      } else {
        handleHover(null);
      }
    });
    viewer.on("mouseout", () => handleHover(null));
    viewer.on("click", async (event) => {
      handleSelect(await tagIdAt(event.pixelPoint));
    });
    viewerRef.current = viewer;
    return () => {
      viewer.remove();
      viewerRef.current = null;
      shownIdRef.current = null;
    };
  }, [accessToken]);

  useEffect(() => {
    const viewer = viewerRef.current;
    if (!viewer || imageId === shownIdRef.current) {
      return;
    }
    viewer.moveTo(imageId).catch((reason: unknown) => {
      if (!(reason instanceof CancelMapillaryError)) {
        setError(`Image ${imageId} could not be loaded from Mapillary.`);
      }
    });
  }, [imageId, accessToken]);

  useEffect(() => {
    const viewer = viewerRef.current;
    if (!viewer) {
      return;
    }
    const tags = viewer.getComponent<TagComponent>("tag");
    tags.removeAll();
    tags.add(toTags(detections, categoryColours));
  }, [detections, categoryColours, accessToken]);

  if (!accessToken) {
    return (
      <p
        role="alert"
        className="m-auto max-w-md p-6 text-center text-stone-300"
      >
        The street-level viewer needs a Mapillary access token. Set
        VITE_MAPILLARY_TOKEN in web/.env.local and restart the dev server.
      </p>
    );
  }
  return (
    <div className="relative h-full w-full">
      <div ref={containerRef} className="h-full w-full" />
      {error && (
        <p role="alert" className="absolute inset-x-0 top-0 bg-red-900/90 p-2">
          {error}
        </p>
      )}
    </div>
  );
}
