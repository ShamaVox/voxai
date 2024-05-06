import { fireEvent, waitFor, screen } from "@testing-library/react-native";
import { mockUpcomingInterviews, mockInsights } from "../utils/MockRequests";

/**
 * Navigates to the specified screen and mocks API responses if necessary.
 *
 * @param screenName - The name of the screen to navigate to.
 */
export const navigateTo = async (screenName: string) => {
  // Mock API responses based on the screen
  if (screenName === "Home") {
    mockUpcomingInterviews();
  } else if (screenName === "Dashboard") {
    mockInsights();
  }

  if (screenName === "Login") {
    await waitFor(async () => {
      fireEvent.press(screen.getByTestId("profile-container"));
      await screen.findByText("Login");
    });
  }
  // Click the corresponding navigation button
  else {
    await waitFor(async () => {
      fireEvent.press(
        screen.getByTestId(`nav-button-${screenName.toLowerCase()}`)
      );
      if (screenName === "Home") {
        await screen.findByText("My Interviews");
      }
      if (screenName === "Dashboard") {
        await screen.findByText("Insights");
      }
    });
  }
};
