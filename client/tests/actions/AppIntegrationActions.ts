import { loginSuccess } from "./LoginActions";
import { navigateTo } from "./NavigationActions";
import { verifyInsightsData } from "./DashboardActions";
import {
  verifyLoggedOutHomepage,
  verifyHomeElements,
  verifyUpcomingInterviews,
} from "./HomeActions";
import { verifyHeader } from "./HeaderActions";
import { waitFor, screen } from "@testing-library/react-native";

/**
 * Navigates to the Login screen and performs a login, optionally creating a new account.
 *
 * @param newAccount (Optional) Set to a number to create a new account with that number as part of the email. Defaults to 0 (existing account).
 * @returns The username of the logged-in user.
 */
export const navigateAndLogin = async (newAccount: number = 0) => {
  let username: string = "Test Name";
  if (newAccount) {
    username = "New User";
  }
  verifyLoggedOutHomepage();
  await verifyHeader(false);

  // Navigate to login page
  await navigateTo("Login");
  await verifyHeader(false);

  // Login using existing actions from LoginActions
  await loginSuccess(newAccount, true);
  await verifyHeader(true, username);
  return username;
};

/**
 * Performs a complete login and navigation flow, verifying elements on each screen.
 *
 * @param newAccount - Optional account number for creating a new account. Defaults to 0 (existing account).
 */
export const loginAndNavigateAll = async (newAccount: number = 0) => {
  // Verify homepage when logged out
  let username: string = await navigateAndLogin(newAccount);

  // Navigate to Dashboard and verify insights data
  await verifyUpcomingInterviews();
  await navigateTo("Dashboard");
  await screen.findByText("Insights");
  await verifyHeader(true, username);
  await verifyInsightsData();

  // Navigate back to Home and verify elements
  await navigateTo("Home");
  await verifyHeader(true, username);
  await verifyUpcomingInterviews();
  await verifyHomeElements();
};
