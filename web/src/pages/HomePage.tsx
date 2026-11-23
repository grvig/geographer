import CountryPicker from "../components/CountryPicker";

export default function HomePage() {
  return (
    <section className="mx-auto flex max-w-3xl flex-col gap-6 px-6 py-16">
      <h1 className="text-4xl font-bold tracking-tight">Geographer</h1>
      <p className="text-lg text-stone-300">
        Walk around real street-level imagery and learn the clues that give a
        place away: bollards, utility poles, road markings, sign backs, soil and
        more.
      </p>
      <p className="text-stone-400">
        Pick a country, look around freely, and hover any highlighted object to
        see what it is and where it points to.
      </p>
      <h2 className="mt-4 text-xl font-semibold">Pick a country</h2>
      <CountryPicker />
    </section>
  );
}
