import type { Detection } from "../data/shardSchema";

export type Filters = {
  hiddenCategories: string[];
  // 0–1, compared with each detection's confidence.
  minConfidence: number;
  verifiedOnly: boolean;
};

export const DEFAULT_FILTERS: Filters = {
  hiddenCategories: [],
  minConfidence: 0,
  verifiedOnly: false,
};

export function filterDetections(detections: Detection[], filters: Filters) {
  return detections.filter((detection) => {
    if (filters.hiddenCategories.includes(detection.category)) {
      return false;
    }
    if (detection.confidence < filters.minConfidence) {
      return false;
    }
    return detection.verified || !filters.verifiedOnly;
  });
}
