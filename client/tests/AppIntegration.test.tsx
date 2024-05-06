import React from "react";
import { render } from "@testing-library/react-native";
import App from "../src/App";
import { SERVER_ENDPOINT } from "../src/utils/Axios";
import { randomAccountNumber } from "./utils/Random";
import {
  navigateAndLogin,
  loginAndNavigateAll,
} from "./actions/AppIntegrationActions";
import {
  verifyUpcomingInterviews,
  verifyLoggedOutHomepage,
} from "./actions/HomeActions";
import { loginFormEntry } from "./actions/LoginActions";
import { verifyHeader, logout } from "./actions/HeaderActions";
import {
  mockTokenValidation,
  mockUpcomingInterviews,
  mockLogout,
} from "./utils/MockRequests";
import { clearCookies, setCookies, getAuthCookies } from "./utils/Cookies";

beforeEach(() => {
  clearCookies();
});

test("Login with existing account and navigate to Dashboard and Home", async () => {
  render(<App enableAnimations={false} />);
  await loginAndNavigateAll();
});

test("Create new account and navigate to Dashboard and Home", async () => {
  render(<App enableAnimations={false} />);
  await loginAndNavigateAll(randomAccountNumber());
});

test("Login persists after refresh", async () => {
  const { unmount } = render(<App enableAnimations={false} />);
  await navigateAndLogin(0);

  // Simulate refresh (unmount and remount App component)
  mockTokenValidation();
  unmount();
  render(<App enableAnimations={false} />);

  // Verify user is still logged in and on the home page
  await verifyUpcomingInterviews();
});

test("Logs in automatically when cookie is present", async () => {
  setCookies({
    auth: {
      username: "Test User",
      email: "test@email.com",
      authToken: "AUTHTOKEN",
    },
  });
  mockTokenValidation();
  mockUpcomingInterviews();
  render(<App enableAnimations={false} />);
  await verifyUpcomingInterviews();
});

// Logs out on refresh with invalid token
test("Logs out on refresh with invalid token", async () => {
  const { unmount } = await render(<App enableAnimations={false} />);
  await navigateAndLogin(0);

  // Set cookies to invalid values
  setCookies({
    auth: {
      username: "Test User",
      email: "test@email.com",
      authToken: "INVALIDAUTHTOKEN",
    },
  });

  // Simulate refresh (unmount and remount App component)
  unmount();
  mockTokenValidation("check_token", false);
  mockLogout();
  render(<App enableAnimations={false} />);

  await verifyHeader(false);
  await loginFormEntry(
    { "email-input": "invalid_email" },
    "Send code",
    "Invalid email"
  );
});

test("Logout button", async () => {
  // Log in successfully
  render(<App enableAnimations={false} />);
  await loginAndNavigateAll();
  // Log out
  await logout("Test Name");
  // Verify the user is no longer logged in
  await verifyLoggedOutHomepage();
});
