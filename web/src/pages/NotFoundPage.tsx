import { Link } from "react-router";

export default function NotFoundPage() {
  return (
    <section className="mx-auto flex max-w-3xl flex-col gap-4 px-6 py-16">
      <h1 className="text-3xl font-bold">Page not found</h1>
      <p className="text-stone-400">
        There is nothing at this address. It may have moved, or the link may be
        mistyped.
      </p>
      <Link to="/" className="text-accent underline">
        Back to the start
      </Link>
    </section>
  );
}
