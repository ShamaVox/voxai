import { loginSuccess } from "./LoginActions";
import { navigateTo } from "./NavigationActions";
import { verifyInsightsData } from "./DashboardActions";
import {
  verifyLoggedOutHomepage,
  verifyHomeElements,
  verifyTabSwitch,
} from "./HomeActions";
import { fireEvent, waitFor, screen } from "@testing-library/react-native";

export const loginAndNavigateAll = async (newAccount: number = 0) => {
  // Verify homepage when logged out
  verifyLoggedOutHomepage();

  // Navigate to login page
  await navigateTo("Login");

  // Login using existing actions from LoginActions
  await loginSuccess(newAccount);

  // Navigate to Dashboard and verify insights data
  await screen.findByText("John Doe");
  //   await waitFor(() => {
  //     expect(
  //       queryAllByTestId("interview-list")[0].props.data.length
  //     ).toBeGreaterThan(9);
  //   });
  await navigateTo("Dashboard");
  await screen.findByText("Insights");
  await verifyInsightsData();

  // Navigate back to Home and verify elements
  await navigateTo("Home");
  await screen.findByText("My Interviews");
  await screen.findByText("John Doe");
  //   await waitFor(() => {
  //     expect(
  //       queryAllByTestId("interview-list")[0].props.data.length
  //     ).toBeGreaterThan(2);
  //   });
  await verifyTabSwitch("Completed");
  await verifyTabSwitch("Upcoming");
  //   await verifyHomeElements(
  //     screen.getByText,
  //     screen.queryByText,
  //     screen.findByText,
  //     queryAllByTestId,
  //     "Both"
  //   );
};
