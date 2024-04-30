import { loginSuccess } from "./LoginActions";
import { navigateTo } from "./NavigationActions";
import { verifyInsightsData } from "./DashboardActions";
import { verifyLoggedOutHomepage, verifyHomeElements } from "./HomeActions";
import { verifyHeader } from "./HeaderActions";
import { waitFor, screen } from "@testing-library/react-native";

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

export const loginAndNavigateAll = async (newAccount: number = 0) => {
  // Verify homepage when logged out
  let username: string = await navigateAndLogin(newAccount);

  // Navigate to Dashboard and verify insights data
  await screen.findByText("John Doe");
  await navigateTo("Dashboard");
  await screen.findByText("Insights");
  await verifyHeader(true, username);
  await verifyInsightsData();

  // Navigate back to Home and verify elements
  await navigateTo("Home");
  await verifyHeader(true, username);
  await screen.findByText("My Interviews");
  await screen.findByText("John Doe");
  await verifyHomeElements();
};
