import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { expect, test, vi } from "vitest";
import { AuthContext } from "../components/auth/auth-context";
import { DataControls } from "../components/settings/DataControls";

vi.mock("../lib/api", () => ({
  apiUrl: (value: string) => value,
  apiFetch: vi.fn(async () => new Response(JSON.stringify({ format: "chronos-account-export", data: {} }), { status: 200 })),
  getApiErrorMessage: vi.fn(),
}));

function setup() {
  const signOut = vi.fn(async () => undefined);
  render(<MemoryRouter><QueryClientProvider client={new QueryClient()}><AuthContext.Provider value={{ session: null, user: null, isLoading: false, signOut }}><DataControls /></AuthContext.Provider></QueryClientProvider></MemoryRouter>);
  return signOut;
}

test("account deletion stays disabled until the exact confirmation", async () => {
  setup(); const user = userEvent.setup();
  await user.click(screen.getByRole("button", { name: "Delete account data" }));
  const button = screen.getByRole("button", { name: "Permanently delete" });
  expect(button).toBeDisabled();
  fireEvent.change(screen.getByLabelText(/Type DELETE MY ACCOUNT/), { target: { value: "DELETE MY ACCOUNT" } });
  expect(button).toBeEnabled();
}, 10_000);
