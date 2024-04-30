import { fireEvent, waitFor, screen } from "@testing-library/react-native";
import { mockUpcomingInterviews, mockInsights } from "../utils/MockRequests";

export const navigateTo = async (screenName: string) => {
  // Mock API responses based on the screen
  if (screenName === "Home") {
    mockUpcomingInterviews();
  } else if (screenName === "Dashboard") {
    mockInsights();
  }

  if (screenName === "Login") {
    await waitFor(() => {
      fireEvent.press(screen.getByTestId("profile-container"));
    });
  }
  // Click the corresponding navigation button
  else {
    await waitFor(() => {
      fireEvent.press(
        screen.getByTestId(`nav-button-${screenName.toLowerCase()}`)
      );
    });
  }
};
