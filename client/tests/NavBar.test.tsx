import React from "react";
import { render, fireEvent, screen } from "@testing-library/react-native";
import NavBar from "../src/NavBar";
import { AuthContext } from "../src/AuthContext";
// import "jest-styled-components";

const mockNavigate = jest.fn();
jest.mock("@react-navigation/native", () => ({
  useNavigation: () => ({
    navigate: mockNavigate,
    addListener: () => jest.fn(),
  }),
}));

const renderNavBar = (isLoggedIn: boolean) => {
  return render(
    <AuthContext.Provider
      value={{
        isLoggedIn: isLoggedIn,
        email: "",
        username: "",
        handleLogin: async () => {},
        authToken: "",
        handleLogout: async () => {},
      }}
    >
      <NavBar />
    </AuthContext.Provider>
  );
};

beforeEach(() => {
  jest.clearAllMocks();
});

test("renders nothing when logged out", () => {
  renderNavBar(false);
  expect(screen.queryByTestId("nav-bar")).toBeNull();
});

test("renders sections and buttons when logged in", () => {
  renderNavBar(true);
  expect(screen.getByTestId("nav-bar")).toBeTruthy();
  expect(screen.getByTestId("section-general")).toBeTruthy();
  expect(screen.getByTestId("section-support")).toBeTruthy();
  expect(screen.getByTestId("nav-button-home")).toBeTruthy();
  expect(screen.getByTestId("nav-button-dashboard")).toBeTruthy();
  expect(screen.getByTestId("nav-button-candidates")).toBeTruthy();
  expect(screen.getByTestId("nav-button-settings")).toBeTruthy();
});

// Doesn't work due to library issues
// test("highlights active route button", () => {
//   const { screen.getByTestId } = renderNavBar(true);
//   expect(screen.getByTestId("nav-button-dashboard")).toHaveStyleRule(
//     "backgroundColor",
//     "#FFFFFF95"
//   );
//});

test("navigates to correct screen on button press", () => {
  renderNavBar(true);

  // Simulate button presses and check navigation calls
  fireEvent.press(screen.getByTestId("nav-button-home"));
  expect(mockNavigate).toHaveBeenCalledWith("Home");

  fireEvent.press(screen.getByTestId("nav-button-dashboard"));
  expect(mockNavigate).toHaveBeenCalledWith("Dashboard");

  fireEvent.press(screen.getByTestId("nav-button-candidates"));
  expect(mockNavigate).toHaveBeenCalledWith("Candidates");
});
