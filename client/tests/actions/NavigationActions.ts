import { fireEvent, waitFor } from "@testing-library/react-native";
import { mockUpcomingInterviews, mockInsights } from "../utils/MockRequests";

export const navigateTo = async (getByTestId, screenName: string) => {
  // Mock API responses based on the screen
  if (screenName === "Home") {
    mockUpcomingInterviews();
  } else if (screenName === "Dashboard") {
    mockInsights();
  }

  if (screenName === "Login") {
    await waitFor(() => {
      fireEvent.press(getByTestId("profile-container"));
    });
  }
  // Click the corresponding navigation button
  else {
    await waitFor(() => {
      fireEvent.press(getByTestId(`nav-button-${screenName.toLowerCase()}`));
    });
  }
};
