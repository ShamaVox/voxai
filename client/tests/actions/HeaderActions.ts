import { screen, waitFor } from "@testing-library/react-native";

/**
 * Verifies the elements and content of the Header component based on login status.
 *
 * @param loggedIn Whether the user is currently logged in.
 * @param username (Optional) The expected username to be displayed.
 */
export const verifyHeader: (a: boolean, b?: string) => Promise<void> = async (
  loggedIn: boolean,
  username: string
) => {
  expect(screen.getByTestId("logo")).toBeTruthy();
  const profileIconName =
    "profile-icon-" + (loggedIn ? "logged-in" : "logged-out");
  if (!username && loggedIn) {
    username = "Log In";
  }
  await waitFor(() => {
    expect(screen.getByTestId(profileIconName)).toBeTruthy();
  });
  if (username) {
    await screen.findByText(username);
  }
};
