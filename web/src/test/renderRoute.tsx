import { render } from "@testing-library/react";
import { createMemoryRouter, RouterProvider } from "react-router";
import { routes } from "../routes";

// Renders the real route tree at the given URL, as the browser would.
export function renderRoute(url: string) {
  const router = createMemoryRouter(routes, { initialEntries: [url] });
  return render(<RouterProvider router={router} />);
}
