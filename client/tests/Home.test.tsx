import React from "react";
import {
  render,
  fireEvent,
  screen,
  waitFor,
} from "@testing-library/react-native";
import {
  mockUpcomingInterviews,
  mockTokenValidation,
} from "./utils/MockRequests";
import {
  verifyLoggedOutHomepage,
  verifyUpcomingInterviews,
  verifyTabSwitch,
} from "./actions/HomeActions";
import Home from "../src/Home";
import { renderComponent } from "./utils/Render";
import { setCookies, clearCookies } from "./utils/Cookies";

const mockNavigate = jest.fn();

jest.mock("@react-navigation/native", () => ({
  useNavigation: () => ({
    navigate: mockNavigate,
  }),
}));

beforeEach(async () => {
  await clearCookies();
});

test("renders placeholder content when logged out", () => {
  renderComponent(Home, false);
  verifyLoggedOutHomepage();
});

test("fetches and renders interviews when logged in", async () => {
  mockUpcomingInterviews();
  renderComponent(Home, true);
  await verifyUpcomingInterviews();
});

test("switches between Upcoming and Completed tabs", async () => {
  mockUpcomingInterviews();
  renderComponent(Home, true);
  await verifyTabSwitch("Both");
});

test("calls logout and navigates to login if token is invalid", async () => {
  mockTokenValidation("interviews", false);
  renderComponent(Home, true);
  await waitFor(() => {
    expect(mockNavigate).toHaveBeenCalledWith("Login");
  });
});
