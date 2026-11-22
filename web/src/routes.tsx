import type { RouteObject } from "react-router";
import Layout from "./components/Layout";
import ExplorePage from "./pages/ExplorePage";
import HomePage from "./pages/HomePage";
import NotFoundPage from "./pages/NotFoundPage";

export const routes: RouteObject[] = [
  {
    element: <Layout />,
    children: [
      {
        index: true,
        element: <HomePage />,
      },
      {
        path: "explore/:country",
        element: <ExplorePage />,
      },
      {
        path: "*",
        element: <NotFoundPage />,
      },
    ],
  },
];
