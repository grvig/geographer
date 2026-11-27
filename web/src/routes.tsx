import type { RouteObject } from "react-router";
import Layout from "./components/Layout";
import ExplorePage from "./pages/ExplorePage";
import HomePage from "./pages/HomePage";
import NotFoundPage from "./pages/NotFoundPage";

const pages: RouteObject[] = [
  {
    index: true,
    element: <HomePage />,
  },
  {
    path: "explore/:country",
    element: <ExplorePage />,
  },
];

// The review page needs the local curation server, so it only exists in
// development; the production build drops this branch and the page with it.
if (import.meta.env.DEV) {
  pages.push({
    path: "curate",
    lazy: async () => {
      const page = await import("./curate/CuratePage");
      return { Component: page.default };
    },
  });
}

pages.push({
  path: "*",
  element: <NotFoundPage />,
});

export const routes: RouteObject[] = [
  {
    element: <Layout />,
    children: pages,
  },
];
