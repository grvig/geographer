// Plain links only: no Google API is called, so no key or billing account is involved.
export function googleMapsUrl(lat: number, lon: number): string {
  const query = `${lat.toFixed(6)},${lon.toFixed(6)}`;
  return `https://www.google.com/maps/search/?api=1&query=${query}`;
}

export function mapillaryImageUrl(imageId: string): string {
  return `https://www.mapillary.com/app/?pKey=${encodeURIComponent(imageId)}`;
}
