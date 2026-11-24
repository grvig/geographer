const countryNames = new Intl.DisplayNames(["en"], { type: "region" });

// "Bourgogne, France" or just "France".
export function placeName(region: { country: string; admin1?: string | null }) {
  const country = countryNames.of(region.country) ?? region.country;
  if (region.admin1) {
    return `${region.admin1}, ${country}`;
  }
  return country;
}
