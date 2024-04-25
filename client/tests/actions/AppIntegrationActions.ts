import { loginSuccess } from "./LoginActions";
import { navigateTo } from "./NavigationActions";
import { verifyInsightsData } from "./DashboardActions";
import {
  verifyLoggedOutHomepage,
  verifyHomeElements,
  verifyTabSwitch,
} from "./HomeActions";
import { fireEvent, waitFor } from "@testing-library/react-native";

export const loginAndNavigateAll = async (
  getByText,
  getByTestId,
  queryByTestId,
  queryByText,
  findByText,
  findByPlaceholderText,
  queryAllByTestId,
  newAccount: number = 0
) => {
  // Verify homepage when logged out
  verifyLoggedOutHomepage(getByText);

  // Navigate to login page
  await navigateTo(getByTestId, "Login");

  // Login using existing actions from LoginActions
  await loginSuccess(findByPlaceholderText, getByTestId, getByText, newAccount);

  // Navigate to Dashboard and verify insights data
  await findByText("John Doe");
  //   await waitFor(() => {
  //     expect(
  //       queryAllByTestId("interview-list")[0].props.data.length
  //     ).toBeGreaterThan(9);
  //   });
  await navigateTo(getByTestId, "Dashboard");
  await findByText("Insights");
  await verifyInsightsData(getByText);

  // Navigate back to Home and verify elements
  await navigateTo(getByTestId, "Home");
  await findByText("My Interviews");
  await findByText("John Doe");
  //   await waitFor(() => {
  //     expect(
  //       queryAllByTestId("interview-list")[0].props.data.length
  //     ).toBeGreaterThan(2);
  //   });
  await verifyTabSwitch(
    getByText,
    queryByText,
    findByText,
    queryAllByTestId,
    getByTestId,
    "Completed"
  );
  await verifyTabSwitch(
    getByText,
    queryByText,
    findByText,
    queryAllByTestId,
    getByTestId,
    "Upcoming"
  );
  //   await verifyHomeElements(
  //     getByText,
  //     queryByText,
  //     findByText,
  //     queryAllByTestId,
  //     "Both"
  //   );
};
