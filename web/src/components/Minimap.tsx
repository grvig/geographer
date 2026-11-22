import { useEffect, useRef } from "react";
import { Map as MapLibreMap, Marker } from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";

// Free OpenFreeMap style: no key, attribution is added by MapLibre from the style.
const STYLE_URL = "https://tiles.openfreemap.org/styles/liberty";

const HEADING_ICON = `
<svg width="28" height="28" viewBox="0 0 28 28" aria-hidden="true">
  <path d="M14 2 L22 22 L14 17 L6 22 Z" fill="#f59e0b" stroke="#1c1917" stroke-width="1.5"/>
</svg>`;

type Props = {
  lat: number;
  lon: number;
  // Compass heading in degrees, 0 = north
  bearing: number;
};

export default function Minimap({ lat, lon, bearing }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<MapLibreMap | null>(null);
  const markerRef = useRef<Marker | null>(null);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) {
      return;
    }
    const map = new MapLibreMap({ container, style: STYLE_URL, zoom: 15 });
    const element = document.createElement("div");
    element.innerHTML = HEADING_ICON;
    const marker = new Marker({ element, rotationAlignment: "map" });
    marker.setLngLat([0, 0]);
    marker.addTo(map);
    mapRef.current = map;
    markerRef.current = marker;
    return () => {
      map.remove();
      mapRef.current = null;
      markerRef.current = null;
    };
  }, []);

  useEffect(() => {
    const map = mapRef.current;
    const marker = markerRef.current;
    if (!map || !marker) {
      return;
    }
    map.jumpTo({ center: [lon, lat] });
    marker.setLngLat([lon, lat]);
    marker.setRotation(bearing);
  }, [lat, lon, bearing]);

  return (
    <div
      ref={containerRef}
      role="region"
      aria-label="Minimap"
      className="h-full w-full"
    />
  );
}
