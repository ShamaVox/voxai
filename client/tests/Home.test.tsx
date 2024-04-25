import React from "react";
import { render, fireEvent } from "@testing-library/react-native";
import Home from "../src/Home";
import { AuthContext } from "../src/AuthContext";
import { mockUpcomingInterviews } from "./utils/MockRequests";
import {
  verifyLoggedOutHomepage,
  verifyUpcomingInterviews,
  verifyTabSwitch,
} from "./actions/HomeActions";

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
  const { getByText } = renderHome(false);
  verifyLoggedOutHomepage(getByText);
});

test("fetches and renders interviews when logged in", async () => {
  mockUpcomingInterviews();
  const { findByText } = renderHome(true);

  await verifyUpcomingInterviews(findByText);
});

test("switches between Upcoming and Completed tabs", async () => {
  mockUpcomingInterviews();
  const { getByText, queryAllByTestId, findByText, queryByText } = renderHome(
    true
  );

  await verifyTabSwitch(
    getByText,
    queryByText,
    findByText,
    queryAllByTestId,
    "Both"
  );
});
