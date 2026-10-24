import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import Home from "./page";

describe("Home page", () => {
  it("renders the product name", () => {
    render(<Home />);
    expect(
      screen.getByRole("heading", { level: 1, name: "CAWASMA" }),
    ).toBeInTheDocument();
  });

  it("links to the API docs", () => {
    render(<Home />);
    expect(screen.getByRole("button", { name: "API docs" })).toHaveAttribute(
      "href",
      "http://localhost:8000/docs",
    );
  });
});
