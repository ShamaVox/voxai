import React from "react";
import { render, fireEvent } from "@testing-library/react-native";
import Home from "../src/Home";
import { AuthContext } from "../src/AuthContext";
import { mockUpcomingInterviews } from "./utils/MockRequests";

const mockNavigate = jest.fn();

jest.mock("@react-navigation/native", () => ({
  useNavigation: () => ({
    navigate: mockNavigate,
  }),
}));

function renderHome(isLoggedIn: boolean) {
  return render(
    <AuthContext.Provider value={{ isLoggedIn: isLoggedIn }}>
      <Home />
    </AuthContext.Provider>
  );
}

test("renders placeholder content when logged out", () => {
  // Will be replaced by real functionality
  const { getByText } = renderHome(false);

  expect(getByText("This is a placeholder homepage")).toBeTruthy();
  expect(getByText("Login")).toBeTruthy();
});

test("fetches and renders interviews when logged in", async () => {
  mockUpcomingInterviews();
  const { findByText, getAllByTestId } = renderHome(true);

  // Wait for interviews to be fetched and rendered
  await findByText("John Doe");
});

test("switches between Upcoming and Completed tabs", async () => {
  mockUpcomingInterviews();
  const { getByText, getAllByTestId, findByText, queryByText } = renderHome(
    true
  );

  // Initially, only Upcoming interviews should be visible
  await findByText("John Doe");

  // Click on the "Completed" tab
  fireEvent.press(getByText("Completed"));

  // Upcoming interviews should no longer be visible
  expect(queryByText("John Doe")).toBeNull();
});
