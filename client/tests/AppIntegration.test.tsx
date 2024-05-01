import React from "react";
import { render } from "@testing-library/react-native";
import App from "../src/App";
import { SERVER_ENDPOINT } from "../src/utils/Axios";
import { randomAccountNumber } from "./utils/Random";
import {
  navigateAndLogin,
  loginAndNavigateAll,
} from "./actions/AppIntegrationActions";
import { verifyUpcomingInterviews } from "./actions/HomeActions";
import { mockValidToken, mockUpcomingInterviews } from "./utils/MockRequests";
import { clearCookies, setCookies, getAuthCookies } from "./utils/Cookies";

beforeEach(() => {
  clearCookies();
});

test("Login with existing account and navigate to Dashboard and Home", async () => {
  render(<App />);
  await loginAndNavigateAll();
});

test("Create new account and navigate to Dashboard and Home", async () => {
  render(<App />);
  await loginAndNavigateAll(randomAccountNumber());
});

test("Login persists after refresh", async () => {
  render(<App />);
  await navigateAndLogin(0);

  // Simulate refresh (unmount and remount App component)
  mockValidToken();
  const { rerender } = render(<App />);
  rerender(<App />);

  // Verify user is still logged in and on the home page
  await verifyUpcomingInterviews();
});

test("logs in automatically when cookie is present", async () => {
  setCookies({
    auth: {
      username: "Test User",
      email: "test@email.com",
      authToken: "AUTHTOKEN",
    },
  });
  mockValidToken();
  mockUpcomingInterviews();
  render(<App />);
  await verifyUpcomingInterviews();
});
