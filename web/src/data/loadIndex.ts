import { z } from "zod";
import {
  countryIndexSchema,
  countryListSchema,
  type CountryIndex,
  type CountryList,
} from "./indexSchema";

export class DataError extends Error {
  name = "DataError";
}

const dataRoot = `${import.meta.env.BASE_URL}data`;

export async function fetchJson<T>(
  url: string,
  schema: z.ZodType<T>,
): Promise<T> {
  const response = await fetch(url);
  if (!response.ok) {
    throw new DataError(`Could not load ${url} (HTTP ${response.status})`);
  }
  const body: unknown = await response.json();
  const result = schema.safeParse(body);
  if (!result.success) {
    throw new DataError(
      `${url} is not in the expected format:\n${z.prettifyError(result.error)}`,
    );
  }
  return result.data;
}

export function loadCountryList(): Promise<CountryList> {
  return fetchJson(`${dataRoot}/index/countries.json`, countryListSchema);
}

export function loadCountryIndex(code: string): Promise<CountryIndex> {
  return fetchJson(`${dataRoot}/index/${code}.json`, countryIndexSchema);
}

export function pickRandomImage(index: CountryIndex, random = Math.random) {
  const position = Math.floor(random() * index.images.length);
  return index.images[position] ?? index.images[0]!;
}
