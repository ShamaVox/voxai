import React from "react";
import { render, fireEvent, screen } from "@testing-library/react-native";
import { mockUpcomingInterviews, mockValidToken } from "./utils/MockRequests";
import {
  verifyLoggedOutHomepage,
  verifyUpcomingInterviews,
  verifyTabSwitch,
} from "./actions/HomeActions";
import { renderHome } from "./utils/Render";
import { setCookies, clearCookies } from "./utils/Cookies";

const mockNavigate = jest.fn();

jest.mock("@react-navigation/native", () => ({
  useNavigation: () => ({
    navigate: mockNavigate,
  }),
}));

test("renders placeholder content when logged out", () => {
  renderHome(false);
  verifyLoggedOutHomepage();
});

test("fetches and renders interviews when logged in", async () => {
  mockUpcomingInterviews();
  renderHome(true);
  await verifyUpcomingInterviews();
});

test("switches between Upcoming and Completed tabs", async () => {
  mockUpcomingInterviews();
  renderHome(true);
  await verifyTabSwitch("Both");
});
