import { useEffect, useState } from "react";
import { loadClues, type ClueLibrary } from "../data/loadClues";
import { findImage, loadShard } from "../data/loadShard";
import type { ShardImage } from "../data/shardSchema";
import type { ViewerImage } from "./MapillaryViewer";

export type Analysis = {
  imageId: string;
  // null when this image has not been analysed yet.
  image: ShardImage | null;
  library: ClueLibrary | null;
  failed: boolean;
};

async function loadAnalysis(
  country: string,
  viewerImage: ViewerImage,
): Promise<Analysis> {
  const shard = await loadShard(country, viewerImage.sequenceId);
  const image = findImage(shard, viewerImage.id);
  if (!image) {
    return {
      imageId: viewerImage.id,
      image: null,
      library: null,
      failed: false,
    };
  }
  // The clue texts are only needed once there is something to show.
  const library = await loadClues();
  return { imageId: viewerImage.id, image, library, failed: false };
}

// The analysis of the image in view, or null while it is loading.
export function useAnalysis(country: string, viewerImage: ViewerImage | null) {
  const [analysis, setAnalysis] = useState<Analysis | null>(null);

  useEffect(() => {
    if (!viewerImage) {
      return;
    }
    let cancelled = false;
    loadAnalysis(country, viewerImage)
      .then((loaded) => {
        if (!cancelled) {
          setAnalysis(loaded);
        }
      })
      .catch(() => {
        if (!cancelled) {
          const imageId = viewerImage.id;
          setAnalysis({ imageId, image: null, library: null, failed: true });
        }
      });
    return () => {
      cancelled = true;
    };
  }, [country, viewerImage]);

  if (!viewerImage || analysis?.imageId !== viewerImage.id) {
    return null;
  }
  return analysis;
}
