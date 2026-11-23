import { useEffect, useState } from "react";
import { Link } from "react-router";
import type { CountryList } from "../data/indexSchema";
import { loadCountryList } from "../data/loadIndex";

type State =
  | { status: "loading" }
  | { status: "failed" }
  | { status: "ready"; countries: CountryList["countries"] };

export default function CountryPicker() {
  const [state, setState] = useState<State>({ status: "loading" });

  useEffect(() => {
    let cancelled = false;
    loadCountryList()
      .then((list) => {
        if (!cancelled) {
          setState({ status: "ready", countries: list.countries });
        }
      })
      .catch(() => {
        if (!cancelled) {
          setState({ status: "failed" });
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  if (state.status === "loading") {
    return <p role="status">Loading countries…</p>;
  }
  if (state.status === "failed") {
    return (
      <p role="alert">
        The country list didn't load. Check your connection and reload.
      </p>
    );
  }
  return (
    <ul className="grid grid-cols-2 gap-2 sm:grid-cols-3">
      {state.countries.map((country) => (
        <li key={country.code}>
          <Link
            to={`/explore/${country.code.toLowerCase()}`}
            className="block rounded border border-stone-700 px-4 py-3 font-medium hover:border-accent hover:text-accent focus-visible:outline-2 focus-visible:outline-accent"
          >
            {country.name}
          </Link>
        </li>
      ))}
    </ul>
  );
}
