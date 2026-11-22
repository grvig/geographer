import { Link, Outlet } from "react-router";

export default function Layout() {
  return (
    <div className="flex h-full flex-col">
      <header className="flex items-center gap-6 border-b border-stone-800 px-6 py-3">
        <Link to="/" className="text-lg font-semibold tracking-tight">
          Geographer
        </Link>
      </header>
      <main className="flex min-h-0 flex-1 flex-col">
        <Outlet />
      </main>
      <footer className="border-t border-stone-800 px-6 py-3 text-xs text-stone-500">
        Street-level imagery from{" "}
        <a
          className="underline hover:text-stone-300"
          href="https://www.mapillary.com"
        >
          Mapillary
        </a>{" "}
        contributors, licensed{" "}
        <a
          className="underline hover:text-stone-300"
          href="https://creativecommons.org/licenses/by-sa/4.0/"
        >
          CC-BY-SA 4.0
        </a>
        .
      </footer>
    </div>
  );
}
